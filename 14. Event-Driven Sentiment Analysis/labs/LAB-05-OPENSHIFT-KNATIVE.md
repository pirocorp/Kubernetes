# Lab 14-E — OpenShift: KafkaSource, Knative Broker, Triggers и CloudEvents consumers

**Цел:** да реализираш **истински Knative Eventing fan-out** за Globex с ASP.NET Core/C# и Kafka. В този lab KafkaSource консумира `globex.reviews` и изпраща CloudEvents към Knative Broker; два Triggers извикват отделни moderation и sentiment HTTP endpoints. Това е конкретната архитектура от [Red Hat Event-Driven Intelligent Applications](https://www.solutionpatterns.io/solution-pattern-sentiment-analysis/solution-pattern-sentiment-analysis/02-architecture.html).

**Не изпълнявай историческия Red Hat Ansible installer автоматично:** оригиналният walkthrough е тестван с **OpenShift 4.13, cluster-admin** и инсталира множество оператори/проекти. Не е безопасен универсален вариант за Developer Sandbox или служебна платформа.

## 1. Задължителни prerequisites

- Преминати Kubernetes Modules 00–08 и познаваш [Module 09 — OpenShift](../../09.%20OpenShift/README.md).
- Личен/разрешен OpenShift Project, работещ `oc` login и права в него за `BuildConfig`, `Build`, `ImageStream`, `Deployment`, `Service`, `Route`, `Secret`, `KafkaSource`, `Broker` и `Trigger`.
- Platform team **вече е инсталирал** поддържана OpenShift Serverless/Knative Eventing конфигурация, **включително KafkaSource controller** и работещ default Broker implementation.
- В същия cluster или разрешено достижим адрес има Kafka cluster (например поддържан Red Hat AMQ Streams) с **четири предварително създадени topics**:
  `globex.reviews`, `reviews.moderated`, `reviews.denied`, `reviews.sentiment`.
