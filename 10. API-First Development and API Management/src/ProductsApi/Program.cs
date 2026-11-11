using System.Collections.Concurrent;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

var apiKey = Environment.GetEnvironmentVariable("API_KEY");
if (string.IsNullOrWhiteSpace(apiKey) || apiKey.Length < 16)
{
    throw new InvalidOperationException("Set API_KEY to a secret of at least 16 characters.");
}

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

// Demo-only API key authentication. Real partner access should use a managed identity
// solution or an API gateway; never hardcode the key or write it to logs.
app.Use(async (context, next) =>
{
    if (!context.Request.Path.StartsWithSegments("/v1"))
    {
        await next();
        return;
    }

    var supplied = context.Request.Headers["X-Api-Key"].ToString();
    var expected = Encoding.UTF8.GetBytes(apiKey);
    var received = Encoding.UTF8.GetBytes(supplied);
    if (expected.Length != received.Length ||
        !CryptographicOperations.FixedTimeEquals(expected, received))
    {
        context.Response.StatusCode = StatusCodes.Status401Unauthorized;
        await context.Response.WriteAsJsonAsync(new ApiError("unauthorized", "Invalid API key"));
        return;
    }

    await next();
});

var products = new ConcurrentDictionary<string, Product>();
products["p-100"] = new Product("p-100", "Keyboard", 49.9m, "EUR");
products["p-101"] = new Product("p-101", "Mouse", 19.5m, "EUR");
var nextId = 101;

app.MapGet("/healthz", () => Results.Text("ok", "text/plain"));

app.MapGet("/v1/products", () =>
    Results.Ok(new ProductList(products.Values.OrderBy(p => p.Id).ToArray())))
    .WithName("listProducts");

app.MapGet("/v1/products/{id}", (string id) =>
    products.TryGetValue(id, out var product)
        ? Results.Ok(product)
        : Results.NotFound(new ApiError("not_found", "Product not found")))
    .WithName("getProductById");

app.MapPost("/v1/products", async (HttpRequest request) =>
{
    NewProduct? input;
    try
    {
        input = await request.ReadFromJsonAsync<NewProduct>();
    }
    catch (JsonException)
    {
        return Results.BadRequest(new ApiError("validation_error", "Invalid product"));
    }

    if (input is null ||
        string.IsNullOrWhiteSpace(input.Name) ||
        input.Name.Length > 100 ||
        input.Price < 0 ||
        input.Currency != "EUR")
    {
        return Results.BadRequest(new ApiError("validation_error", "Invalid product"));
    }

    var id = "p-" + Interlocked.Increment(ref nextId);
    var product = new Product(id, input.Name, input.Price, input.Currency);
    products[id] = product;
    return Results.Created("/v1/products/" + id, product);
}).WithName("createProduct");

app.Run();

record Product(string Id, string Name, decimal Price, string Currency);
[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
record NewProduct(
    [property: JsonRequired] string Name,
    [property: JsonRequired] decimal Price,
    [property: JsonRequired] string Currency);
record ProductList(Product[] Items);
record ApiError(string Code, string Message);
