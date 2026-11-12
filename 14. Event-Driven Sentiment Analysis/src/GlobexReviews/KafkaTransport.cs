using Confluent.Kafka;
using Confluent.Kafka.Admin;

namespace GlobexReviews;

public sealed class KafkaTransport : IDisposable
{
    private readonly string _bootstrap;
    private readonly Lazy<IProducer<string, string>> _producer;
    private readonly SemaphoreSlim _setupLock = new(1, 1);
    private bool _ready;
    public const string InputTopic = "globex.reviews";

    public KafkaTransport(IConfiguration configuration)
    {
        _bootstrap = configuration["KAFKA_BOOTSTRAP"] ?? "127.0.0.1:9092";
        _producer = new Lazy<IProducer<string, string>>(() =>
            new ProducerBuilder<string, string>(
                new ProducerConfig
                {
                    BootstrapServers = _bootstrap,
                    Acks = Acks.All,
                    MessageTimeoutMs = 10000
                }).Build());
    }

    public async Task SetupTopics(CancellationToken ct)
    {
        if (_ready) return;
        await _setupLock.WaitAsync(ct);
        try
        {
            if (_ready) return;
            if (Environment.GetEnvironmentVariable("KAFKA_MANAGE_TOPICS") == "false")
            {
                _ready = true; // Admin must pre-create all four topics in this mode.
                return;
            }
            using var admin = new AdminClientBuilder(
                new AdminClientConfig { BootstrapServers = _bootstrap }).Build();
            try
            {
                await admin.CreateTopicsAsync(
                    new[] { InputTopic, "reviews.moderated", "reviews.denied", "reviews.sentiment" }
                        .Select(name => new TopicSpecification
                        {
                            Name = name,
                            NumPartitions = 1,
                            ReplicationFactor = 1
                        }));
            }
            catch (CreateTopicsException exception) when (
                exception.Results.All(r => r.Error.Code is ErrorCode.TopicAlreadyExists or ErrorCode.NoError))
            {
                // Re-running the exercise must not fail for existing demo topics.
            }
            _ready = true;
        }
        finally { _setupLock.Release(); }
    }

    public async Task SendEvent<T>(
        string topic, EventEnvelope<T> envelope, string reviewId, CancellationToken ct)
    {
        await SetupTopics(ct);
        await _producer.Value.ProduceAsync(topic,
            new Message<string, string>
            {
                Key = reviewId,
                Value = EventJson.Encode(envelope)
            }, ct);
    }

    public string Bootstrap => _bootstrap;
    public void Dispose()
    {
        if (_producer.IsValueCreated)
        {
            _producer.Value.Flush(TimeSpan.FromSeconds(3));
            _producer.Value.Dispose();
        }
        _setupLock.Dispose();
    }
}

public sealed class KafkaWorkers(
    KafkaTransport transport, ReviewProcessor processor, IConfiguration configuration,
    ILogger<KafkaWorkers> logger) : BackgroundService
{
    protected override Task ExecuteAsync(CancellationToken stoppingToken)
    {
        if (configuration["REVIEWS_MODE"] != "kafka") return Task.CompletedTask;
        return Task.WhenAll(
            Task.Run(() => Consume("m14-moderation", processor.Moderate, stoppingToken), stoppingToken),
            Task.Run(() => Consume("m14-sentiment", processor.Analyze, stoppingToken), stoppingToken));
    }

    private async Task Consume(
        string group, Func<Review, CancellationToken, Task> handle, CancellationToken ct)
    {
        await transport.SetupTopics(ct);
        using var consumer = new ConsumerBuilder<string, string>(new ConsumerConfig
        {
            BootstrapServers = transport.Bootstrap,
            GroupId = group,
            EnableAutoCommit = false,
            AutoOffsetReset = AutoOffsetReset.Earliest,
            AllowAutoCreateTopics = false
        }).Build();
        consumer.Subscribe(KafkaTransport.InputTopic);
        while (!ct.IsCancellationRequested)
        {
            ConsumeResult<string, string>? received = null;
            try
            {
                received = consumer.Consume(ct);
                var envelope = EventJson.ParseReview(received.Message.Value);
                await handle(envelope.Data, ct);
                // Acknowledgement only after side effects succeeded: at-least-once, NOT exactly once.
                consumer.Commit(received);
            }
            catch (OperationCanceledException) when (ct.IsCancellationRequested) { break; }
            catch (Exception error)
            {
                logger.LogError(error, "Kafka consumer group {Group} failed at {Offset}",
                    group, received?.TopicPartitionOffset.ToString() ?? "n/a");
                if (received is not null)
                {
                    // Seek back for retry: failures must not silently skip a review.
                    try { consumer.Seek(received.TopicPartitionOffset); }
                    catch (Exception seekError) { logger.LogError(seekError, "Kafka seek failed"); }
                }
                try { await Task.Delay(1500, ct); } catch (OperationCanceledException) { break; }
            }
        }
        consumer.Close();
    }
}
