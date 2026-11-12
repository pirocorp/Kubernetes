# Lab 11-B — API Registry, governance и versioning

**Цел:** versioned API contract, immutable publication и откриване на breaking changes. Оригинал: [Red Hat API-First Solution Pattern](https://www.solutionpatterns.io/solution-pattern-api-first/api-first/index.html).

## Предпоставки

Python 3.10+, Bash, Git и **съществуващият** `contract/products-v1.openapi.json`. Отвори корена на Module 11. Не се изисква външен Apicurio или OpenShift.

## 1. Публикувай версия 1.0.0 в локалния учебен registry

```bash
python3 tools/registry.py publish contract/products-v1.openapi.json
python3 tools/registry.py list
find .registry/products -type f -maxdepth 3 -print
```

**Очаквано:** `.registry/products/1.0.0/openapi.json` и `sha256.txt` с SHA256 hash. Второ публикуване на **същия** договор е idempotent, но промяна на съдържанието под същата версия се отказва. Това демонстрира **artifact identity**, не е реален Apicurio Registry deployment.

## 2. Създай обратно съвместима версия

Създай временен договор `/tmp/m11-v2-compatible.openapi.json`: новата версия добавя **незадължително** поле `description` към `Product`, без да премахва операции.

```bash
python3 - <<'PY'
import json
doc = json.load(open('contract/products-v1.openapi.json'))
doc['info']['version'] = '1.1.0'
doc['components']['schemas']['Product']['properties']['description'] = {'type': 'string'}
with open('/tmp/m11-v2-compatible.openapi.json', 'w') as f:
    json.dump(doc, f, indent=2)
PY
python3 tools/registry.py check contract/products-v1.openapi.json /tmp/m11-v2-compatible.openapi.json
python3 tools/registry.py publish /tmp/m11-v2-compatible.openapi.json
python3 tools/registry.py list
```

**Очаквано:** checker не намира breaking changes и registry има версии `1.0.0` и `1.1.0`. **Важно:** това е ограничен образователен checker, а не пълна семантична OpenAPI compatibility проверка.

## 3. Направи умишлен breaking change

```bash
python3 - <<'PY'
import json
doc = json.load(open('contract/products-v1.openapi.json'))
doc['info']['version'] = '2.0.0'
del doc['paths']['/v1/products/{id}']
with open('/tmp/m11-v2-breaking.openapi.json', 'w') as f:
    json.dump(doc, f, indent=2)
PY
if python3 tools/registry.py check contract/products-v1.openapi.json /tmp/m11-v2-breaking.openapi.json; then
  echo 'FAIL: checker accepted removed GET endpoint'
else
  echo 'PASS: breaking change rejected'
fi
```

**Очаквано:** `BREAKING: Removed path /v1/products/{id}`, после `PASS`.

## Корпоративен вариант — Apicurio Registry

Нашият локален `registry.py` демонстрира принципа, но **не е Apicurio**. В подходяща среда използвай [Apicurio Registry 3.x](https://www.apicur.io/registry/docs/apicurio-registry/3.0.x/index.html) за централизирани API artifacts, версии и правила. Проверявай конкретната release, storage backend, authentication и поддръжката на OPENAPI artifacts преди deployment. В споделен Developer Sandbox не инсталирай Registry Operator без право/квота.

Разликата: Git съхранява source; registry прави спецификацията **публикувана/откриваема за потребители**; compatibility policy предпазва тези потребители от неочаквано breaking изменение. За production се използват пълни OpenAPI semantic validators, approvals, CI и деплой политики.

## Troubleshooting

`Immutable version conflict` означава, че модифицираш вече публикувана версия; създай **нова** `info.version`. Ако `json.decoder.JSONDecodeError`, провери `python3 -m json.tool`. Ако compatibility проверката не засече по-сложна семантична грешка, това е **ограничение** на нашия checker — не твърди пълна governance защита.

## Cleanup

```bash
rm -f /tmp/m11-v2-compatible.openapi.json /tmp/m11-v2-breaking.openapi.json
# Само от корена на Module 11, след проверка на pwd:
test -f contract/products-v1.openapi.json && test -d .registry && rm -r -- .registry
```

**Критерий:** успяваш да публикуваш 1.0.0/1.1.0, а изтриването на операция се разпознава като breaking change.
