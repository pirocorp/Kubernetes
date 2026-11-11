using System.Threading.Channels;

namespace GlobexReviews;

// Bounded per-consumer queues make fan-out and backpressure explicit.
// For learning only: process restart loses events and state.
public sealed class LocalChannels
{
    public Channel<Review> Moderation { get; } =
        Channel.CreateBounded<Review>(new BoundedChannelOptions(1024)
        {
            SingleReader = true, SingleWriter = false, FullMode = BoundedChannelFullMode.Wait
        });
    public Channel<Review> Sentiment { get; } =
        Channel.CreateBounded<Review>(new BoundedChannelOptions(1024)
        {
            SingleReader = true, SingleWriter = false, FullMode = BoundedChannelFullMode.Wait
        });

    public async Task Publish(Review review, CancellationToken ct)
    {
        // Cannot atomically write to two independent channels; this is a LOCAL
        // illustration, not durable exactly-once delivery.
        await Moderation.Writer.WriteAsync(review, ct);
        await Sentiment.Writer.WriteAsync(review, ct);
    }
}

public sealed class LocalWorkers(
    LocalChannels channels, ReviewProcessor processor, IConfiguration config, ILogger<LocalWorkers> log)
    : BackgroundService
{
    protected override Task ExecuteAsync(CancellationToken stoppingToken)
    {
        if (config["REVIEWS_MODE"] is "kafka" or "knative") return Task.CompletedTask;
        return Task.WhenAll(ProcessModeration(stoppingToken), ProcessSentiment(stoppingToken));
    }

    private async Task ProcessModeration(CancellationToken ct)
    {
        await foreach (var review in channels.Moderation.Reader.ReadAllAsync(ct))
        {
            try { await processor.Moderate(review, ct); }
            catch (Exception ex) { log.LogError(ex, "Moderation worker failed for review {Id}", review.Id); }
        }
    }

    private async Task ProcessSentiment(CancellationToken ct)
    {
        await foreach (var review in channels.Sentiment.Reader.ReadAllAsync(ct))
        {
            try { await processor.Analyze(review, ct); }
            catch (Exception ex) { log.LogError(ex, "Sentiment worker failed for review {Id}", review.Id); }
        }
    }
}
