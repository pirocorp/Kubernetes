# Lab 15-E — OpenShift: CDC modern workloads, security, observability и recovery

**Цел:** да разположиш **двете C# роли** в разрешен OpenShift namespace и да ги свържеш с *вече подготвени* managed PostgreSQL, Debezium/Kafka Connect, Kafka и Elasticsearch услуги. Това следва топологията на [Red Hat CDC/OpenShift Pattern](https://www.solutionpatterns.io/solution-pattern-modernization-cdc/solution-pattern-modernization-cdc/02-architecture.html), но **не** изпълнява стария Ansible installer от оригиналния demo.

**Важно разграничение:** самостоятелният **реален end-to-end CDC** lab е 15-B–D чрез Docker Compose, без cluster permissions. OpenShift вариантът е **условен live-cluster lab**: не може да измислим Kafka/Postgres DNS, сертификати, operator licenses или RBAC. Тук има конкретен code/build/deployment път, който се изпълнява **само след изпълнените явни prerequisites**.

**Platform profile P is mandatory:** follow [15-E managed CDC prerequisites](../../docs/OPENSHIFT-LAB-PROFILES.md#module-15-e--external-managed-cdc), then run `bash scripts/check-openshift-profile.sh m15-cdc` from repository root. The script checks API/RBAC; a platform owner must separately verify the actual Debezium connector, two PostgreSQL databases, Kafka topics and Elasticsearch. No automatic Operator or production-slot changes.

## 1. Необходими предпоставки

- Developer Sandbox/разрешен OpenShift Project с `oc` CLI login и права за namespaced `BuildConfig`, `Build`, `ImageStream`, `Deployment`, `ServiceAccount`, `Service` и `Secret`.
- Работещи managed **legacy PostgreSQL** с `wal_level=logical`, publication, replication slot и таблиците от [legacy.sql](../sql/legacy.sql). В production **не променяй legacy schema**, само учебна среда.
- **Вече конфигуриран Debezium Source connector** и Kafka brokers, с topics: `retailcdc.public.customer`, `retailcdc.public.product`, `retailcdc.public.sale`, `retailcdc.public.line_item`. Приложението **не инсталира Kafka/Operator**.
- **Cashback PostgreSQL** със schema от [cashback.sql](../sql/cashback.sql) и Elasticsearch HTTP endpoint с разрешен достъп.
- **Профил на съвместимост:** учебният C# Kafka client използва PLAINTEXT bootstrap и учебният Elasticsearch client — HTTP без API credentials. При стандартен enterprise Kafka SASL/TLS и Elasticsearch HTTPS/auth **трябва да се разработят и конфигурират подходящи security adapters**, преди да използваш този sample. Не изключвай security на служебни ресурси само за тест.
- Container build nodes достигат Microsoft .NET 10 images и NuGet. Достатъчна image/Pod quota.
- Bash, Python 3.10+, `oc`. Работна директория = Module 15 root, [Dockerfile](../Dockerfile) и [workloads.yaml](../openshift/workloads.yaml) са включени.

**Ако липсват managed dependencies, това не е разрешение за инсталиране на cluster-scoped Operators или използване на production PostgreSQL slot.** Направи 15-B–D на локалната Docker Compose среда — тя действително включва всички нужни компоненти.

## 2. Preflight: провери клъстера, Project и RBAC

```bash
oc whoami
oc project
oc version
oc get resourcequota
oc auth can-i create deployments.apps
oc auth can-i create serviceaccounts
oc auth can-i create services
oc auth can-i create secrets
oc auth can-i create buildconfigs.build.openshift.io
oc auth can-i create builds.build.openshift.io
oc auth can-i create imagestreams.image.openshift.io
oc get deploy,svc,sa,secret,bc,is -l training=module15
test -s Dockerfile
test -s openshift/workloads.yaml
```

**Очаквано:** всички `can-i` са `yes`, избран е правилният личен namespace, имената `m15-*` са свободни и quota позволява два C# Pod-а и един build. Не обновявай или изтривай чужд `m15-*` resource.

## 3. Build и ImageStream

```bash
oc new-build --name=m15-retail-image --binary --strategy=docker
oc start-build m15-retail-image --from-dir=. --follow --wait
oc get builds -l buildconfig=m15-retail-image
M15_IMAGE="$(oc get istag m15-retail-image:latest -o jsonpath='{.image.dockerImageReference}')"
test -n "$M15_IMAGE" || { echo 'No container image'; false; }
printf 'Built image reference: %s\n' "$M15_IMAGE"
```

**Очаквано:** Build `Complete`, ImageStream с таг `latest`. При `Forbidden` — отказ заради RBAC; при build fail — `oc logs build/ИМЕ`, Pull access и NuGet network. **Не** заобикаляй SCC с root/privileged containers.

## 4. Конфигурирай две отделни тайни, без shared database credentials

C# code работи с различни connection strings:
- **Legacy App:** `LEGACY_CONNECTION` към **само** legacy PostgreSQL.
- **Modern App:** `CASHBACK_CONNECTION` към **само** собствената cashback DB, `KAFKA_BOOTSTRAP` към broker, `SEARCH_URL` към Elasticsearch.

Вътрешните DNS/credentials трябва да бъдат предоставени от platform team; **не използвай предположен hostname или публичен DB**. Създай *собствени временни env файлове* с `0600` чрез локален editor в `.runtime/` (Git-ignored), без да ги commit-ваш:

```bash
umask 077
mkdir -p .runtime
printf 'LEGACY_CONNECTION=Host=REPLACE;Database=retail;Username=REPLACE;Password=REPLACE\n' \
  > .runtime/openshift-legacy.env
printf 'CASHBACK_CONNECTION=Host=REPLACE;Database=cashback;Username=REPLACE;Password=REPLACE\nKAFKA_BOOTSTRAP=REPLACE_HOST:9092\nSEARCH_URL=http://REPLACE_HOST:9200\n' \
  > .runtime/openshift-modern.env
chmod 600 .runtime/openshift-legacy.env .runtime/openshift-modern.env
```

**Преди следващата команда** замени *всички* `REPLACE` стойности с разрешени актуални данни чрез editor; полетата са инструкции, **не са работещи credentials**. Съхранявай правилните TLS настройки/secret management според реалния environment. Не изпращай тайните в chat/logове.

```bash
if grep -q 'REPLACE' .runtime/openshift-legacy.env; then
  echo 'Replace the placeholder values in the legacy secret file' >&2
else
  oc create secret generic m15-legacy-conn --from-env-file=.runtime/openshift-legacy.env
fi
if grep -q 'REPLACE' .runtime/openshift-modern.env; then
  echo 'Replace the placeholder values in the modern secret file' >&2
else
  oc create secret generic m15-modern-conn --from-env-file=.runtime/openshift-modern.env
fi
oc get secret m15-legacy-conn m15-modern-conn
```

**Очаквано:** само собствените Secret обекти са създадени; legacy Pod **не получава cashback DB credentials**, modern Pod **не получава legacy DB credentials**. Това дава реална least-privilege граница на configuration ниво, а в production проверявай и DB роли/network policies.

## 5. Namespace-scoped Deployments и ClusterIP Services

```bash
sed "s|IMAGE_PLACEHOLDER|$M15_IMAGE|g" openshift/workloads.yaml \
  | oc apply --dry-run=client -f -
sed "s|IMAGE_PLACEHOLDER|$M15_IMAGE|g" openshift/workloads.yaml \
  | oc apply -f -
oc rollout status deployment/m15-legacy --timeout=300s
oc rollout status deployment/m15-modern --timeout=300s
oc get deploy,svc,sa -l training=module15
oc get endpointslice -l kubernetes.io/service-name=m15-legacy
oc get endpointslice -l kubernetes.io/service-name=m15-modern
```

**Очаквано:** 2 Ready Deployments с default restricted SCC, non-root containers, 2 ServiceAccounts и 2 ClusterIP Services. **Няма публичен Route** за четене на лични wallet данни и за legacy write endpoints — те се отварят **само чрез временни port-forwards**. `/healthz` е процесен liveness endpoint, **не** доказва CDC или инфраструктурна готовност.

## 6. Тествай HTTP през port-forward, без да експозваш системата

В терминал A:

```bash
oc port-forward service/m15-legacy 5084:8080
```

В терминал B:

```bash
oc port-forward service/m15-modern 5085:8080
```

В терминал C (същия source checkout):

```bash
curl -fsS http://127.0.0.1:5084/healthz
curl -fsS http://127.0.0.1:5085/healthz
curl -fsS http://127.0.0.1:5084/legacy/products
curl -fsS 'http://127.0.0.1:5085/search?q=fern'
curl -fsS http://127.0.0.1:5085/wallets/1
```

**Очаквано:** HTTP 200, seed продукти, търсене по индекс и проектиран customer wallet **само ако** платформените DBs и Kafka connector имат същите synthetic source records и структури. При различни реални данни измени queries според реално разрешените fixtures. **Не** изпълнявай destructive create/delete върху неучебни records.

Пълният `tools/verify.py` изпраща **write операции** и променя customer tier; ползвай го **само** върху изолирания собствен 15-B–D demo dataset, не върху споделена или production база.

## 7. Observability и recovery runbook

Следи независимо:
- **Postgres:** WAL retention, `pg_replication_slots.restart_lsn`, availability, publication и privileges.
- **Debezium/Kafka Connect:** connector/task state, snapshot status, source offsets/lag, connector errors.
- **Kafka:** topic health, consumer-group lag, partition ordering и retention.
- **Modern consumer:** exception/seek/retry, poison events, schema changes, idempotency, offset commit.
- **Search:** документен брой, refresh/lag, индекс mappings и възстановяване от replay/snapshot.
- **Wallet DB:** count на sale_stage/item_stage, expenses totals, customer rates, reconciliation/duplicates.

**Scenario A — Kafka/Connect down:** legacy continues SQL commits, но WAL се задържа; оценявай free disk + restart_lsn. **Не** изтривай slot за „бързо решение“, ако зависимата система не е ресинхронизирана.

**Scenario B — Modern DB down:** consumer не commit-ва успешен offset; след възстановяване същите събития могат да се изпълнят отново. Idempotent state projection предотвратява двойно начисляване; нужен е production DLQ/bounded retry.

**Scenario C — Elasticsearch загубен:** възстанови индекс чрез controlled re-index snapshot/replay с нов consumer group/offset plan; не стартирай две конкуриращи се writer версии без reconciliation.

**Scenario D — schema change:** `ALTER TABLE` може да промени CDC payload; следи compatibility, deprecations, defaults, type conversions и migrations. Не разчитай, че C# consumer автоматично ще разбере новото поле/тип.

## 8. Troubleshooting

| Симптом | Команда/диагноза | Решение |
|---|---|---|
| ImagePullBackOff | `oc describe pod -l app=m15-modern` | Registry permissions / ImageStream reference |
| CrashLoopBackOff | `oc logs deploy/m15-modern --previous` | Secret env, Kafka / ES / DB connectivity |
| Deployment Ready, но search празен | Kafka Connect task и ES index health | Не бъркай liveness с full readiness |
| Wallet 404 | `oc logs deploy/m15-modern` | Customer snapshot/DB data |
| `Forbidden` за builds/secrets | `oc auth can-i ...` | Не е разрешен live lab — използвай Docker Compose |
| Kafka SASL/TLS отказ | Broker security config | Нужен C# supported security config, не plaintext workaround |
| WAL расте | DBA queries за slots и LSN | Ограничи retention и алармирай |
| Port-forward не тръгва | Порт 5084/5085 е зает | Спри собствените стари forwards |
| TLS/SSL грешка | Certificate chain/trust | Не използвай `curl -k` или disable security за production |

## 9. Cleanup — само собствени учебни ресурси

Спри port-forward терминалите (Ctrl+C). В правилния Project:

```bash
oc delete deployment/m15-legacy deployment/m15-modern --ignore-not-found
oc delete service/m15-legacy service/m15-modern --ignore-not-found
oc delete serviceaccount/m15-legacy-sa serviceaccount/m15-modern-sa --ignore-not-found
oc delete secret/m15-legacy-conn secret/m15-modern-conn --ignore-not-found
oc delete buildconfig/m15-retail-image imagestream/m15-retail-image --ignore-not-found
oc delete builds -l buildconfig=m15-retail-image --ignore-not-found
oc get deploy,svc,sa,secret,bc,is -l training=module15
unset M15_IMAGE
```

Локалните `.runtime/openshift-*.env` файлове остават за преглед, **изтрий само твоите копия**, когато приключиш и няма нужда от тях.

**Не** изтривай чужди Kafka topics, connector, replication slots, managed DBs, Elasticsearch индекси, Operators или Project. Този lab **не ги е създавал**.

**Приемане:** можеш да deploy-неш две C# роли с отделни Secrets, да обясниш защо не се експозват публично и да диагностицираш CDC pipeline-а по всички слоеве. **Същинската end-to-end функционална валидация на реален CDC pipeline** е автоматизирана в Docker Labs 15-B–D; тук се изисква изрично налична и разрешена OpenShift инфраструктура.
