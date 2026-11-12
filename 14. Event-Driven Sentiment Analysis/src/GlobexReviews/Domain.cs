using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

namespace GlobexReviews;

public sealed record ReviewInput(
    [property: JsonRequired] string ProductId,
    [property: JsonRequired] string Category,
    [property: JsonRequired] string Text);

public sealed record Review(string Id, string ProductId, string Category, string Text, DateTimeOffset SubmittedAt);
public sealed record ModerationDecision(string ReviewId, string Category, string Status, string Reason, DateTimeOffset At);
public sealed record SentimentReading(
    string ReviewId, string Category, string Label, double Score, string Model, DateTimeOffset At);

public sealed record EventEnvelope<T>(
    string Specversion, string Id, string Source, string Type,
    DateTimeOffset Time, string Datacontenttype, T Data)
{
    public static EventEnvelope<T> Create(string type, T data) =>
        new("1.0", Guid.NewGuid().ToString("N"), "/globex/reviews",
            type, DateTimeOffset.UtcNow, "application/json", data);
}

public static class EventJson
{
    public static readonly JsonSerializerOptions Options = new(JsonSerializerDefaults.Web)
    {
        PropertyNameCaseInsensitive = true
    };
    public static string Encode<T>(T obj) => JsonSerializer.Serialize(obj, Options);
    public static EventEnvelope<Review> ParseReview(string text)
    {
        var result = JsonSerializer.Deserialize<EventEnvelope<Review>>(text, Options)
            ?? throw new JsonException("CloudEvent is absent");
        if (result.Specversion != "1.0" ||
            result.Type != "globex.review.submitted" ||
            result.Data is null ||
            !ReviewRules.IsValid(result.Data.ProductId, result.Data.Category, result.Data.Text))
            throw new JsonException("Unexpected CloudEvent type or invalid review");
        return result;
    }

    // KafkaSource typically emits dev.knative.kafka.event with the Kafka payload as its data.
    // Accepts either a nested JSON CloudEvent or a string containing its JSON serialization.
    public static EventEnvelope<Review> ParseKnative(JsonElement document)
    {
        JsonElement candidate = document;
        if (!document.TryGetProperty("type", out var type))
            throw new JsonException("CloudEvent missing type");
        if (type.GetString() == "dev.knative.kafka.event")
        {
            if (!document.TryGetProperty("data", out candidate))
                throw new JsonException("Kafka CloudEvent missing data");
            if (candidate.ValueKind == JsonValueKind.String)
            {
                using var nested = JsonDocument.Parse(candidate.GetString()!);
                return ParseReview(nested.RootElement.GetRawText());
            }
        }
        return ParseReview(candidate.GetRawText());
    }
}

public static class ReviewRules
{
    public static readonly string[] Categories =
        ["clothing", "bags", "utensils", "office-supplies", "fashion-accessory",
          "electronics", "sports-equipment"];

    // Deliberate *non-ML* deterministic stand-in for a moderation model.
    private static readonly HashSet<string> Blocked = new(StringComparer.OrdinalIgnoreCase)
        { "spam", "scam", "abusive" };

    private static readonly HashSet<string> Positive = new(StringComparer.OrdinalIgnoreCase)
        { "good", "great", "excellent", "amazing", "love", "perfect" };
    private static readonly HashSet<string> Negative = new(StringComparer.OrdinalIgnoreCase)
        { "bad", "terrible", "broken", "poor", "slow", "awful" };

    public static bool IsValid(string? productId, string? category, string? text) =>
        !string.IsNullOrWhiteSpace(productId) && productId.Length <= 40 &&
        Regex.IsMatch(productId, "^[a-zA-Z0-9_-]+$") &&
        Categories.Contains(category, StringComparer.Ordinal) &&
        !string.IsNullOrWhiteSpace(text) && text.Length <= 500;

    private static string[] Words(string text) =>
        Regex.Matches(text.ToLowerInvariant(), "[a-z]+")
            .Select(m => m.Value).ToArray();

    public static ModerationDecision Moderate(Review r)
    {
        var denied = Words(r.Text).Any(Blocked.Contains);
        return new(r.Id, r.Category, denied ? "denied" : "approved",
            denied ? "demo-blocklist" : "accepted", DateTimeOffset.UtcNow);
    }

    public static SentimentReading Sentiment(Review r)
    {
        var words = Words(r.Text);
        var pos = words.Count(Positive.Contains);
        var neg = words.Count(Negative.Contains);
        var score = pos + neg == 0 ? 0.0 : (double)(pos - neg) / (pos + neg);
        var label = score > 0 ? "positive" : score < 0 ? "negative" : "neutral";
        return new(r.Id, r.Category, label, score, "demo-lexicon-v1", r.SubmittedAt);
    }
}
