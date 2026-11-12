# Lab 12-B — ASP.NET Core 10: две API версии и три поколения клиенти

**Учебна цел:** изпълни реален OrderPlacement API с URL versioning и демонстрирай как клиент 1.0.0 работи върху 1.1.0 backend, но не може да изпраща стар payload към v2. Оригинал: [Red Hat — Enable Versions 1.0.0, 1.1.0 and 2.0.0](https://www.solutionpatterns.io/solution-pattern-api-versioning/api-versioning/03-demo.html).

## 1. Предпоставки

- Инсталиран **.NET 10 SDK**, Python 3.10+, Bash, Git, свободен TCP **8080**. Не са необходими NuGet библиотеки извън .NET shared framework, база данни, OpenShift или 3scale.
- Работна директория = коренът на Module 12. Файловете са [Program.cs](../src/OrderPlacementApi/Program.cs), [csproj](../src/OrderPlacementApi/OrderPlacementApi.csproj), [три JSON payload-а](../examples/order-1.0.0.json) и [проверки](../tools/check.py).
- `API_KEY` е само учебна тайна; **не** го записвай в Git. API е bind-нат на `127.0.0.1:8080`; не го публикувай в интернет.

```bash
dotnet --version
python3 --version
test -f src/OrderPlacementApi/Program.cs
test -f examples/order-1.0.0.json
test -f examples/order-1.1.0.json
test -f examples/order-2.0.0.json
```

**Очаквано:** SDK започва с `10.`; всички файлове са налични. `dotnet --version` само по себе си не доказва компилация.

## 2. Как е реализирана съвместимостта?

- **v1 endpoint**: `POST /v1/placeorder` приема `firstName`, `lastName`, `sku`, `quantity` и *optional* `deliveryInstructions`. Използва 1.1.0 schema, затова стар 1.0.0 клиент работи без промени.
- **v2 endpoint**: `POST /v2/placeorder` изисква `fullName`, `sku`, `quantity`; отхвърля `firstName` и `lastName`. Това е breaking change.
- **`X-API-Revision`** показва текущата schema revision за обслужената major линия — `1.1.0` или `2.0.0`.
- `API_KEY` се проверява преди API operation; грешките връщат `ApiError {code,message}`.
- **`ALLOWED_MAJOR=both|v1|v2`** позволява локално една инстанция, а в OpenShift — два отделни backend Deployment-а от същия image.
- Данните са **само в паметта**; `orderId` е симулиран брояч. Няма webhook.site, съхранение на поръчки, интеграция с payments или реален customer data pipeline.

## 3. Компилирай и стартирай API

Изпълни следния блок в **един Bash терминал**. Приложението се стартира във фон, за да могат следващите проверки да използват същия `API_KEY`:

```bash
dotnet restore src/OrderPlacementApi/OrderPlacementApi.csproj
dotnet build src/OrderPlacementApi/OrderPlacementApi.csproj --no-restore
mkdir -p .runtime
export API_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
test "${#API_KEY}" -ge 16
ASPNETCORE_URLS=http://127.0.0.1:8080 \
V1_LIFECYCLE=active ALLOWED_MAJOR=both \
dotnet run --project src/OrderPlacementApi/OrderPlacementApi.csproj --no-build --no-launch-profile \
  > .runtime/api.log 2>&1 &
M12_API_PID=$!
```

След стартиране:

```bash
curl -fsS http://127.0.0.1:8080/healthz
python3 tools/check.py --base-url http://127.0.0.1:8080 --v1-status active
```

**Очаквано:** `ok`, серия от `PASS` тестове за 401, 201, 400 и финално `ALL VERSION COMPATIBILITY CHECKS PASSED`.

Ако услугата още стартира, повтори `curl` след готовността на процеса и провери `cat .runtime/api.log`. **Не** стартирай второ копие върху същия порт. При `401` увери се, че `API_KEY` е от shell-а, стартирал API, а не нова случайна стойност.

## 4. Изпитай трите поколения clients

В **същия Bash терминал**:

```bash
python3 consumers/client.py --version 1.0.0 --base-url http://127.0.0.1:8080
python3 consumers/client.py --version 1.1.0 --base-url http://127.0.0.1:8080
python3 consumers/client.py --version 2.0.0 --base-url http://127.0.0.1:8080
```

**Очаквано:** всички връщат `HTTP: 201`. За първите два клиента `X-API-Revision: 1.1.0` и endpoint `/v1`. За третия — `2.0.0` и endpoint `/v2`.

### 4.1. Умишлено несъвместим клиент

Проверката е в `tools/check.py`: `v2` отхвърля `v1` JSON (старите `firstName/lastName`) с HTTP 400, а `v1` отхвърля `fullName`-only JSON с HTTP 400. Това доказва, че двете линии **не са взаимозаменяеми**.

```bash
python3 tools/check.py --base-url http://127.0.0.1:8080 --v1-status active
```

**Ключова идея:** API provider не бива да сменя значението на един и същ `/v1` endpoint и да очаква старите клиенти „сами“ да разберат новия request format. Нужни са паралелна версия, известяване и план за миграция.

## 5. Анализ на грешки

| Симптом | Причина/проверка | Корекция |
|---|---|---|
| `dotnet: command not found` | SDK липсва | Инсталирай .NET SDK **10**, а не само runtime |
| `dotnet build` fail | `dotnet restore` и error output | Провери SDK, csproj и source; без root права |
| `Connection refused` | API не е стартирано | `cat .runtime/api.log` и `kill -0 "$M12_API_PID"` |
| `HTTP 401` | Няма ключ/различен ключ | Запази същия `API_KEY` в същия shell |
| `HTTP 400` | Входният payload не съвпада със schema | Сравни трите JSON примера и съответния OpenAPI |
| v1 не е наличен | `ALLOWED_MAJOR=v2` | За локалния lab използвай `both`; за OpenShift има отделни инстанции |
| `Address already in use` | Порт 8080 е зает | Спри собствения стар процес; не убивай чужди приложения |

## 6. Cleanup

Тези команди спират **само** стартирания от упражнението процес:

```bash
if test -n "${M12_API_PID:-}"; then
  kill "$M12_API_PID" 2>/dev/null || true
  unset M12_API_PID
fi
unset API_KEY
```

По желание `dotnet clean src/OrderPlacementApi/OrderPlacementApi.csproj`; локалният `.runtime/api.log` може да се изтрие, след като вече не е нужен. Няма cluster resources.

**Приемане:** успешен build, проверка през HTTP, работа на трите client версии, и два отрицателни cross-version теста.
