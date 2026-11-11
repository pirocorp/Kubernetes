using System.Collections.Concurrent;

namespace GlobexReviews;

public sealed class ReviewState
{
    private readonly ConcurrentDictionary<string, Review> _reviews = new();
    private readonly ConcurrentDictionary<string, ModerationDecision> _moderations = new();
    private readonly ConcurrentDictionary<string, SentimentReading> _sentiments = new();
    private readonly ConcurrentQueue<object> _events = new();

    public bool Put(Review review)
    {
        var added = _reviews.TryAdd(review.Id, review);
        if (added) Remember(EventEnvelope<Review>.Create("globex.review.submitted", review));
        return added;
    }

    public void Moderated(ModerationDecision decision)
    {
        if (_moderations.TryAdd(decision.ReviewId, decision))
            Remember(EventEnvelope<ModerationDecision>.Create(
                decision.Status == "approved" ? "globex.review.moderated" : "globex.review.denied",
                decision));
    }

    public void Scored(SentimentReading result)
    {
        if (_sentiments.TryAdd(result.ReviewId, result))
            Remember(EventEnvelope<SentimentReading>.Create("globex.review.sentiment", result));
    }

    private void Remember<T>(EventEnvelope<T> value)
    {
        _events.Enqueue(value);
        while (_events.Count > 1000) _events.TryDequeue(out _);
    }

    public object? Get(string id) => _reviews.TryGetValue(id, out var review)
        ? new
        {
            review.Id, review.ProductId, review.Category,
            moderation = _moderations.TryGetValue(id, out var mod) ? mod.Status : "pending",
            sentiment = _sentiments.TryGetValue(id, out var val) ? val.Label : "pending",
            score = _sentiments.TryGetValue(id, out var score) ? (double?)score.Score : null
        }
        : null;

    public object[] Approved() => _reviews.Values
        .Where(r => _moderations.TryGetValue(r.Id, out var d) && d.Status == "approved")
        .OrderBy(r => r.SubmittedAt)
        .Select(r => (object)r).ToArray();

    public object[] Events() => _events.ToArray();

    public object[] Summary() => _sentiments.Values
        .GroupBy(s => s.Category)
        .OrderBy(g => g.Key)
        .Select(g => (object)new
        {
            category = g.Key,
            count = g.Count(),
            averageScore = Math.Round(g.Average(s => s.Score), 3),
            positive = g.Count(s => s.Label == "positive"),
            negative = g.Count(s => s.Label == "negative"),
            neutral = g.Count(s => s.Label == "neutral"),
            models = g.Select(s => s.Model).Distinct().OrderBy(s => s).ToArray()
        }).ToArray();
}
