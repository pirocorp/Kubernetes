# Lab 15-C — Elasticsearch Product Search чрез INSERT/UPDATE/DELETE CDC

**Цел:** добави full-text търсене към **непроменен legacy каталог**. Направи SQL-backed продуктова операция чрез стария API и докажи, че новият Elasticsearch индекс се синхронизира **само** чрез Debezium → Kafka → C# projection. Оригинал: [Red Hat — CDC Search Context](https://www.solutionpatterns.io/solution-pattern-modernization-cdc/solution-pattern-modernization-cdc/02-architecture.html).

## 1. Изисквания и старт от чист checkout

Docker + Compose v2, Python 3.10+, Bash, интернет за образите и NuGet. Свободни портове 5084, 5085, 5441/5442, 8083, 9092, 9200 и достатъчна RAM (~10–12 GiB свободна). Работна директория: корен на Module 15. Не е нужно да си изпълнил 15-B: следният блок е **пълна самостоятелна подготовка**:

```bash
python3 tools/init_env.py
docker compose up -d --build
set -a
. .env
set +a
python3 tools/register_connector.py
python3 tools/check_infra.py
```

**Очаквано:** `kafka-init` е завършил успешно и Connect + Debezium task RUNNING, logical slot, четири CDC topics. Topics се създават преди C# consumer да започне subscription. Ако Kafka Connect още стартира, регистрационният скрипт чака до 2 минути; при timeout чети Connect logs, вместо да създаваш втори connector със същата slot.

## 2. Провери първоначалния snapshot

```bash
curl -fsS http://127.0.0.1:5084/legacy/products
curl -fsS 'http://127.0.0.1:5085/search?q=fern'
```

**Очаквано:** legacy DB вече има `Red Fern` (productId 101) и `Blue Pot` (102); след обработка на snapshot поискай повторно search и се увери, че намира 101. Това **не** е директна заявка на modern API към legacy SQL: modern API прави Elasticsearch `/_search`.

## 3. CREATE: нов продукт в старата система

```bash
curl -sS -i -H 'Content-Type: application/json' \
  -d '{"productId":7777,"name":"Purple Orchid","description":"Rare indoor orchid","priceCents":2500}' \
  http://127.0.0.1:5084/legacy/products
curl -fsS 'http://127.0.0.1:5085/search?q=orchid'
```

**Очаквано:** legacy API връща HTTP 201. В modern search след евентуално забавяне до няколко секунди се вижда productId 7777, name `Purple Orchid`, priceCents 2500.

**Защо е eventually consistent?** PostgreSQL COMMIT, Debezium, Kafka consumer, Elasticsearch indexing и index refresh са отделни фази. В production **никога** не обещавай, че search веднага вижда всяка SQL промяна.

## 4. UPDATE: цена и име

```bash
curl -sS -i -X PUT -H 'Content-Type: application/json' \
  -d '{"productId":7777,"name":"Purple Orchid Deluxe","description":"Rare indoor orchid","priceCents":3100}' \
  http://127.0.0.1:5084/legacy/products/7777
curl -fsS 'http://127.0.0.1:5085/search?q=orchid'
```

**Очаквано:** HTTP 200, после новият Elasticsearch document е със същия стабилен ID 7777, но `priceCents=3100`, `name=Purple Orchid Deluxe`. C# projector използва `PUT /retail-products/_doc/{productId}`, а не нов случаен document ID — повторен event не създава дубликат.

## 5. DELETE: последователно премахване от индекса

```bash
curl -sS -i -X DELETE http://127.0.0.1:5084/legacy/products/7777
curl -fsS 'http://127.0.0.1:5085/search?q=orchid'
```

**Очаквано:** HTTP 204; след CDC/Elasticsearch refresh продукт 7777 **вече не се намира**. Debezium `op=d` и последващ null tombstone имат различни роли. Нашият C# consumer изтрива документа при `op=d`, а tombstone commit-ва без повторно изтриване. Ако нямаше това разграничение, старият search може да пази „призрачен“ продукт.

Провери и самия индекс, не само REST facade:

```bash
curl -fsS 'http://127.0.0.1:9200/retail-products/_search?q=name:fern'
```

**Очаквано:** остава seed продукт `Red Fern`. Обърни внимание: Elasticsearch порт 9200 е достъпен **само от localhost** в това упражнение и security е изключена за demo. Не го излагай публично.

## 6. Автоматичен тест от чиста среда

```bash
# Първо спри свои стари lab containers, ако желаеш абсолютно чисти данни:
# docker compose down -v  # ВНИМАНИЕ: изтрива учебните volumes
bash scripts/verify-cdc.sh
```

**Очаквано:** тестът използва портове, проверява snapshot, извършва INSERT/UPDATE/DELETE и poll-ва резултатите. **Идемпотентността на setup:** първоначалният seed остава същият; ако вече си създал продукт 7777 ръчно, премахни го от собствения legacy API преди теста. Не изтривай чужда база, за да стартираш тест.

## 7. Troubleshooting

| Симптом | Диагноза | Действие |
|---|---|---|
| HTTP 201, но search празен | `docker compose logs modern connect` | Consumer lag, connector task, ES startup |
| 409 при INSERT | Продукт 7777 вече съществува | Използвай друг demo ID за ръчна проверка или изтрий **своя** 7777 |
| HTTP 404 при PUT | Продуктът липсва | Създай го преди update |
| В Elasticsearch е старата цена | Event lag / refresh interval | Изчакай, провери Kafka topic и consumer offsets |
| Документ не се трие | Debezium delete/tombstone или projector exception | Провери op=d и topic record |
| Elasticsearch 503 | `docker compose logs search` | Memory, disk, single-node startup |
| 401/403 в enterprise search | Този lab е без auth, production е отделно | Настрой сертификати/credentials, не изключвай security |

## 8. Cleanup

Ако продължаваш към cashback Lab 15-D, остави stack-а. Иначе:

```bash
docker compose down
unset PG_PASSWORD CASHBACK_PASSWORD
```

Това **запазва** собствените Postgres/Elasticsearch named volumes. `docker compose down -v` ги изтрива **само по изричен избор**.

**Приемане:** успяваш да докажеш INSERT→index, UPDATE→same document, DELETE→absence без legacy приложение да публикува Kafka или пише Elasticsearch.
