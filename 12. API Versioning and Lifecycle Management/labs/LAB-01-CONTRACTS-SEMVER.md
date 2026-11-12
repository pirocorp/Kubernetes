# Lab 12-A — API versioning strategy, SemVer и съвместимост на договорите

**Учебна цел:** да определяш кога е нужна нова версия, кои промени нарушават съществуващи клиенти и как се планира съвместно съществуване на две major версии. Източник: [Red Hat API Versioning — Architecture](https://www.solutionpatterns.io/solution-pattern-api-versioning/api-versioning/02-architecture.html) и [основният Solution Pattern](https://www.solutionpatterns.io/solution-pattern-api-versioning/api-versioning/index.html).

## 1. Предпоставки

Python **3.10+**, Bash, Git. **Не** се изискват .NET, Docker, OpenShift, Apicurio, 3scale или платени услуги. Изпълни от корена на Module 12:

```bash
pwd
python3 --version
test -s contracts/orderplacement-1.0.0.openapi.json
test -s contracts/orderplacement-1.1.0.openapi.json
test -s contracts/orderplacement-2.0.0.openapi.json
python3 -m json.tool contracts/orderplacement-1.0.0.openapi.json >/dev/null
python3 -m json.tool contracts/orderplacement-1.1.0.openapi.json >/dev/null
python3 -m json.tool contracts/orderplacement-2.0.0.openapi.json >/dev/null
```

**Очаквано:** файловете са валидни JSON документи, които съдържат OpenAPI 3.0.3. JSON е официално допустим формат за OpenAPI — не е необходим YAML parser.

## 2. Стратегии за версиониране

| Стратегия | Пример | Предимство | Недостатък |
|---|---|---|---|
| URL major version | `POST /v1/placeorder`, `POST /v2/placeorder` | Ясен routing и наблюдение | Промяна на URI при major version |
| Header | `X-API-Version: 2` | Стабилен URI | Кеширане/диагностика/проксита изискват повече внимание |
| Endpoint name | `/placeorder_v2` | Лесно в прост API | Имена се натрупват |
| Отделен API Product | Два 3scale Products | Изолирани credentials/plan и sunset | Допълнителна платформена конфигурация |

**Избираме URL major version**, както Red Hat. Важно: Semantic Versioning `1.0.0`, `1.1.0`, `2.0.0` **не** означава, че всеки minor/patch има отделен URI. В този курс `1.0.0` и `1.1.0` се обслужват през **същия** `/v1`; breaking `2.0.0` е през `/v2`.

## 3. Анализ на трите договора

```bash
python3 - <<'PY'
import json
from pathlib import Path
for file in sorted(Path("contracts").glob("*.openapi.json")):
    c = json.loads(file.read_text())
    s = c["components"]["schemas"]["OrderRequest"]
    print(c["info"]["version"], list(c["paths"]), "required:", s["required"])
    print(" fields:", list(s["properties"]))
PY
```

**Очаквано:**
- `1.0.0` — задължителни `firstName`, `lastName`, `sku`, `quantity`.
- `1.1.0` — същите задължителни полета + **незадължително** `deliveryInstructions`. Старият клиент продължава да изпраща същия payload.
- `2.0.0` — **задължително** `fullName` вместо `firstName` и `lastName`; нов URI `/v2/placeorder`.

### Защо промяната 1.0 → 1.1 е backward-compatible?

Старият JSON payload не съдържа `deliveryInstructions`. Новият schema не го изисква, затова старият payload остава валиден. Но **в реален проект** съвместимостта изисква и семантични, поведенчески и integration tests: съвместимите типове не гарантират съвместимо бизнес поведение.

### Защо 1.1 → 2.0 е breaking?

Старият consumer изпраща `firstName` и `lastName`, а v2 API изисква `fullName`. Ако същият endpoint бъде променен in-place, старият клиент ще получи грешка. Поддържането на **две URI версии** дава време за миграция.

## 4. Изпълни статичен compatibility check

```bash
python3 tools/contract_diff.py \
  contracts/orderplacement-1.0.0.openapi.json \
  contracts/orderplacement-1.1.0.openapi.json

if python3 tools/contract_diff.py \
  contracts/orderplacement-1.1.0.openapi.json \
  contracts/orderplacement-2.0.0.openapi.json; then
  echo 'FAIL: breaking change was not detected'
  exit 1
else
  RESULT=$?
  test "$RESULT" -eq 2 && echo 'PASS: breaking change detected'
fi
```

**Очаквано:** първата команда печата `COMPATIBLE` и `deliveryInstructions`. Втората открива премахнат `/v1` path, изчезнали `firstName/lastName` и ново задължително `fullName`, връща exit code **2**, след което получаваш `PASS`.

**Ограничение:** `contract_diff.py` е **образователен статичен checker**, не пълна OpenAPI semantic validator/governance система. Промяна на numeric ranges, response schemas, security requirements или неочевидно поведение изисква други правила. В enterprise използвай policy-based registry, CI и consumer-driven contract tests.

## 5. Кои са участниците?

- **API provider:** поддържа версията, roadmap, документация, portal, application plans и срокове.
- **Backend developer:** поддържа паралелните API contract модели, JSON validation, storage/data migrations и backward compatibility.
- **API consumer:** променя request payload и URL, провежда регресионни тестове, следи deprecation и измерва миграцията.

Това е тройката роли от оригиналния Red Hat сценарий. Наличието на `v2` само в Swagger/Registry не означава, че клиентите автоматично ще преминат към нея.

## 6. Troubleshooting и cleanup

Ако има `JSONDecodeError`, провери файл с `python3 -m json.tool`. При `Expected OrderRequest` използвай файловете от `contracts/` без да преименуваш схемата. Ако вторият check върне **0**, той не е открил breaking change — провери дали действително сравняваш `1.1.0 → 2.0.0`.

**Cleanup:** Нищо не е създадено или модифицирано. Няма Kubernetes обекти, процеси или временни файлове.

**Самопроверка:** Защо може да имаме две OpenAPI `info.version` стойности за един и същи `/v1` URI? Защо removal на field не е равнозначно на добавяне на optional field? Кога е разумно да създадеш отделен 3scale Product за `v2`?
