using Confluent.Kafka;

namespace RetailModernization;

// One teaching worker subscribes to Debezium's four topics.
// Offsets are committed only AFTER successful projection side effects.
public sealed class CdcWorker(
    IConfiguration cfg, CdcProjection projection, ILogger<CdcWorker> logger) : BackgroundService
{
    protected override Task ExecuteAsync(CancellationToken ct)
    {
        if (cfg["APP_MODE"] != "modern") return Task.CompletedTask;
        return Task.Run(() => Consume(ct), ct);
    }

    private async Task Consume(CancellationToken ct)
    {
        using var consumer = new ConsumerBuilder<string, string>(new ConsumerConfig
        {
            BootstrapServers = cfg["KAFKA_BOOTSTRAP"] ?? "kafka:19092",
            GroupId = cfg["KAFKA_GROUP_ID"] ?? "m14-projections",
            AutoOffsetReset = AutoOffsetReset.Earliest,
            EnableAutoCommit = false,
            AllowAutoCreateTopics = false
        }).Build();
        consumer.Subscribe(
        [
            "retailcdc.public.customer", "retailcdc.public.product",
            "retailcdc.public.sale", "retailcdc.public.line_item"
        ]);
        try
        {
            while (!ct.IsCancellationRequested)
            {
                ConsumeResult<string, string>? record = null;
                try
                {
                    record = consumer.Consume(ct);
                    if (record.Message.Value is not null)
                        await projection.Apply(record.Topic, record.Message.Value, ct);
                    // Null value is a tombstone following a delete; delete was
                    // already handled by the earlier op=d change event.
                    consumer.Commit(record);
                }
                catch (OperationCanceledException) when (ct.IsCancellationRequested)
                { break; }
                catch (Exception ex)
                {
                    logger.LogError(ex, "CDC projection failed at {TopicOffset}",
                        record?.TopicPartitionOffset.ToString() ?? "before delivery");
                    if (record is not null)
                    {
                        try { consumer.Seek(record.TopicPartitionOffset); }
                        catch (Exception seek) { logger.LogWarning(seek, "Cannot seek to retry"); }
                    }
                    try { await Task.Delay(1500, ct); }
                    catch (OperationCanceledException) { break; }
                }
            }
        }
        finally { consumer.Close(); }
    }
}
