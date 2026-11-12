# Lab 14-B — PostgreSQL WAL → Debezium → Kafka (истински CDC)

**Цел:** да активираш *реална* PostgreSQL logical replication и да наблюдаваш началния snapshot и CDC events в Kafka. **Няма polling на таблиците и няма simulated Kafka publisher.**

**Основен източник:** [Red Hat CDC architecture](https://www.solutionpatterns.io/solution-pattern-modernization-cdc/solution-pattern-modernization-cdc/02-architecture.html); [Debezium PostgreSQL Connector 3.3](https://debezium.io/documentation/reference/3.3/connectors/postgresql.html).

## 1. Предпоставки

- Docker Engine + Docker Compose v2, Bash, Python >= 3.10, curl, Git.
- Достъп за pull на `postgres:17.6`, `apache/kafka:4.1.2`, `quay.io/debezium/connect:3.3`, `docker.elastic.co/elasticsearch/elasticsearch:8.17.10` и Microsoft .NET 10 images, NuGet.
- Поне 10–12 GiB свободна RAM (ориентир), достатъчно дисково място за контейнерите/volumes.
- Свободни localhost портове `5084/5085/5441/5442/9092/8083/9200`. Никой от тях не трябва да е зает от чужд процес.
- Работна директория = **корен на Module 14**, с [compose.yaml](../compose.yaml), [legacy.sql](../sql/legacy.sql), [register_connector.py](../tools/register_connector.py).

Няма нужда да си изпълнил Lab 14-A, нито да инсталираш локален .NET SDK: build става във Docker. Няма OpenShift или cluster-admin.

## 2. Стартирай компонентите

```bash
docker compose version
python3 tools/init_env.py
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

**Очаквано:** services `legacy-db`, `cashback-db`, `kafka`, `connect`, `search`, `legacy` и `modern` са стартирани. Не бъркай `running` с `ready`; провери dependencies:

```bash
docker compose exec -T legacy-db pg_isready -U retail -d retail
docker compose exec -T cashback-db pg_isready -U cashback -d cashback
curl -fsS http://127.0.0.1:8083/connectors
curl -fsS http://127.0.0.1:9200/_cluster/health
curl -fsS http://127.0.0.1:5084/healthz
curl -fsS http://127.0.0.1:5085/healthz
```

При първо стартиране изчакай и повтори, докато всички станат Ready. **Не** обявявай HTTP 200 от `/healthz` за доказателство за пълен CDC поток — следващите стъпки проверяват същинската репликация.

## 3. Регистрирай Debezium PostgreSQL connector

```bash
set -a
. .env
set +a
python3 tools/register_connector.py
```

**Очаквано:** `Debezium connector registered` (или съществуващият се запазва) и `PASS actual Debezium connector + task RUNNING`. Python скриптът използва собствената ти локална random DB password, **не я печата**, и регистрира connector през Kafka Connect REST API на localhost:8083. Конфигурацията включва:
- `plugin.name=pgoutput` и `snapshot.mode=initial`;
- `topic.prefix=retailcdc`;
- `table.include.list=public.customer,public.product,public.sale,public.line_item`;
- `slot.name=m14_retail_slot` и `publication.name=m14_retail_pub`.

**Тези names не са secrets.** Самата DB password не трябва да е hardcoded в repository, shell history, screenshots или публични CI logs.

## 4. Проверка на истинския WAL slot

```bash
docker compose exec -T legacy-db psql -U retail -d retail -c \
  "SHOW wal_level"
docker compose exec -T legacy-db psql -U retail -d retail -c \
  "SELECT slot_name, plugin, active, restart_lsn FROM pg_replication_slots"
docker compose exec -T legacy-db psql -U retail -d retail -c \
  "SELECT pubname FROM pg_publication"
python3 tools/check_infra.py
```

**Очаквано:** `wal_level=logical`; slot `m14_retail_slot` с plugin `pgoutput`; publication `m14_retail_pub`, четири реални Kafka topics:
`retailcdc.public.customer`, `retailcdc.public.product`, `retailcdc.public.sale`, `retailcdc.public.line_item`.

**Защо следим slot?** При спряна репликация WAL може да се натрупва. В production следи `pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)`, connector task state/lag, disk pressure и retention policy. Никога не изтривай чужд replication slot без решение на DBA.

## 5. Виж raw Kafka CDC event

```bash
docker compose exec -T kafka \
  /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:19092 \
  --topic retailcdc.public.product \
  --from-beginning --max-messages 1 --timeout-ms 15000
```

**Очаквано:** Debezium JSON envelope с `before`, `after`, `op`, `source`, `ts_ms`. Началният snapshot съдържа вече съществуващите `Red Fern` и `Blue Pot`. При `op=r` се вижда ред от snapshot; `c/u/d` са изменения след него. **DELETE** може да публикува и Kafka `tombstone` (message value null) за log compaction; consumer трябва да разпознава двата типа.

**Важен нюанс:** няма глобална подредба между `sale` и `line_item` topics. Kafka гарантира ред в конкретна partition, **не между всички topics**. Cashback не трябва да допуска частично агрегирана покупка.

## 6. Проверка на snapshot към новия search index

```bash
curl -fsS 'http://127.0.0.1:5085/search?q=fern'
```

**Очаквано:** JSON с `productId=101`, `name=Red Fern`. Индексът се запълва **асинхронно**; ако заявката е празна непосредствено след регистрацията, повтори след няколко секунди или изпълни `python3 tools/verify.py` за bounded polling.

## 7. Troubleshooting

| Симптом | Проверка | Корекция |
|---|---|---|
| Kafka Connect REST 503/refused | `docker compose logs --tail=100 connect` | Изчакай Connect startup, провери Kafka/hostname |
| Connector FAILED | `curl http://127.0.0.1:8083/connectors/m14-retail-postgres/status` | Проверка DB credentials, logical WAL, slot, permissions |
| `wal_level != logical` | `SHOW wal_level` | Използвай само собствената Docker Compose база; не променяй production DB |
| Empty topics | `docker compose logs connect` | Snapshot task RUNNING, таблиците са в publication |
| CDC schema parsing error | `docker compose logs modern` | Провери Debezium connector version и before/after envelope |
| Kafka listener error | `docker compose logs kafka` | Провери INTERNAL listener 19092, EXTERNAL 9092 |
| Search empty | `curl localhost:9200/_cluster/health` | Индекс/producer lag, 1s ES refresh |
| Docker disk/memory | `docker stats`, `docker system df` | Освободи само свои ресурси; не прави глобален prune |

## 8. Cleanup

Ако продължаваш към 14-C/14-D, **не изпълнявай cleanup сега**, защото следващите стъпки използват същия lab stack. За спиране без загуба на данни:

```bash
docker compose down
unset PG_PASSWORD CASHBACK_PASSWORD
```

За **изрично изтриване** на учебните volumes (ще изтрие Postgres, Kafka state в контейнери и Elasticsearch index):

```bash
docker compose down -v
```

Не изтривай реален namespace, Kafka broker, Debezium connector или replication slot на чужда система. **Приемане:** истински RUNNING Debezium connector, активен pgoutput replication slot, 4 Kafka topics, snapshot product видим в новия search index.
