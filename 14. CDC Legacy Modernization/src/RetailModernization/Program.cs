using RetailModernization;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddHttpClient();
builder.Services.AddSingleton<CdcProjection>();
builder.Services.AddHostedService<CdcWorker>();
var app = builder.Build();
var mode = app.Configuration["APP_MODE"] ?? "legacy";
if (mode != "legacy" && mode != "modern")
    throw new InvalidOperationException("APP_MODE must be legacy or modern");

app.MapGet("/healthz", () => Results.Text("ok", "text/plain"));
if (mode == "legacy")
    LegacyRoutes.Map(app);
else
    ModernRoutes.Map(app);
app.Run();
