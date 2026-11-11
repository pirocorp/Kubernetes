using System.Globalization;
using System.Net.Http.Headers;
using System.Text;
using Npgsql;

namespace GlobexReviews;

// External sinks are optional in the standalone local lab. In the compose lab
// both are configured, so moderation writes PostgreSQL and sentiment writes InfluxDB.
public sealed class OutputSinks(IConfiguration config, IHttpClientFactory factory)
{
    public bool HasPostgres => !string.IsNullOrWhiteSpace(config["POSTGRES_CONNECTION"]);
    public bool HasInflux => !string.IsNullOrWhiteSpace(config["INFLUX_URL"]);

    public async Task SaveApproved(Review review, CancellationToken ct)
    {
        var connectionString = config["POSTGRES_CONNECTION"];
        if (string.IsNullOrWhiteSpace(connectionString)) return;
        await using var conn = new NpgsqlConnection(connectionString);
        await conn.OpenAsync(ct);
        await using var command = new NpgsqlCommand(
            "INSERT INTO approved_reviews (review_id, product_id, category, review_text, submitted_at) " +
            "VALUES (@id, @product, @category, @text, @at) ON CONFLICT (review_id) DO NOTHING", conn);
        command.Parameters.AddWithValue("id", Guid.Parse(review.Id));
        command.Parameters.AddWithValue("product", review.ProductId);
        command.Parameters.AddWithValue("category", review.Category);
        command.Parameters.AddWithValue("text", review.Text);
        command.Parameters.AddWithValue("at", review.SubmittedAt);
        await command.ExecuteNonQueryAsync(ct);
    }

    public async Task<object[]> ReadApproved(ReviewState state, CancellationToken ct)
    {
        var connectionString = config["POSTGRES_CONNECTION"];
        if (string.IsNullOrWhiteSpace(connectionString)) return state.Approved();
        var reviews = new List<object>();
        await using var conn = new NpgsqlConnection(connectionString);
        await conn.OpenAsync(ct);
        await using var cmd = new NpgsqlCommand(
            "SELECT review_id, product_id, category, review_text, submitted_at " +
            "FROM approved_reviews ORDER BY submitted_at", conn);
        await using var reader = await cmd.ExecuteReaderAsync(ct);
        while (await reader.ReadAsync(ct))
            reviews.Add(new Review(reader.GetGuid(0).ToString(), reader.GetString(1),
                reader.GetString(2), reader.GetString(3), reader.GetFieldValue<DateTimeOffset>(4)));
        return reviews.ToArray();
    }

    private static string EscapeTag(string text) =>
        text.Replace("\\", "\\\\").Replace(" ", "\\ ")
            .Replace(",", "\\,").Replace("=", "\\=");

    public async Task SaveSentiment(SentimentReading reading, CancellationToken ct)
    {
        var url = config["INFLUX_URL"];
        if (string.IsNullOrWhiteSpace(url)) return;
        var token = config["INFLUX_TOKEN"] ?? throw new InvalidOperationException("INFLUX_TOKEN missing");
        var org = config["INFLUX_ORG"] ?? throw new InvalidOperationException("INFLUX_ORG missing");
        var bucket = config["INFLUX_BUCKET"] ?? throw new InvalidOperationException("INFLUX_BUCKET missing");

        // Stable review_id tag AND stable review SubmittedAt timestamp make retries
        // update the same time-series point in this SMALL synthetic data set.
        // High-cardinality ID tags are not recommended for production InfluxDB.
        var line = $"review_sentiment,category={EscapeTag(reading.Category)},review_id={EscapeTag(reading.ReviewId)} " +
                   $"score={reading.Score.ToString("R", CultureInfo.InvariantCulture)} " +
                   reading.At.ToUnixTimeSeconds().ToString(CultureInfo.InvariantCulture);
        var destination = url.TrimEnd('/') + "/api/v2/write?org=" + Uri.EscapeDataString(org) +
                          "&bucket=" + Uri.EscapeDataString(bucket) + "&precision=s";
        using var request = new HttpRequestMessage(HttpMethod.Post, destination);
        request.Headers.Authorization = new AuthenticationHeaderValue("Token", token);
        request.Content = new StringContent(line, Encoding.UTF8, "text/plain");
        using var response = await factory.CreateClient().SendAsync(request, ct);
        response.EnsureSuccessStatusCode();
    }
}
