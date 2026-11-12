# Lab 10-A — Design-first OpenAPI contract и mock

**Цел:** потребителят и разработчикът работят по един API договор, преди да има истински backend. Оригинален източник: [Red Hat API-First Solution Pattern](https://www.solutionpatterns.io/solution-pattern-api-first/api-first/index.html).

## Предпоставки

- Python **3.10+**, Git, Bash и `curl`. **Не** са нужни OpenShift, Docker, NuGet или платени продукти.
- Отвори директорията на Module 10 (виж [началната страница](../README.md)). Използваме `contract/products-v1.openapi.json` — **валиден OpenAPI 3.0.3 документ**; JSON е равностоен на YAML като формат за OpenAPI.
- Нужни са свободни локални портове **8082** (mock), по-късно 8080 (реално API) и 8081 (gateway). Командите са за Bash.

## 1. Прочети договора

```bash
python3 -m json.tool contract/products-v1.openapi.json >/dev/null
python3 - <<'PY'
import json
doc = json.load(open('contract/products-v1.openapi.json', encoding='utf-8'))
print(doc['info']['title'], doc['info']['version'])
for path, methods in doc['paths'].items():
    for method, operation in methods.items():
        print(method.upper(), path, operation['operationId'])
PY
```

**Очаквано:** версия `1.0.0`, `GET /healthz`, `GET/POST /v1/products`, `GET /v1/products/{id}`. В `components.schemas` са `Product`, `ProductList`, `NewProduct` и `ApiError`, включително `required` и `currency: EUR`.

**Основни понятия:** `paths` описва HTTP операции, `requestBody` — тялото на заявка, `responses` — статус/форма/пример, `securitySchemes` — как клиентът се идентифицира, `$ref` — препратка към обща схема. `example` са **примерни**, не обещание за постоянни данни. Договорът е **source of truth**; кодът трябва да се съобрази с него.

## 2. Стартирай mock, който чете примерите от договора

Генерирай временен ключ без да го commit-ваш или пишеш в shell history:

```bash
export API_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
test "${#API_KEY}" -ge 16
python3 tools/mock_server.py > /tmp/m10-mock.log 2>&1 &
MOCK_PID=$!
```

**Продължи в същия Bash терминал**, за да използваш същия `API_KEY`. Mock процесът остава във фон. Проверка при отказ: `cat /tmp/m10-mock.log`. Ако порт 8082 вече е зает, спри собствения предишен mock, вместо да стартираш второ копие.

```bash
curl -fsS http://127.0.0.1:8082/healthz
curl -fsS -H "X-Api-Key: $API_KEY" http://127.0.0.1:8082/v1/products
curl -fsS -H "X-Api-Key: $API_KEY" http://127.0.0.1:8082/v1/products/p-100
python3 tools/contract_check.py --base-url http://127.0.0.1:8082
```

**Очаквано:** `ok`, списък от Keyboard и Mouse, детайли за `p-100`, след това девет успешни contract smoke проверки (health, unauthorized, list, found, 404, POST 201 и три отказани POST 400, включително непознато поле). Mock `POST` връща примерен обект, **не** запазва нови продукти.

## Troubleshooting

| Симптом | Проверка | Корекция |
|---|---|---|
| `Address already in use` | `ss -ltn | grep 8082` | Спри предишния mock; не убивай произволни процеси |
| `Invalid API key` | `test "${#API_KEY}" -ge 16` | Използвай ключа от процеса, стартирал mock |
| `Connection refused` | Наличен ли е процесът и на 127.0.0.1:8082? | Стартирай `python3 tools/mock_server.py` |
| `ModuleNotFoundError` | Този lab не използва Python packages | Провери дали е стартиран **нашият** `tools/mock_server.py` |

## Cleanup

С Ctrl+C спри foreground mock или, само ако си стартирал собствен процес във фон: `if test -n "${MOCK_PID:-}"; then kill "$MOCK_PID"; unset MOCK_PID; fi`. Няма създадени кластерни ресурси. След всички labs: `unset API_KEY`.

**Самопроверка:** Защо mock позволява UI екипът да работи, преди backend кодът да е написан? Защо OpenAPI `examples` не са доказателство за DB persistence?
