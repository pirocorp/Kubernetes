# Lab 10-D — API management: authentication, quotas, analytics

**Цел:** отделяме **upstream API** от **gateway**, което контролира достъпа, брои заявките и прилага ограничение. В Red Hat това е ролята на **3scale/APIcast**; тук използваме собствен **локален преподавателски proxy**, който **не** е 3scale.

## Предпоставки

- **.NET SDK 10**, Python 3.10+, Bash и `curl`; локални портове **8080** и **8081** трябва да са свободни. Не се изисква предварително изпълнен Lab 10-C, OpenShift, 3scale или платен лиценз.
- Работна директория = коренът на Module 10. Реалният upstream проект е [ProductsApi.csproj](../src/ProductsApi/ProductsApi.csproj) с [Program.cs](../src/ProductsApi/Program.cs), а gateway е [tools/gateway.py](../tools/gateway.py).
- **Не** стартирай втори backend върху port 8080. Ако Lab 10-C още работи, изпълни неговия собствен cleanup (чрез запазения му PID), преди да започнеш този lab.

## 1. Стартирай upstream API и gateway от чиста среда

**Изпълни блока в един Bash терминал**, за да споделят двете приложения една и съща учебна тайна. Тези команди не зависят от терминал или process, оставен от предишен lab:

```bash
dotnet --version
dotnet build src/ProductsApi/ProductsApi.csproj -c Release
export API_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
export ADMIN_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
test "${#API_KEY}" -ge 16 && test "${#ADMIN_KEY}" -ge 16
export API_UPSTREAM=http://127.0.0.1:8080
ASPNETCORE_URLS=http://127.0.0.1:8080 dotnet run \
  --project src/ProductsApi/ProductsApi.csproj \
  -c Release --no-build --no-launch-profile > /tmp/m10d-api.log 2>&1 &
M10D_API_PID=$!
python3 tools/gateway.py > /tmp/m10d-gateway.log 2>&1 &
GATEWAY_PID=$!
```

**Преди тестовете** провери готовността; ако една от заявките не успее, виж `/tmp/m10d-api.log` и `/tmp/m10d-gateway.log` и повтори, след като процесът стартира:

```bash
curl -fsS http://127.0.0.1:8080/healthz
curl -sS -o /dev/null -w 'gateway unauthorized: %{http_code}\n' \
  http://127.0.0.1:8081/v1/products
```

**Очаквано:** `ok` от upstream и `401` от gateway без ключ. Не продължавай, ако имаш `Connection refused` или чужд процес на някой от двата порта. Backend и gateway валидират един и същ `API_KEY` (учебна defense-in-depth демонстрация), но нямат enterprise IdP/portal/billing.

Gateway и API и двата валидират header `X-Api-Key`. Това е **учебна defense-in-depth схема**; няма потребители, IdP, истински API products или billing.

## 2. Authentication и rate limiting

```bash
curl -sS -o /dev/null -w 'no key -> %{http_code}\n' \
  http://127.0.0.1:8081/v1/products
for i in 1 2 3 4; do
  curl -sS -o /dev/null -w "request $i -> %{http_code}\n" \
    -H "X-Api-Key: $API_KEY" http://127.0.0.1:8081/v1/products
done
```

**Очаквано:** без ключ → **401**, първите три валидни заявки в рамките на 15 секунди → **200**, четвъртата → **429**. Ако ги изпълниш много бавно и прозорецът изтече, повтори непосредствено 4-те заявки; това е **in-memory rolling time-window**. Не подавай произволни production API keys.

## 3. Прочети counters

```bash
curl -fsS -H "X-Admin-Key: $ADMIN_KEY" http://127.0.0.1:8081/_metrics
curl -sS -o /dev/null -w 'metrics without admin key -> %{http_code}\n' \
  http://127.0.0.1:8081/_metrics
```

**Очаквано:** JSON counters с `requests`, `denied`, `limited` и втори отговор 401. Counter-ите се нулират след рестарт; локалната метрика **не** е production audit log.

## 4. Как това се отнася към Red Hat 3scale

| Нашата демонстрация | Enterprise capability с 3scale |
|---|---|
| Един `API_KEY` | Приложения, developer accounts и credentials |
| In-memory лимит 3/15 сек | Application plans, methods, metrics, quotas, configurable policies |
| Прокси с URL на upstream | APIcast gateway и маршрутизация към backend APIs |
| `/_metrics` counters | API analytics, usage reports, developer portal |
| Локален Python процес | Managed/self-managed gateway с lifecycle и интеграции |

Оригинал: [Red Hat API-First Solution Pattern](https://www.solutionpatterns.io/solution-pattern-api-first/api-first/index.html). Референция: [3scale — Getting started / API access policies](https://docs.redhat.com/en/documentation/red_hat_3scale_api_management/2.16/html/getting_started/launching-apis).

**За реална 3scale инсталация** са необходими достъп, лицензи/условия и поддържан OpenShift клъстер с нужните admin права. Не се опитвай да инсталираш 3scale Operator в общ Developer Sandbox. В този lab **не твърдим**, че локалният proxy имплементира production API management. JWT/OIDC, TLS между services, identity federation, distributed rate limits и persistent metrics са отделни enterprise задачи.

## Troubleshooting

`502` → upstream на 8080 не работи; `401` → различен/липсващ ключ; `429` → учебният лимит е достигнат; `Address already in use` → има втори gateway на 8081. **Не** променяй contract response, за да прикриеш gateway проблем.

## Cleanup

Използвай **само записаните PID-ове от този lab** (не прекъсвай други API процеси). Ако вече си стартирал gateway/endpoint и си загубил PID-а, прегледай съответните портове преди ръчно спиране:

```bash
if test -n "${GATEWAY_PID:-}"; then kill "$GATEWAY_PID" 2>/dev/null || true; unset GATEWAY_PID; fi
if test -n "${M10D_API_PID:-}"; then kill "$M10D_API_PID" 2>/dev/null || true; unset M10D_API_PID; fi
unset API_KEY ADMIN_KEY API_UPSTREAM
```

Няма Kubernetes/OpenShift ресурси. За допълнителна end-to-end проверка на **mock → .NET API → gateway** от чиста среда изпълни [локалната acceptance suite](../scripts/verify-local.sh) чрез `bash scripts/verify-local.sh`; тя проверява портовете, генерира собствени временни ключове и спира собствените test процеси.

**Критерий:** наблюдавани **401 / 200 / 429** и admin-only метрика; разбираш защо gateway не замества backend security.
