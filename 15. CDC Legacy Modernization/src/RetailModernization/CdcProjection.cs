using System.Text;
using System.Text.Json;
using Npgsql;

namespace RetailModernization;

// Each modern projection owns only its own destination: Elasticsearch or cashback-db.
// No CDC consumer ever queries or updates the legacy retail database.
public sealed class CdcProjection(IConfiguration config, IHttpClientFactory factory)
{
    private static long Id(JsonElement row, string property) => row.GetProperty(property).GetInt64();
    private static string Text(JsonElement row, string property) => row.GetProperty(property).GetString()!;
    private static long Number(JsonElement row, string property) => row.GetProperty(property).GetInt64();

    public async Task Apply(string topic, string raw, CancellationToken ct)
    {
        using var json = JsonDocument.Parse(raw);
        var root = json.RootElement;
        if (root.TryGetProperty("payload", out var payload)) root = payload;
        var op = root.GetProperty("op").GetString();
        if (op is not ("r" or "c" or "u" or "d")) return;
        var rowName = topic.Split('.').Last();
        var after = root.GetProperty("after");
        var before = root.GetProperty("before");
        var row = op == "d" ? before : after;
        if (row.ValueKind != JsonValueKind.Object)
            throw new JsonException("Debezium record missing before/after data");
        if (rowName == "product")
        {
            await ProductSearch(row, op == "d", ct);
            return;
        }
        if (rowName is not ("customer" or "sale" or "line_item")) return;
        await using var db = new NpgsqlConnection(config["CASHBACK_CONNECTION"] ??
            throw new InvalidOperationException("CASHBACK_CONNECTION missing"));
        await db.OpenAsync(ct);
        await using var tx = await db.BeginTransactionAsync(ct);
        switch (rowName)
        {
            case "customer":
                if (op == "d")
                    await Execute(db, tx, "DELETE FROM customer_projection WHERE customer_id=@id", ct,
                        ("id", Id(row, "customer_id")));
                else
                    await Execute(db, tx,
                        "INSERT INTO customer_projection(customer_id,full_name,tier) VALUES(@id,@n,@t) " +
                        "ON CONFLICT(customer_id) DO UPDATE SET full_name=EXCLUDED.full_name,tier=EXCLUDED.tier",
                        ct, ("id", Id(row, "customer_id")),
                        ("n", Text(row, "full_name")), ("t", Text(row, "tier")));
                break;
            case "sale":
                if (op == "d")
                    await Execute(db, tx, "DELETE FROM sale_stage WHERE sale_id=@id", ct,
                        ("id", Id(row, "sale_id")));
                else
                    await Execute(db, tx,
                        "INSERT INTO sale_stage(sale_id,customer_id,expected_lines) VALUES(@id,@c,@n) " +
                        "ON CONFLICT(sale_id) DO UPDATE SET customer_id=EXCLUDED.customer_id," +
                        "expected_lines=EXCLUDED.expected_lines",
                        ct, ("id", Id(row, "sale_id")),
                        ("c", Number(row, "customer_id")),
                        ("n", row.GetProperty("expected_lines").GetInt32()));
                break;
            case "line_item":
                if (op == "d")
                    await Execute(db, tx, "DELETE FROM item_stage WHERE line_item_id=@id", ct,
                        ("id", Id(row, "line_item_id")));
                else
                    await Execute(db, tx,
                        "INSERT INTO item_stage(line_item_id,sale_id,quantity,unit_price_cents) " +
                        "VALUES(@id,@s,@q,@c) ON CONFLICT(line_item_id) DO UPDATE SET " +
                        "sale_id=EXCLUDED.sale_id,quantity=EXCLUDED.quantity," +
                        "unit_price_cents=EXCLUDED.unit_price_cents",
                        ct, ("id", Id(row, "line_item_id")),
                        ("s", Id(row, "sale_id")),
                        ("q", row.GetProperty("quantity").GetInt32()),
                        ("c", Number(row, "unit_price_cents")));
                break;
        }

        // Intentional clarity-over-throughput algorithm: rebuild small demo projections
        // atomically after every event. No double credit on replays or out-of-order topics.
        // Real production systems should implement per-sale transactional reconciliation,
        // inbox/offset management and bounded retries; never use global rebuild at scale.
        await Execute(db, tx, "DELETE FROM expenses", ct);
        await Execute(db, tx,
            "INSERT INTO expenses(sale_id,customer_id,total_cents,cashback_cents) " +
            "SELECT s.sale_id,s.customer_id,SUM(i.quantity::bigint*i.unit_price_cents)::bigint," +
            "(SUM(i.quantity::bigint*i.unit_price_cents)::bigint * " +
            "(CASE c.tier WHEN 'gold' THEN 10 WHEN 'silver' THEN 5 ELSE 2 END))/100 " +
            "FROM sale_stage s JOIN item_stage i ON s.sale_id=i.sale_id " +
            "JOIN customer_projection c ON c.customer_id=s.customer_id " +
            "GROUP BY s.sale_id,s.customer_id,s.expected_lines,c.tier " +
            "HAVING COUNT(i.line_item_id)=s.expected_lines",
            ct);
        await Execute(db, tx, "DELETE FROM wallets", ct);
        await Execute(db, tx,
            "INSERT INTO wallets(customer_id,balance_cents) " +
            "SELECT c.customer_id,COALESCE(SUM(e.cashback_cents),0)::bigint " +
            "FROM customer_projection c LEFT JOIN expenses e ON e.customer_id=c.customer_id " +
            "GROUP BY c.customer_id", ct);
        await tx.CommitAsync(ct);
    }

    private async Task ProductSearch(JsonElement row, bool delete, CancellationToken ct)
    {
        var id = Id(row, "product_id");
        var search = (config["SEARCH_URL"] ?? "http://127.0.0.1:9200").TrimEnd('/');
        var url = search + "/retail-products/_doc/" + id;
        using var req = new HttpRequestMessage(delete ? HttpMethod.Delete : HttpMethod.Put, url);
        if (!delete)
            req.Content = new StringContent(JsonSerializer.Serialize(new
            {
                productId = id,
                name = Text(row, "name"),
                description = Text(row, "description"),
                priceCents = Number(row, "price_cents")
            }), Encoding.UTF8, "application/json");
        using var resp = await factory.CreateClient().SendAsync(req, ct);
        if (delete && resp.StatusCode == System.Net.HttpStatusCode.NotFound) return;
        resp.EnsureSuccessStatusCode();
    }

    private static async Task Execute(
        NpgsqlConnection db, NpgsqlTransaction tx, string sql, CancellationToken ct,
        params (string Name, object Value)[] args)
    {
        await using var cmd = new NpgsqlCommand(sql, db, tx);
        foreach (var arg in args) cmd.Parameters.AddWithValue(arg.Name, arg.Value);
        await cmd.ExecuteNonQueryAsync(ct);
    }
}
