using System.Text;
using System.Text.Json;
using Npgsql;

namespace RetailModernization;

public static class ModernRoutes
{
    private static NpgsqlConnection Db(IConfiguration cfg) =>
        new(cfg["CASHBACK_CONNECTION"] ?? throw new InvalidOperationException("CASHBACK_CONNECTION missing"));

    public static void Map(WebApplication app)
    {
        app.MapGet("/search", async Task<IResult> (
            string? q, IConfiguration cfg, IHttpClientFactory factory, CancellationToken ct) =>
        {
            if (string.IsNullOrWhiteSpace(q) || q.Length > 80)
                return Results.BadRequest(new { code = "invalid_query" });
            var endpoint = (cfg["SEARCH_URL"] ?? "http://127.0.0.1:9200").TrimEnd('/');
            using var req = new HttpRequestMessage(HttpMethod.Post,
                endpoint + "/retail-products/_search");
            req.Content = new StringContent(JsonSerializer.Serialize(new
            {
                size = 20,
                query = new { multi_match = new { query = q, fields = new[] { "name", "description" } } }
            }), Encoding.UTF8, "application/json");
            using var response = await factory.CreateClient().SendAsync(req, ct);
            if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
                return Results.Ok(Array.Empty<object>());
            response.EnsureSuccessStatusCode();
            using var doc = JsonDocument.Parse(await response.Content.ReadAsStringAsync(ct));
            var matches = doc.RootElement.GetProperty("hits").GetProperty("hits")
                .EnumerateArray().Select(h => h.GetProperty("_source").Clone()).ToArray();
            return Results.Ok(matches);
        });

        app.MapGet("/wallets/{id:long}", async Task<IResult> (
            long id, IConfiguration cfg, CancellationToken ct) =>
        {
            await using var db = Db(cfg);
            await db.OpenAsync(ct);
            await using var cmd = new NpgsqlCommand(
                "SELECT c.customer_id,c.full_name,c.tier,COALESCE(w.balance_cents,0) " +
                "FROM customer_projection c LEFT JOIN wallets w ON w.customer_id=c.customer_id " +
                "WHERE c.customer_id=@id", db);
            cmd.Parameters.AddWithValue("id", id);
            await using var row = await cmd.ExecuteReaderAsync(ct);
            return await row.ReadAsync(ct)
                ? Results.Ok(new { customerId = row.GetInt64(0), name = row.GetString(1),
                    tier = row.GetString(2), balanceCents = row.GetInt64(3) })
                : Results.NotFound(new { code = "not_projected" });
        });

        app.MapGet("/expenses/{id:long}", async Task<IResult> (
            long id, IConfiguration cfg, CancellationToken ct) =>
        {
            await using var db = Db(cfg);
            await db.OpenAsync(ct);
            await using var cmd = new NpgsqlCommand(
                "SELECT sale_id,customer_id,total_cents,cashback_cents FROM expenses WHERE sale_id=@id", db);
            cmd.Parameters.AddWithValue("id", id);
            await using var row = await cmd.ExecuteReaderAsync(ct);
            return await row.ReadAsync(ct)
                ? Results.Ok(new { saleId = row.GetInt64(0), customerId = row.GetInt64(1),
                    totalCents = row.GetInt64(2), cashbackCents = row.GetInt64(3) })
                : Results.NotFound(new { code = "not_projected" });
        });
    }
}
