# Lab 12-D — Deprecation, sunset, клиентска миграция и rollback

**Учебна цел:** да управляваш безопасен lifecycle на стара major API версия, да уведомиш consumer-ите, да наблюдаваш тяхното преминаване към v2 и да различаваш `deprecated` от действително `retired`. Основен източник: [Red Hat API Versioning workshop — deprecate and sunset](https://www.solutionpatterns.io/solution-pattern-api-versioning/api-versioning/03-demo.html).

**Важно:** датите 2026-01-01 (deprecation) и 2027-06-30 (sunset) са **изцяло учебни**, а локалното състояние може да бъде превключено ръчно независимо от текущата дата. Това не е действителна политика на Red Hat или Globex.

## 1. Предпоставки и самостоятелно стартиране

- Python 3.10+, .NET SDK 10, Bash, портове **8080/8081** и файловете от Module 12.
- Изпълни **в един и същ Bash shell**. Ако Lab 12-C още работи със същия ключ и `active` policy, пропусни само стартирането на процесите и премини към раздел 2.
- Ако започваш **директно** оттук, изпълни целия блок:

```bash
mkdir -p .runtime
dotnet build src/OrderPlacementApi/OrderPlacementApi.csproj
export API_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
export ADMIN_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
ASPNETCORE_URLS=http://127.0.0.1:8080 V1_LIFECYCLE=active ALLOWED_MAJOR=both \
  dotnet run --project src/OrderPlacementApi/OrderPlacementApi.csproj \
    --no-build --no-launch-profile > .runtime/api.log 2>&1 &
M12_API_PID=$!
python3 tools/policy.py set active
python3 tools/gateway.py > .runtime/gateway.log 2>&1 &
M12_GATEWAY_PID=$!
curl -fsS http://127.0.0.1:8081/healthz
```

**Очаквано:** `ok`. Ако видиш `Connection refused`, прегледай `.runtime/api.log` и `.runtime/gateway.log` и повтори проверката след startup. **Не** стартирай второ копие върху заетите портове.

## 2. Baseline: v1 и v2 обслужват заявки

```bash
python3 tools/check.py --base-url http://127.0.0.1:8081 --v1-status active
python3 tools/metrics.py
```

**Очаквано:** v1.0 клиент работи чрез `/v1`, v1.1 клиент също; v2 използва `/v2`. В version analytics има поне `v1_201` и `v2_201`. Запази тези стойности за сравнение след миграцията.

## 3. Обяви deprecation — без да чупиш v1

Публикувай migration guide и release notes **преди** техническите промени: [MIGRATION.md](../docs/MIGRATION.md). Покажи как се сменят URI, body и tests. След това симулирай server policy:

```bash
python3 tools/policy.py set deprecated
python3 tools/policy.py get
python3 tools/check.py --base-url http://127.0.0.1:8081 --v1-status deprecated
python3 consumers/client.py --version 1.0.0 --base-url http://127.0.0.1:8081
```

**Очаквано:** старият consumer **все още получава 201** и работи; отговорът съдържа `Deprecation: @<unix-seconds>` по **RFC 9745** и `Sunset: <HTTP-date>` по **RFC 8594**. `tools/check.py` проверява и двата header-а.

Защо няма 410? **Deprecation сам по себе си не променя функционалността.** Той е предупреждение и план за миграция. `Sunset` обявява очакван бъдещ момент, но физическото изключване трябва да се прави след предварително съобщена policy и monitoring. В локалния lab датите са фиктивни.

## 4. Мигрирай клиента към v2

```bash
python3 consumers/client.py --version 2.0.0 --base-url http://127.0.0.1:8081
python3 tools/metrics.py
```

**Очаквано:** v2 HTTP 201 без Deprecation/Sunset warnings; броят `v2_201` нараства. Ако `v1_201` още се увеличава, значи **поне някой** все още ползва стария endpoint; в този demo може да е един от нашите тестове. Броят заявки **не е** брой уникални потребители.

Правилна production процедура: списък на consumer owners, проследяване на last-used, договорен migration window, поддържан v1 fallback, актуализирани release notes и API portal documentation. Не използвай „няма traffic през последните 5 минути“ като достатъчен критерий за sunset.

## 5. Sunset / retirement: контролирано 410 Gone

След симулирано уведомяване и готовност на consumers промени локалната policy:

```bash
python3 tools/policy.py set sunset
python3 tools/check.py --base-url http://127.0.0.1:8081 --v1-status sunset
if python3 consumers/client.py --version 1.0.0 --base-url http://127.0.0.1:8081; then
  echo 'FAIL: retired v1 client still succeeded'
  exit 1
else
  echo 'PASS: retired v1 client rejected'
fi
python3 consumers/client.py --version 2.0.0 --base-url http://127.0.0.1:8081
python3 tools/metrics.py
```

**Очаквано:** `POST /v1/placeorder` → **410 Gone** (с lifecycle headers); `POST /v2/placeorder` → **201 Created**. В counters се появява `v1_410`, а `v2_201` продължава да расте.

**Разграничение от 3scale:** оригиналният Red Hat workshop показва и управление на **нови записвания към стари application plans**. Това е отделно от прекратяване на всички съществуващи заявки. Нашият локален `sunset` направо връща 410; не представя този преход като реални действия върху 3scale Product или Application Plan.

## 6. Rollback, наблюдение и cleanup

При неочаквано открит критичен consumer можеш да възстановиш `active`:

```bash
python3 tools/policy.py set active
python3 tools/check.py --base-url http://127.0.0.1:8081 --v1-status active
```

**Очаквано:** v1 отново дава 201. В production rollback трябва да мине през approval, актуализация на комуникацията и проверка за data migration; тук се сменя **само gateway routing policy**, не business data.

### Troubleshooting

| Проблем | Проверка | Корекция |
|---|---|---|
| 503 от gateway | `python3 tools/policy.py get` | Върни валидна policy `active/deprecated/sunset` |
| 502 от gateway | `curl http://127.0.0.1:8080/healthz` | Стартирай backend, провери `.runtime/api.log` |
| Няма lifecycle headers | Policy active, или заявката е към backend директно | Ползвай `--base-url http://127.0.0.1:8081` |
| Стар клиент 201 след „sunset“ | Приложението е директно на 8080 | Тестът на management policy минава **през 8081** |
| v2 дава 400 | Consumer все още изпраща `firstName`, `lastName` | Използвай [migration guide](../docs/MIGRATION.md) |
| Metrics 401 | Различен `ADMIN_KEY` | Използвай ключа от shell-а, стартирал gateway |

### Cleanup

```bash
if test -n "${M12_GATEWAY_PID:-}"; then kill "$M12_GATEWAY_PID" 2>/dev/null || true; unset M12_GATEWAY_PID; fi
if test -n "${M12_API_PID:-}"; then kill "$M12_API_PID" 2>/dev/null || true; unset M12_API_PID; fi
unset API_KEY ADMIN_KEY
rm -f .runtime/lifecycle.json
```

Не изтривай чужди файлове от `.runtime`. Всички процеси са локални; няма OpenShift ресурси.

**Приемане:** наблюдаваш `201 → 201+Deprecation/Sunset → 410 → rollback 201` за v1 и непрекъснат `201` за v2, със статистика по версия.
