using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

var key = Environment.GetEnvironmentVariable("API_KEY");
if (string.IsNullOrWhiteSpace(key) || key.Length < 16)
    throw new InvalidOperationException("Set API_KEY to a secret with at least 16 characters.");

var lifecycle = Environment.GetEnvironmentVariable("V1_LIFECYCLE") ?? "active";
if (lifecycle is not ("active" or "deprecated" or "sunset"))
    throw new InvalidOperationException("V1_LIFECYCLE must be active, deprecated or sunset.");

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();
var orderSequence = 0;

app.Use(async (context, next) =>
{
    if (!context.Request.Path.StartsWithSegments("/v1") &&
        !context.Request.Path.StartsWithSegments("/v2"))
    {
        await next();
        return;
    }

    var supplied = Encoding.UTF8.GetBytes(context.Request.Headers["X-Api-Key"].ToString());
    var expected = Encoding.UTF8.GetBytes(key);
    if (supplied.Length != expected.Length ||
        !CryptographicOperations.FixedTimeEquals(supplied, expected))
    {
        context.Response.StatusCode = StatusCodes.Status401Unauthorized;
        await context.Response.WriteAsJsonAsync(new ApiError("unauthorized", "Invalid API key"));
        return;
    }

    await next();
});

app.MapGet("/healthz", () => Results.Text("ok", "text/plain"));

app.MapPost("/v1/placeorder", async (HttpContext context) =>
{
    // The major version in the URL stays /v1 for compatible 1.0.0 -> 1.1.0 revisions.
    if (lifecycle is "deprecated" or "sunset")
    {
        // Illustrative training policy dates. Not actual Globex retirement dates.
        var deprecatedAt = new DateTimeOffset(2027, 1, 1, 0, 0, 0, TimeSpan.Zero);
        var sunsetAt = new DateTimeOffset(2027, 6, 30, 0, 0, 0, TimeSpan.Zero);
        context.Response.Headers["Deprecation"] = "@" +
            deprecatedAt.ToUnixTimeSeconds().ToString(CultureInfo.InvariantCulture);
        context.Response.Headers["Sunset"] = sunsetAt.ToString("r", CultureInfo.InvariantCulture);
    }

    if (lifecycle == "sunset")
        return Results.Json(new ApiError("gone", "Version v1 has been retired"),
            statusCode: StatusCodes.Status410Gone);

    if (!await TryReadOrder(context.Request))
        return Results.BadRequest(new ApiError("validation_error", "Invalid order payload"));

    var document = await ReadOrder(context.Request);
    using (document)
    {
        var root = document.RootElement;
        if (!ValidText(root, "firstName", 80) ||
            !ValidText(root, "lastName", 80) ||
            !ValidSkuAndQuantity(root) ||
            (root.TryGetProperty("deliveryInstructions", out var d) &&
             (d.ValueKind != JsonValueKind.String || d.GetString()!.Length > 200)) ||
            root.EnumerateObject().Any(p =>
                p.Name is not ("firstName" or "lastName" or "sku" or "quantity" or "deliveryInstructions")))
            return Results.BadRequest(new ApiError("validation_error", "Invalid order payload"));

        context.Response.Headers["X-API-Revision"] = "1.1.0";
        var id = "ord-" + Interlocked.Increment(ref orderSequence);
        return Results.Created("/v1/orders/" + id, new OrderReceipt(id, "accepted", "1.1.0"));
    }
});

app.MapPost("/v2/placeorder", async (HttpContext context) =>
{
    if (!await TryReadOrder(context.Request))
        return Results.BadRequest(new ApiError("validation_error", "Invalid order payload"));

    var document = await ReadOrder(context.Request);
    using (document)
    {
        var root = document.RootElement;
        if (!ValidText(root, "fullName", 160) ||
            !ValidSkuAndQuantity(root) ||
            (root.TryGetProperty("deliveryInstructions", out var d) &&
             (d.ValueKind != JsonValueKind.String || d.GetString()!.Length > 200)) ||
            root.EnumerateObject().Any(p =>
                p.Name is not ("fullName" or "sku" or "quantity" or "deliveryInstructions")))
            return Results.BadRequest(new ApiError("validation_error", "Invalid order payload"));

        context.Response.Headers["X-API-Revision"] = "2.0.0";
        var id = "ord-" + Interlocked.Increment(ref orderSequence);
        return Results.Created("/v2/orders/" + id, new OrderReceipt(id, "accepted", "2.0.0"));
    }
});

// A single process is sufficient to demonstrate version compatibility, not HA or persistence.
app.Run();

static async Task<bool> TryReadOrder(HttpRequest request)
{
    // Validate JSON once using a buffered body, then reset for the parser below.
    request.EnableBuffering();
    if (request.ContentLength is > 8192)
        return false;
    try
    {
        using var doc = await JsonDocument.ParseAsync(request.Body);
        return doc.RootElement.ValueKind == JsonValueKind.Object;
    }
    catch (JsonException)
    {
        return false;
    }
    finally
    {
        request.Body.Position = 0;
    }
}

static Task<JsonDocument> ReadOrder(HttpRequest request) =>
    JsonDocument.ParseAsync(request.Body);

static bool ValidText(JsonElement root, string property, int maxLength) =>
    root.TryGetProperty(property, out var value) &&
    value.ValueKind == JsonValueKind.String &&
    !string.IsNullOrWhiteSpace(value.GetString()) &&
    value.GetString()!.Length <= maxLength;

static bool ValidSkuAndQuantity(JsonElement root) =>
    ValidText(root, "sku", 100) &&
    root.TryGetProperty("quantity", out var qty) &&
    qty.ValueKind == JsonValueKind.Number &&
    qty.TryGetInt32(out var count) &&
    count is >= 1 and <= 100;

record OrderReceipt(string OrderId, string Status, string ApiVersion);
record ApiError(string Code, string Message);
