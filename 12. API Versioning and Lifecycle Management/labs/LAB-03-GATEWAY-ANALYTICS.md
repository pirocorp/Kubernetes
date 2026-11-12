# Lab 12-C — API Provider: version routing, analytics и 3scale concepts

**Учебна цел:** да виждаш кои consumers още използват v1, да поддържаш паралелни major линии и да разделяш backend routing от API management. Това адаптира provider/consumer частите от [Red Hat workshop](https://www.solutionpatterns.io/solution-pattern-api-versioning/api-versioning/03-demo.html), **без** да инсталира 3scale в чужд shared cluster.

## 1. Предпоставки

- Linux/macOS/WSL Bash, Python 3.10+, **.NET SDK 10**, Git, свободни TCP портове **8080 (API)** и **8081 (gateway)**.
- Работна директория: коренът на Module 12. Всички необходими файлове са включени: [C# API](../src/OrderPlacementApi/Program.cs), [gateway.py](../tools/gateway.py), [policy.py](../tools/policy.py), [metrics.py](../tools/metrics.py), [HTTP тестовете](../tools/check.py).
- Не е нужно да изпълняваш Lab 12-B предварително — стартът на API е даден по-долу. Не работи едновременно с друга инстанция на портове 8080/8081. Не използвай production credentials.

## 2. Подготви две локални услуги

```bash
mkdir -p .runtime
dotnet build src/OrderPlacementApi/OrderPlacementApi.csproj
export API_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
export ADMIN_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
test "${#API_KEY}" -ge 16 && test "${#ADMIN_KEY}" -ge 16
ASPNETCORE_URLS=http://127.0.0.1:8080 V1_LIFECYCLE=active ALLOWED_MAJOR=both \
  dotnet run --project src/OrderPlacementApi/OrderPlacementApi.csproj \
    --no-build --no-launch-profile > .runtime/api.log 2>&1 &
M12_API_PID=$!
python3 tools/policy.py set active
python3 tools/gateway.py > .runtime/gateway.log 2>&1 &
M12_GATEWAY_PID=$!
```

Провери, че и двете приложения са готови:

```bash
curl -fsS http://127.0.0.1:8080/healthz
curl -fsS http://127.0.0.1:8081/healthz
python3 tools/policy.py get
```

**Очаквано:** `ok` и от двата HTTP портa; policy = `active`. Ако някоя проверка не работи, виж `cat .runtime/api.log` и `cat .runtime/gateway.log` и не продължавай.

**Какво е gateway?** В оригинала 3scale/APIcast дава public API endpoint, authentication, mapping rules, metrics и application plans. Нашият Python gateway е **само учебна симулация на routing/броене**. Той приема header `X-Api-Key`, препраща към същия ASP.NET Core API, записва **aggregate counts**, а отделният admin key дава достъп до `/_metrics`. Няма portal, real application plans, OIDC, persistent statistics, TLS или distributed quota.

## 3. Consumer traffic по двете версии

Изпълни HTTP contract проверките срещу **gateway**, не директно срещу backend:

```bash
python3 tools/check.py --base-url http://127.0.0.1:8081 --v1-status active
python3 consumers/client.py --version 1.0.0 --base-url http://127.0.0.1:8081
python3 consumers/client.py --version 1.1.0 --base-url http://127.0.0.1:8081
python3 consumers/client.py --version 2.0.0 --base-url http://127.0.0.1:8081
python3 tools/metrics.py
```

**Очаквано:** старият и новият v1 client получават HTTP 201 през **`/v1/placeorder`**; v2 client получава HTTP 201 през **`/v2/placeorder`**. В metrics има поне `v1_201`, `v2_201`, `v1_401`, `v2_400` (зависимo от тестовете), които доказват различни модели на потребление.

### Какво НЕ доказват тези counters?

- Не съхраняват данни след gateway restart.
- Не са уникални потребители: един consumer може да изпрати 100 заявки.
- Не показват последна употреба на стар client по identity — нямаме потребителски профили.
- Не са достатъчни сами по себе си за production решение за sunset.

За production се нуждаем от 3scale traffic analytics/metrics **по версия**, developer accounts и telemetry за действителните външни клиенти.

## 4. Как това се отнася към 3scale?

| Enterprise ресурс | Какво прави | Какво показва нашият lab |
|---|---|---|
| **3scale Product** | Публичен API, portal и management | Един входен gateway адрес |
| **3scale Backend** | Препраща към съответния microservice | `/v1`/ `/v2` се маршрутизират към API |
| **Mapping Rules** | Разпознават конкретни methods/paths | Version path matching |
| **Application Plan** | Usage limits и достъп на consumer | Само един учебен API key |
| **Method/Metric** | Брои заявки по API version | `v1_201`, `v2_201` |
| **Developer Portal / ActiveDocs** | Договори и достъп за клиенти | Нашите Markdown/OpenAPI файлове |
| **APIcast Staging/Production** | Промоция на управляемата gateway config | Тук **няма** истинска промоция |

Оригиналният Red Hat сценарий управлява 3scale resources чрез **GitOps/Argo CD** и отделни git tags за `1.0.0`, `1.1.0`, `2.0.0`. Това е **платформена конфигурация**, която трябва да се версионира независимо от кода на backend. Нашият `tools/policy.py` показва промяната на policy state, но **не** е ArgoCD приложение.

## 5. Диагностика и cleanup

| Симптом | Провери | Корекция |
|---|---|---|
| gateway HTTP `502` | `curl http://127.0.0.1:8080/healthz` | Backend не работи; виж `.runtime/api.log` |
| HTTP `401` | `API_KEY` и gateway процес | Използвай ключа от началото на същия Bash shell |
| `Missing lifecycle policy` | `python3 tools/policy.py get` | `python3 tools/policy.py set active` |
| metrics HTTP `401` | `ADMIN_KEY` | `tools/metrics.py` чете ADMIN_KEY от environment |
| `Address already in use` | портове 8080 и 8081 | Спри **собствен** предходен процес |

За следващия **Lab 12-D** можеш да запазиш и двата процеса и двете environment променливи. Ако приключваш:

```bash
if test -n "${M12_GATEWAY_PID:-}"; then kill "$M12_GATEWAY_PID" 2>/dev/null || true; unset M12_GATEWAY_PID; fi
if test -n "${M12_API_PID:-}"; then kill "$M12_API_PID" 2>/dev/null || true; unset M12_API_PID; fi
unset API_KEY ADMIN_KEY
rm -f .runtime/lifecycle.json
```

Няма клъстерни ресурси. `.runtime/api.log` и `.runtime/gateway.log` са локални и могат да бъдат изтрити след troubleshooting.

**Приемане:** двата major endpoint-а работят едновременно, виждаш version-specific counters и можеш да обясниш разликата между 3scale Product, Backend, Application Plan и Mapping Rule.
