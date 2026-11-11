using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using GlobexReviews;

var builder = WebApplication.CreateBuilder(args);
var mode = builder.Configuration["REVIEWS_MODE"] ?? "local";
if (mode is not ("local" or "kafka" or "knative"))
    throw new InvalidOperationException("REVIEWS_MODE must be local, kafka, or knative.");
builder.Services.AddSingleton<ReviewState>();
builder.Services.AddSingleton<LocalChannels>();
builder.Services.AddSingleton<KafkaTransport>();
builder.Services.AddSingleton<ReviewProcessor>();
builder.Services.AddSingleton<OutputSinks>();
builder.Services.AddSingleton<SentimentScorer>();
builder.Services.AddHttpClient();
builder.Services.AddHostedService<LocalWorkers>();
builder.Services.AddHostedService<KafkaWorkers>();
var app = builder.Build();

// No external auth needed on loopback. If INGEST_KEY is present (e.g. OpenShift),
// it protects the public submission endpoint; webhooks remain internal-only.
app.Use(async (context, next) =>
{
    if (context.Request.Path.StartsWithSegments("/reviews") &&
        !string.IsNullOrWhiteSpace(app.Configuration["INGEST_KEY"]))
    {
        var expected = Encoding.UTF8.GetBytes(app.Configuration["INGEST_KEY"]!);
        var provided = Encoding.UTF8.GetBytes(context.Request.Headers["X-Api-Key"].ToString());
        if (expected.Length != provided.Length ||
            !CryptographicOperations.FixedTimeEquals(expected, provided))
        {
            context.Response.StatusCode = 401;
            await context.Response.WriteAsJsonAsync(new { code = "unauthorized" });
            return;
        }
    }
    await next();
});

app.MapGet("/healthz", () => Results.Text("ok", "text/plain"));
app.MapGet("/readyz", () => Results.Text("ready", "text/plain"));

app.MapPost("/reviews", async Task<IResult> (
    ReviewInput input, ReviewState state, LocalChannels queues,
    KafkaTransport kafka, IConfiguration config, CancellationToken ct) =>
{
    if (!ReviewRules.IsValid(input.ProductId, input.Category, input.Text))
        return Results.BadRequest(new { code = "validation_error", message = "Invalid category, productId or text" });

    var review = new Review(Guid.NewGuid().ToString(), input.ProductId, input.Category,
        input.Text, DateTimeOffset.UtcNow);
    try
    {
        if (mode == "local")
        {
            state.Put(review);
            await queues.Publish(review, ct);
        }
        else
        {
            await kafka.SendEvent(KafkaTransport.InputTopic,
                EventEnvelope<Review>.Create("globex.review.submitted", review), review.Id, ct);
            state.Put(review);
        }
    }
    catch (Exception error)
    {
        app.Logger.LogError(error, "Cannot publish review event");
        return Results.Json(new { code = "event_unavailable", message = "Event transport unavailable" },
            statusCode: StatusCodes.Status503ServiceUnavailable);
    }
    return Results.Accepted("/reviews/" + review.Id, new { reviewId = review.Id, status = "queued" });
});

app.MapGet("/reviews/{id}", (string id, ReviewState state) =>
    state.Get(id) is { } review ? Results.Ok(review) : Results.NotFound(new { code = "not_found" }));
app.MapGet("/reviews/approved", async Task<IResult> (OutputSinks outputs, ReviewState state, CancellationToken ct) =>
    Results.Ok(await outputs.ReadApproved(state, ct)));
app.MapGet("/metrics/sentiment", (ReviewState state) => Results.Ok(state.Summary()));
app.MapGet("/events", (ReviewState state) => Results.Ok(state.Events()));

// Real Knative Trigger delivery uses this internal Kubernetes Service, not a public Route.
// KafkaSource may wrap the Kafka JSON event inside dev.knative.kafka.event.
app.MapPost("/events/moderation", async Task<IResult> (
    HttpRequest request, ReviewState state, ReviewProcessor processor, CancellationToken ct) =>
{
    if (mode != "knative") return Results.NotFound();
    try
    {
        using var document = await JsonDocument.ParseAsync(request.Body, cancellationToken: ct);
        var cloudEvent = EventJson.ParseKnative(document.RootElement);
        state.Put(cloudEvent.Data);
        await processor.Moderate(cloudEvent.Data, ct);
        return Results.Accepted();
    }
    catch (JsonException) { return Results.BadRequest(new { code = "invalid_cloud_event" }); }
});

app.MapPost("/events/sentiment", async Task<IResult> (
    HttpRequest request, ReviewState state, ReviewProcessor processor, CancellationToken ct) =>
{
    if (mode != "knative") return Results.NotFound();
    try
    {
        using var document = await JsonDocument.ParseAsync(request.Body, cancellationToken: ct);
        var cloudEvent = EventJson.ParseKnative(document.RootElement);
        state.Put(cloudEvent.Data);
        await processor.Analyze(cloudEvent.Data, ct);
        return Results.Accepted();
    }
    catch (JsonException) { return Results.BadRequest(new { code = "invalid_cloud_event" }); }
});

app.Run();
