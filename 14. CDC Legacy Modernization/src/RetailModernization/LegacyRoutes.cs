using Npgsql;

namespace RetailModernization;

// This intentionally simulates the OLD unmodifiable business system.
// Crucially, NONE of these routes knows about Kafka, Debezium or Elasticsearch.
public record ProductInput(long ProductId, string Name, string Description, long PriceCents);
public record SaleLineInput(long ProductId, int Quantity);
public record SaleInput(long CustomerId, List<SaleLineInput> Items);
public record TierInput(string Tier);

public static class LegacyRoutes
{
    private static NpgsqlConnection Db(IConfiguration cfg) =>
        new(cfg["LEGACY_CONNECTION"] ?? throw new InvalidOperationException("LEGACY_CONNECTION missing"));

    public static void Map(WebApplication app)
    {
        var group = app.MapGroup("/legacy");
        group.MapGet("/products", async (IConfiguration cfg, CancellationToken ct) =>
        {
            await using var db = Db(cfg);
            await db.OpenAsync(ct);
            await using var cmd = new NpgsqlCommand(
                "SELECT product_id,name,description,price_cents FROM product ORDER BY product_id", db);
            var values = new List<object>();
            await using var rows = await cmd.ExecuteReaderAsync(ct);
            while (await rows.ReadAsync(ct))
                values.Add(new { productId = rows.GetInt64(0), name = rows.GetString(1),
                    description = rows.GetString(2), priceCents = rows.GetInt64(3) });
            return Results.Ok(values);
        });

        group.MapPost("/products", async Task<IResult> (ProductInput p, IConfiguration cfg, CancellationToken ct) =>
        {
            if (!ValidProduct(p)) return Results.BadRequest(new { code = "invalid_product" });
            try
            {
                await using var db = Db(cfg);
                await db.OpenAsync(ct);
                await using var cmd = new NpgsqlCommand(
                    "INSERT INTO product(product_id,name,description,price_cents) VALUES(@id,@n,@d,@p)", db);
                cmd.Parameters.AddWithValue("id", p.ProductId);
                cmd.Parameters.AddWithValue("n", p.Name);
                cmd.Parameters.AddWithValue("d", p.Description);
                cmd.Parameters.AddWithValue("p", p.PriceCents);
                await cmd.ExecuteNonQueryAsync(ct);
                return Results.Created($"/legacy/products/{p.ProductId}", p);
            }
            catch (PostgresException ex) when (ex.SqlState == "23505")
            { return Results.Conflict(new { code = "product_exists" }); }
        });

        group.MapPut("/products/{id:long}", async Task<IResult> (
            long id, ProductInput p, IConfiguration cfg, CancellationToken ct) =>
        {
            if (id != p.ProductId || !ValidProduct(p))
                return Results.BadRequest(new { code = "invalid_product" });
            await using var db = Db(cfg);
            await db.OpenAsync(ct);
            await using var cmd = new NpgsqlCommand(
                "UPDATE product SET name=@n,description=@d,price_cents=@p WHERE product_id=@id", db);
            cmd.Parameters.AddWithValue("id", id);
            cmd.Parameters.AddWithValue("n", p.Name);
            cmd.Parameters.AddWithValue("d", p.Description);
            cmd.Parameters.AddWithValue("p", p.PriceCents);
            return await cmd.ExecuteNonQueryAsync(ct) == 1
                ? Results.Ok(p) : Results.NotFound(new { code = "not_found" });
        });

        group.MapDelete("/products/{id:long}", async Task<IResult> (
            long id, IConfiguration cfg, CancellationToken ct) =>
        {
            try
            {
                await using var db = Db(cfg);
                await db.OpenAsync(ct);
                await using var cmd = new NpgsqlCommand(
                    "DELETE FROM product WHERE product_id=@id", db);
                cmd.Parameters.AddWithValue("id", id);
                return await cmd.ExecuteNonQueryAsync(ct) == 1
                    ? Results.NoContent() : Results.NotFound(new { code = "not_found" });
            }
            catch (PostgresException ex) when (ex.SqlState == "23503")
            { return Results.Conflict(new { code = "product_has_sales" }); }
        });

        group.MapPut("/customers/{id:long}/tier", async Task<IResult> (
            long id, TierInput change, IConfiguration cfg, CancellationToken ct) =>
        {
            if (change.Tier is not ("bronze" or "silver" or "gold"))
                return Results.BadRequest(new { code = "invalid_tier" });
            await using var db = Db(cfg);
            await db.OpenAsync(ct);
            await using var cmd = new NpgsqlCommand(
                "UPDATE customer SET tier=@tier WHERE customer_id=@id", db);
            cmd.Parameters.AddWithValue("id", id);
            cmd.Parameters.AddWithValue("tier", change.Tier);
            return await cmd.ExecuteNonQueryAsync(ct) == 1
                ? Results.Ok(new { customerId = id, tier = change.Tier })
                : Results.NotFound(new { code = "not_found" });
        });

        group.MapPost("/sales", async Task<IResult> (
            SaleInput sale, IConfiguration cfg, CancellationToken ct) =>
        {
            if (sale.CustomerId <= 0 || sale.Items is null ||
                sale.Items.Count is < 1 or > 20 ||
                sale.Items.Any(i => i.ProductId <= 0 || i.Quantity is < 1 or > 100))
                return Results.BadRequest(new { code = "invalid_sale" });
            await using var db = Db(cfg);
            await db.OpenAsync(ct);
            await using var tx = await db.BeginTransactionAsync(ct);
            await using (var exists = new NpgsqlCommand(
                "SELECT COUNT(*) FROM customer WHERE customer_id=@id", db, tx))
            {
                exists.Parameters.AddWithValue("id", sale.CustomerId);
                if (Convert.ToInt64(await exists.ExecuteScalarAsync(ct)) != 1)
                    return Results.BadRequest(new { code = "unknown_customer" });
            }
            var lines = new List<(long ProductId, int Quantity, long Price)>();
            foreach (var item in sale.Items)
            {
                await using var price = new NpgsqlCommand(
                    "SELECT price_cents FROM product WHERE product_id=@id FOR SHARE", db, tx);
                price.Parameters.AddWithValue("id", item.ProductId);
                var result = await price.ExecuteScalarAsync(ct);
                if (result is not long cents)
                    return Results.BadRequest(new { code = "unknown_product" });
                lines.Add((item.ProductId, item.Quantity, cents));
            }
            await using var insertSale = new NpgsqlCommand(
                "INSERT INTO sale(customer_id,expected_lines) VALUES(@c,@n) RETURNING sale_id", db, tx);
            insertSale.Parameters.AddWithValue("c", sale.CustomerId);
            insertSale.Parameters.AddWithValue("n", lines.Count);
            var saleId = Convert.ToInt64(await insertSale.ExecuteScalarAsync(ct));
            foreach (var line in lines)
            {
                await using var cmd = new NpgsqlCommand(
                    "INSERT INTO line_item(sale_id,product_id,quantity,unit_price_cents) " +
                    "VALUES(@s,@p,@q,@c)", db, tx);
                cmd.Parameters.AddWithValue("s", saleId);
                cmd.Parameters.AddWithValue("p", line.ProductId);
                cmd.Parameters.AddWithValue("q", line.Quantity);
                cmd.Parameters.AddWithValue("c", line.Price);
                await cmd.ExecuteNonQueryAsync(ct);
            }
            await tx.CommitAsync(ct);
            return Results.Created($"/legacy/sales/{saleId}",
                new { saleId, customerId = sale.CustomerId, lineCount = lines.Count });
        });
    }

    private static bool ValidProduct(ProductInput p) =>
        p.ProductId > 0 && !string.IsNullOrWhiteSpace(p.Name) && p.Name.Length <= 100 &&
        !string.IsNullOrWhiteSpace(p.Description) && p.Description.Length <= 500 &&
        p.PriceCents is >= 0 and <= 100000000;
}
