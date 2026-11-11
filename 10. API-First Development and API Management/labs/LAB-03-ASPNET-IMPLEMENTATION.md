# Lab 10-C — ASP.NET Core 10: implement the contract, then verify it

**Цел:** прилагаме вече дефинирания OpenAPI договор на C# и проверяваме реалните HTTP отговори. Оригинална идея: [Red Hat API-First Solution Pattern](https://www.solutionpatterns.io/solution-pattern-api-first/api-first/index.html). **Разлика:** вместо Quarkus използваме ASP.NET Core Minimal API.

## Предпоставки

- [.NET SDK 10](https://dotnet.microsoft.com/en-us/download/dotnet/10.0) с команда `dotnet`, Python 3.10+, Bash и `curl`; работна директория = корен на Module 10.
- Свободен TCP port **8080**; локален mock на 8082 не е нужен за този lab.
- Source: [ProductsApi.csproj](../src/ProductsApi/ProductsApi.csproj), [Program.cs](../src/ProductsApi/Program.cs), [OpenAPI договор](../contract/products-v1.openapi.json), [contract smoke suite](../tools/contract_check.py).
- Не е нужен NuGet пакет извън framework SDK / `Microsoft.AspNetCore.App` shared runtime. Не са нужни външни DB или cluster.

## 1. Разгледай implementation

- `GET /healthz` e публичен, `/v1/*` изисква `X-Api-Key`.
- `GET /v1/products` връща `ProductList` с `items`, `GET /v1/products/p-100` — `Product`, непознат ID — `404 ApiError`, `POST /v1/products` — `201` и `Location`.
- `Product`, `NewProduct`, `ProductList`, `ApiError` са C# record типове. Данните са **само в паметта** — рестартиране нулира новите продукти. Това е изрично ограничение на упражнението, а не тиха замяна на database слой.
- API key е демонстрация за authentication; production използва надежден IdP/gateway и защитени secret stores.

## 2. Build и run

```bash
dotnet --version
dotnet restore src/ProductsApi/ProductsApi.csproj
dotnet build src/ProductsApi/ProductsApi.csproj --no-restore
export API_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
test "${#API_KEY}" -ge 16
ASPNETCORE_URLS=http://127.0.0.1:8080 dotnet run --project src/ProductsApi/ProductsApi.csproj --no-build > /tmp/m10-api.log 2>&1 &
API_PID=$!
```

**Продължи в същия Bash терминал** с вече експортирания `API_KEY`. Приложението работи във фон. Ако API не е готово при първия `curl`, провери `cat /tmp/m10-api.log`, направи повторна заявка и потърси порт/SDK/configuration проблема. Не стартирай ново копие върху зает порт.

## 3. Тествай по OpenAPI

В същия терминал:

```bash
curl -fsS http://127.0.0.1:8080/healthz
curl -fsS -H "X-Api-Key: $API_KEY" http://127.0.0.1:8080/v1/products
python3 tools/contract_check.py --base-url http://127.0.0.1:8080
```

**Очаквано:** `GET /healthz` → `ok`; catalog с Keyboard/Mouse; contract suite проверява `200`, `401`, `404`, `201`, `400` (включително липсващо задължително поле) и структурите `Product`, `ProductList`, `ApiError`.

### Негативен тест

```bash
curl -sS -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:8080/v1/products
curl -sS -H "X-Api-Key: $API_KEY" -H 'Content-Type: application/json' \
  -d '{"name":"","price":-1,"currency":"EUR"}' \
  -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:8080/v1/products
```

**Очаквано:** `401` без ключ, `400` при невалиден product payload. Няма logging на API key.

**Граница на валидатора:** `tools/contract_check.py` проверява **подмножество** от schema правила (required/type/enum/additionalProperties за response тела), не е пълен OpenAPI semantic validator или end-to-end penetration test. Той проверява *реалния HTTP endpoint*, вместо да сравнява само C# типове по име.

## 4. Container image (локален, опционален)

При наличен Docker/Podman:

```bash
docker build -f Dockerfile -t m10-products:dev .
docker run --rm -p 127.0.0.1:18080:8080 --env API_KEY m10-products:dev
```

Провери в друг терминал `curl -fsS -H "X-Api-Key: $API_KEY" http://127.0.0.1:18080/v1/products`. Не изпълнявай локален Docker build, ако същият порт вече е зает. Image използва .NET 10 SDK за build и ASP.NET Core 10 runtime, слуша на **8080** и не изисква root за работа на приложението.

## Troubleshooting

| Симптом | Проверка | Действие |
|---|---|---|
| `dotnet: command not found` | `dotnet --info` | Инсталирай .NET 10 SDK |
| `Address already in use` | `ss -ltn | grep 8080` | Спри собствения предходен процес |
| App fails on startup | `test "${#API_KEY}" -ge 16` | Генерирай ключ и export преди run |
| `401` с header | Проверка дали двата терминала споделят **същия** secret | Подай същата стойност без печатане/log |
| Contract suite fails | Сравни конкретния method/path/status/schema с `contract/*.json` | Поправи implementation, не променяй договора само за да мине тестът |

## Cleanup

Ако имаш `API_PID` от собствения background run: `if test -n "${API_PID:-}"; then kill "$API_PID"; unset API_PID; fi`. Ако си създал container, спри го с Ctrl+C (използвано е `--rm`). По избор: `dotnet clean src/ProductsApi/ProductsApi.csproj`. След края на всички labs: `unset API_KEY`. Няма клъстерни ресурси.

**Критерий:** успешен `dotnet build`, работещ API и `contract_check.py` с деветте очаквани HTTP проверки, включително отказ на непознато JSON поле.