- За този lab broker endpoint е **вътрешен и без SASL/TLS**, защото учебният Kafka client не конфигурира enterprise SASL/SSL. Това е **изолирана учебна среда**, не production настройка. При Kafka изискващ mTLS/SASL, настоящият sample не е съвместим без допълнителен security adapter.
- OpenShift build nodes могат да изтеглят .NET 10 SDK/runtime images и NuGet packages. Има quota за поне **1 app Pod**, KafkaSource dispatch resources и Eventing components.
- Bash, Python 3.10+, `oc` и `curl`. **Локален .NET SDK не е необходим** — Docker strategy build компилира проекта.
- Всички файлове са включени: [Dockerfile](../Dockerfile), [OpenShift Deployment/Service/Route](../openshift/workload.yaml), [Broker/KafkaSource/Triggers](../openshift/knative-eventing.yaml) и [C# CloudEvent callbacks](../src/GlobexReviews/Program.cs).

**Ако липсва което и да е условие**, не заобикаляй SCC/RBAC, не инсталирай cluster-scoped оператори и не обявявай lab-а за изпълнен. Използвай локалния [Lab 14-C](./LAB-03-KAFKA-STORAGE-DASHBOARD.md) с истински Kafka и бази.

## 2. Preflight — преди промени в cluster

От **корена на Module 14**:

```bash
oc whoami
oc project
oc version
oc get resourcequota
oc api-resources | grep -E 'kafkasources|brokers|triggers'
oc auth can-i create deployments.apps
oc auth can-i create services
oc auth can-i create routes.route.openshift.io
oc auth can-i create secrets
oc auth can-i create buildconfigs.build.openshift.io
oc auth can-i create builds.build.openshift.io
oc auth can-i create imagestreams.image.openshift.io
oc auth can-i create kafkasources.sources.knative.dev
oc auth can-i create brokers.eventing.knative.dev
oc auth can-i create triggers.eventing.knative.dev
oc get deploy/m14-globex-reviews service/m14-globex-reviews route/m14-globex-reviews 2>/dev/null || true
oc get broker/m14-reviews-broker kafkasource/m14-globex-kafka-source 2>/dev/null || true
```

**Очаквано:** избраният Project е **твоят**, всички необходими CRDs са налични и всяко `can-i` е `yes`. Провери, че имената `m14-*` са свободни. Потвърди от cluster admin/AMQ Streams documentation **Kafka Bootstrap Service DNS**, topic existence и правила за достъп. Не гадай hostname и не използвай публичен анонимен Kafka broker.

## 3. Build контейнерен образ от реалния C# source

```bash
oc new-build --name=m14-globex-image --binary --strategy=docker
oc start-build m14-globex-image --from-dir=. --follow --wait
oc get builds -l buildconfig=m14-globex-image
M14_IMAGE="$(oc get istag m14-globex-image:latest -o jsonpath='{.image.dockerImageReference}')"
test -n "$M14_IMAGE" || { echo 'Build produced no image'; false; }
printf 'Image resolved: %s\n' "$M14_IMAGE"
```

**Очаквано:** Build `Complete`, ImageStream `m14-globex-image:latest`, image reference. При грешки: `oc get builds`, `oc describe bc m14-globex-image`, `oc logs build/ИМЕ`. **Никога** не давай privileged SCC за да поправиш failed build.

## 4. Личен ingestion key и Deployment

Полученият Kafka bootstrap адрес е **конкретно предоставен от платформата**, например `my-cluster-kafka-bootstrap.my-namespace.svc:9092`, но не приемай, че примерният адрес съществува. Въведи реалната стойност интерактивно:

```bash
read -r -p "Kafka bootstrap host:port for this cluster: " M14_BOOTSTRAP
test -n "$M14_BOOTSTRAP"
export INGEST_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
umask 077
M14_KEY_FILE="$(mktemp)"
printf 'INGEST_KEY=%s\n' "$INGEST_KEY" > "$M14_KEY_FILE"
oc create secret generic m14-review-secret --from-env-file="$M14_KEY_FILE"
rm -f -- "$M14_KEY_FILE"
unset M14_KEY_FILE
```

Тайната е в OpenShift Secret, не в Git. API изисква `X-Api-Key` за **всички /reviews GET и POST**. Knative callbacks `/events/*` не са публично изложени от Route.

Замени **само** двете placeholders в YAML pipeline:

```bash
sed -e "s|IMAGE_PLACEHOLDER|$M14_IMAGE|g" \
    -e "s|KAFKA_BOOTSTRAP_PLACEHOLDER|$M14_BOOTSTRAP|g" \
    openshift/workload.yaml | oc apply --dry-run=client -f -
sed -e "s|IMAGE_PLACEHOLDER|$M14_IMAGE|g" \
    -e "s|KAFKA_BOOTSTRAP_PLACEHOLDER|$M14_BOOTSTRAP|g" \
    openshift/workload.yaml | oc apply -f -
oc rollout status deployment/m14-globex-reviews --timeout=300s
oc get deploy/m14-globex-reviews svc/m14-globex-reviews route/m14-globex-reviews
oc get endpointslice -l kubernetes.io/service-name=m14-globex-reviews
```

**Очаквано:** Deployment `1/1 Ready`, ClusterIP Service на port 8080, edge TLS Route с path `/reviews`. `REVIEWS_MODE=knative` активира Kafka producer, **но не стартира собствените Kafka consumer groups**; съобщенията ще се обработват от Knative.

**Persistence boundary:** този минимален OpenShift deployment съхранява резултатите **само в паметта**, ако не е конфигуриран подходящ PostgreSQL/InfluxDB service. След рестарт те ще изчезнат. В production разположи одобрени managed storage services и конфигурирай `POSTGRES_CONNECTION` и `INFLUX_*` чрез Secrets, както в Lab 14-C. Не твърди, че самото Knative deployment вече има durable review database.

## 5. Broker + KafkaSource + два Triggers

```bash
sed "s|KAFKA_BOOTSTRAP_PLACEHOLDER|$M14_BOOTSTRAP|g" \
  openshift/knative-eventing.yaml | oc apply --dry-run=client -f -
sed "s|KAFKA_BOOTSTRAP_PLACEHOLDER|$M14_BOOTSTRAP|g" \
  openshift/knative-eventing.yaml | oc apply -f -
oc get broker/m14-reviews-broker
oc get kafkasource/m14-globex-kafka-source
oc get trigger/m14-moderation-trigger trigger/m14-sentiment-trigger
oc describe kafkasource m14-globex-kafka-source
```

**Очаквано:** `Broker`, `KafkaSource` и двата `Triggers` с `READY=True`, след като controllers са активирали всички ресурси. Ако `READY=False`, провери `oc describe` и events — не продължавай преди разрешаване.

**Точният event flow:**
1. C# producer публикува CloudEvent JSON в Kafka `globex.reviews`.
2. KafkaSource **със собствена Kafka consumer group** `m14-knative-source` чете topic-а.
3. KafkaSource доставя Knative Kafka CloudEvent до Broker `m14-reviews-broker`.
4. Двата Triggers fan-out-ват едно и също събитие към `/events/moderation` и `/events/sentiment` на вътрешния Service.
5. C# callbacks обработват и публикуват derived CloudEvents към `reviews.moderated`/`reviews.denied` и `reviews.sentiment`.

**Не обърквай:** `KafkaSource/Knative Broker` не е самият Kafka broker. Това са различни ресурси с различни роли и механизми за доставка. `Knative KafkaSource` може да обвие оригиналното Kafka payload в нов CloudEvent; C# parser поддържа nested JSON payload от този стандартен сценарий.

## 6. Реален HTTP тест

```bash
M14_HOST="$(oc get route m14-globex-reviews -o jsonpath='{.spec.host}')"
test -n "$M14_HOST"
python3 tools/generate_reviews.py --base-url "https://$M14_HOST" --count 3
```

**Очаквано:** три synthetic POST заявки към **публичния Route** се приемат с HTTP 202 и собствен `INGEST_KEY` (прочетен от environment, без отпечатване). Route е умишлено ограничен до `/reviews`; `/healthz`, `/metrics` и `/events` не са публично достъпни от него. Поради това пълният acceptance test се изпълнява **през временен port-forward**, а не през Route.

**Терминал 1** (остави да работи):

```bash
oc port-forward service/m14-globex-reviews 5508:8080
```

**Терминал 2** (същия локален checkout и `INGEST_KEY` от раздел 4):

```bash
python3 tools/verify.py --base-url http://127.0.0.1:5508 --timeout 90
curl -fsS http://127.0.0.1:5508/metrics/sentiment
curl -fsS http://127.0.0.1:5508/events
oc logs deployment/m14-globex-reviews --tail=60
oc get events --sort-by=.lastTimestamp
```

**Очаквано:** структурирани JSON резултати. Спри port-forward с Ctrl+C. Ако Route дава `503`, диагностицирай Service endpoints/Pod readiness и API logs. Ако POST дава `503 event_unavailable`, Kafka producer не успява да достигне/публикува в topic-а.

### Локална проверка на HTTP callback contract (без Knative Operator)

Ако имаш изпълнен [Lab 14-C](./LAB-03-KAFKA-STORAGE-DASHBOARD.md) и истинския Kafka Compose stack още работи, можеш предварително да провериш как ASP.NET Core обработва **nested KafkaSource CloudEvent** и директен structured CloudEvent. Проверката стартира **отделен процес на порт 5081**, за да не се сблъсква със стандартния Kafka API на порт 5080:

```bash
# Порт 5081 трябва да е свободен; Kafka Compose stack трябва да работи.
bash scripts/verify-knative-callbacks.sh
```

**Очаквано:** `PASS wrapped KafkaSource CloudEvent` и `PASS Knative-style CloudEvent HTTP callback contract`. Този тест използва истински Kafka/PostgreSQL/InfluxDB, но **имитира HTTP доставката**, не инсталира/валидира реален Knative Broker/Trigger. Изходни файлове: [verify_knative_callbacks.py](../tools/verify_knative_callbacks.py) и [verify-knative-callbacks.sh](../scripts/verify-knative-callbacks.sh). **Live Serverless** остава проверката от раздели 2–6.

## 7. Failure scenarios

| Симптом | Проверка | Корекция |
|---|---|---|
| `kafkasources` CRD липсва | `oc api-resources` | Няма Knative KafkaSource installation; lab блокиран |
| Broker/Trigger `READY=False` | `oc describe broker/trigger` | Анализирай control-plane events / sink readiness |
| KafkaSource `READY=False` | `oc describe kafkasource` | Topics, DNS, network, Kafka auth |
| BuildConfig Forbidden | `oc auth can-i create...` | Използвай разрешен namespace, без cluster-wide escalation |
| Pod CrashLoopBackOff | `oc logs deploy/m14-globex-reviews --previous` | Configuration, image, dependency issue |
| Route HTTP 401 | `INGEST_KEY` и `X-Api-Key` | Използвай правилната собствена тайна без печатане |
| Review остава pending | `oc get kafkasource,trigger` и C# logs | Kafka/Knative delivery/consumer failure |
| Unexpected duplicates | KafkaSource retry / API callbacks | ReviewState и PG idempotency са частични; нужен production outbox |
| PostgreSQL/Grafana липсват | Този лаб не deploy-ва DB/observability addons | Интегрирай поддържаните services; не твърди full persistence |
| Изисква се SASL/TLS | Kafka client е plaintext demo | Нужен поддържан security adapter и конфигурация |

## 8. Cleanup — само обектите от упражнението

Спри всякакъв временен port-forward. След това **в избрания личен Project**:

```bash
oc delete trigger/m14-moderation-trigger trigger/m14-sentiment-trigger --ignore-not-found
oc delete kafkasource/m14-globex-kafka-source --ignore-not-found
oc delete broker/m14-reviews-broker --ignore-not-found
oc delete route/m14-globex-reviews --ignore-not-found
oc delete deployment/m14-globex-reviews service/m14-globex-reviews --ignore-not-found
oc delete secret/m14-review-secret --ignore-not-found
oc delete buildconfig/m14-globex-image imagestream/m14-globex-image --ignore-not-found
oc delete builds -l buildconfig=m14-globex-image --ignore-not-found
oc get deploy,svc,route,secret,bc,is,broker,kafkasource,trigger
unset INGEST_KEY M14_IMAGE M14_BOOTSTRAP M14_HOST
```

**Не** изтривай чужд Kafka cluster, operator, namespace, Kafka topics или Kubernetes CRDs. Topics са **platform-owned** и не са създадени от този lab. Ако се налага data retention/cleanup за review events, съгласувай го с Kafka administrator.

**Приемане:** съществуват реално Ready KafkaSource + Broker + 2 Triggers, review submission идва през HTTPS Route, callbacks се обработват, проверките минават, а cleanup премахва само собствените resources. **Няма live cluster test в GitHub Actions**, защото това изисква твоята разрешена инфраструктура.
