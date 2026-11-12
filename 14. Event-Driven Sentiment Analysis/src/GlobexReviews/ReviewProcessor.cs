namespace GlobexReviews;

public sealed class ReviewProcessor(
    ReviewState state, OutputSinks outputs, KafkaTransport kafka,
    SentimentScorer scorer, IConfiguration config)
{
    public async Task Moderate(Review review, CancellationToken ct)
    {
        var result = ReviewRules.Moderate(review);
        if (result.Status == "approved")
            await outputs.SaveApproved(review, ct);
        if (config["REVIEWS_MODE"] is "kafka" or "knative")
            await kafka.SendEvent(
                result.Status == "approved" ? "reviews.moderated" : "reviews.denied",
                EventEnvelope<ModerationDecision>.Create(
                    result.Status == "approved" ? "globex.review.moderated" : "globex.review.denied",
                    result), result.ReviewId, ct);
        state.Moderated(result);
    }

    public async Task Analyze(Review review, CancellationToken ct)
    {
        var reading = await scorer.Score(review, ct);
        await outputs.SaveSentiment(reading, ct);
        if (config["REVIEWS_MODE"] is "kafka" or "knative")
            await kafka.SendEvent("reviews.sentiment",
                EventEnvelope<SentimentReading>.Create("globex.review.sentiment", reading),
                reading.ReviewId, ct);
        state.Scored(reading);
    }
}
