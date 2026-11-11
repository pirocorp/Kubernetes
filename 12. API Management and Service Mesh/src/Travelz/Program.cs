using System.Text.Json;

var mode = Environment.GetEnvironmentVariable("APP_MODE") ?? "agency-v1";
if (mode is not ("agency-v1" or "agency-v2" or "portal"))
    throw new InvalidOperationException("APP_MODE must be agency-v1, agency-v2 or portal.");

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddHttpClient("agency", c => c.Timeout = TimeSpan.FromSeconds(4));
var app = builder.Build();

app.MapGet("/healthz", () => Results.Text("ok", "text/plain"));
app.MapGet("/identity", () => Results.Ok(new { service = mode }));

if (mode == "portal")
{
    var agencyUrl = (Environment.GetEnvironmentVariable("AGENCY_URL")
                     ?? "http://127.0.0.1:5200").TrimEnd('/');

    app.MapGet("/portal/{city}", async Task<IResult> (
        string city, IHttpClientFactory factory, HttpContext context) =>
    {
        if (!ValidCity(city))
            return Results.BadRequest(new ApiError("validation_error", "City name is invalid"));

        // Correlation context is application-level; it is not a replacement for
        // OpenTelemetry traces, Istio tracing or mutual TLS service identities.
        var correlationId = Guid.NewGuid().ToString("N");
        using var request = new HttpRequestMessage(
            HttpMethod.Get, agencyUrl + "/api/travels/" + Uri.EscapeDataString(city));
        request.Headers.TryAddWithoutValidation("X-Correlation-Id", correlationId);
        try
        {
            using var response = await factory.CreateClient("agency")
                .SendAsync(request, context.RequestAborted);
            if (!response.IsSuccessStatusCode)
                return Results.Json(new ApiError("upstream_failure", "Agency request failed"),
                    statusCode: StatusCodes.Status502BadGateway);

            await using var stream = await response.Content.ReadAsStreamAsync(context.RequestAborted);
            using var document = await JsonDocument.ParseAsync(stream, cancellationToken: context.RequestAborted);
            Console.WriteLine("portal correlation={0} city={1}", correlationId, city);
            return Results.Ok(new
            {
                channel = "travel-portal",
                correlationId,
                quote = document.RootElement.Clone()
            });
        }
        catch (HttpRequestException)
        {
            return Results.Json(new ApiError("upstream_failure", "Agency unavailable"),
                statusCode: StatusCodes.Status502BadGateway);
        }
        catch (TaskCanceledException) when (!context.RequestAborted.IsCancellationRequested)
        {
            return Results.Json(new ApiError("timeout", "Agency request timed out"),
                statusCode: StatusCodes.Status504GatewayTimeout);
        }
    });
}
else
{
    var version = mode == "agency-v1" ? "v1" : "v2";
    app.MapGet("/api/travels/{city}", (string city, HttpContext context) =>
    {
        if (!ValidCity(city))
            return Results.BadRequest(new ApiError("validation_error", "City name is invalid"));

        // Explicitly simulated failure makes local retry/fallback observable.
        if (version == "v2" && city.Equals("Failover", StringComparison.OrdinalIgnoreCase))
            return Results.Json(new ApiError("unavailable", "Simulated v2 failure"),
                statusCode: StatusCodes.Status503ServiceUnavailable);

        var correlationId = context.Request.Headers["X-Correlation-Id"].ToString();
        if (correlationId.Length > 64) correlationId = "";
        Console.WriteLine("agency version={0} city={1} correlation={2}", version, city, correlationId);

        var quote = new
        {
            city,
            version,
            hotel = version == "v1" ? 120.00m : 118.00m,
            flight = 240.00m,
            car = 45.00m,
            insuranceIncluded = version == "v2",
            currency = "EUR",
            correlationId
        };
        return Results.Ok(quote);
    });
}

app.Run();

static bool ValidCity(string city) =>
    !string.IsNullOrWhiteSpace(city) && city.Length <= 80 &&
    city.All(c => char.IsLetter(c) || c is '-' or ' ');

record ApiError(string Code, string Message);
