using System.Net.Http.Json;
using System.Text.Json;

namespace GlobexReviews;

public sealed record ModelOutput(string Label, double Score, string Model);

public sealed class SentimentScorer(IConfiguration config, IHttpClientFactory factory)
{
    public async Task<SentimentReading> Score(Review review, CancellationToken ct)
    {
        var modelUrl = config["SENTIMENT_MODEL_URL"];
        if (string.IsNullOrWhiteSpace(modelUrl))
            return ReviewRules.Sentiment(review);

        // This *teaching inference contract* is not KServe's universal wire format.
        // A real OpenShift AI model serving endpoint needs its own adapter and auth.
        var client = factory.CreateClient();
        using var response = await client.PostAsJsonAsync(modelUrl,
            new { text = review.Text }, EventJson.Options, ct);
        response.EnsureSuccessStatusCode();
        var model = await response.Content.ReadFromJsonAsync<ModelOutput>(EventJson.Options, ct)
            ?? throw new JsonException("Inference response missing");
        if (model.Label is not ("positive" or "negative" or "neutral") ||
            double.IsNaN(model.Score) || double.IsInfinity(model.Score) ||
            model.Score is < -1 or > 1 || string.IsNullOrWhiteSpace(model.Model))
            throw new JsonException("Inference model returned invalid score/label");
        return new SentimentReading(review.Id, review.Category,
            model.Label, model.Score, model.Model, review.SubmittedAt);
    }
}
