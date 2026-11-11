# Lab 13-B — Moderation, Sentiment Scoring, privacy и безопасно публикуване

**Цел:** отдели **moderation decision** от **sentiment score**; провери, че review с забранено съдържание **не се публикува**, независимо от sentiment оценката. Това адаптира двата независими intelligent application consumers от [Red Hat Globex Pattern](https://www.solutionpatterns.io/solution-pattern-sentiment-analysis/solution-pattern-sentiment-analysis/03-demo.html).

## 1. Предпоставки

.NET SDK 10, Python 3.10+, Bash, Git, порт 5080 и source файловете в Module 13. Няма нужда да си изпълнил Lab 13-A преди това. От корена на Module 13:

```bash
test -f src/GlobexReviews/ReviewProcessor.cs
test -f src/GlobexReviews/ReviewState.cs
test -f src/GlobexReviews/Domain.cs
test -f tools/verify.py
bash scripts/verify-local.sh
```

**Очаквано:** build и HTTP тестовете минават и учебният API се спира автоматично.

## 2. Двата business outcomes са различни

| Въпрос | Review Moderation | Sentiment Analysis |
|---|---|---|
| За какво решава? | Може ли текстът да бъде показан публично? | Каква е емоционалната оценка на текста? |
| Изход | `approved` или `denied` с reason | `positive/negative/neutral` и score |
| Влияе на PostgreSQL? | **Само approved** се записва | Не променя moderation decision |
| Влияе на времевия анализ? | Може да има политика за филтриране на denied events | Scores се записват в time-series sink |
| Модел в този лаб | Детерминистичен blocklist | Детерминистичен lexicon scorer |
| Подходящ за production? | **Не** без човешки review и ML evaluation | **Не** без обучен и валидиран модел |

Нашата **локална** логика се намира в [ReviewRules](../src/GlobexReviews/Domain.cs). Blocklist е `spam`, `scam` и `abusive`; използваме **отделни думи**, а не `substring`, за да не маркираме произволна част от друга дума. Реалната moderation система изисква езици, контекст, false-positive/false-negative анализ, appeals, bias и human-in-the-loop.

Scorer брои демонстрационни положителни/отрицателни думи, изчислява:

\[
score = \frac{N_{\text{positive}} - N_{\text{negative}}}{N_{\text{positive}} + N_{\text{negative}}}
\]

При нула намерени думи резултатът е `0` (neutral); score е между `−1` и `+1`. Тези резултати **не са вероятност** и не бива да се интерпретират като confidence на реален ML модел.

## 3. Стартирай самостоятелен API

В терминал 1:

```bash
dotnet build src/GlobexReviews/GlobexReviews.csproj -c Release
ASPNETCORE_URLS=http://127.0.0.1:5080 REVIEWS_MODE=local \
  dotnet run --project src/GlobexReviews/GlobexReviews.csproj \
  -c Release --no-build --no-launch-profile
```

В терминал 2, от същия корен, генерирай синтетични reviews:

```bash
python3 tools/generate_reviews.py --base-url http://127.0.0.1:5080 --count 30
python3 tools/verify.py --base-url http://127.0.0.1:5080
curl -fsS http://127.0.0.1:5080/reviews/approved
curl -fsS http://127.0.0.1:5080/metrics/sentiment
```

**Очаквано:** всички 30 POST заявки са приети с HTTP 202; `verify.py` изпраща още четири **контролирани** fixtures и доказва approved/denied/positive/negative/neutral. В `/reviews/approved` няма текстове с `spam` (според този учебен blocklist), но те могат да бъдат анализирани от отделния sentiment worker.

**Важно:** оригиналният Red Hat pattern използва Kafka topics `globex.reviews` → `reviews.moderated` / `reviews.denied` и отделен sentiment поток. Локалният in-memory режим демонстрира **семантиката**, а **Kafka topics действително се създават и консумират** в [Lab 13-C](./LAB-03-KAFKA-STORAGE-DASHBOARD.md).

## 4. Защо отрицателен review може да бъде approved?

Например `"This bag is broken and terrible"` е **негативен**, но не е злоупотреба. Негативните мнения са ценни за бизнеса и не трябва да се блокират просто защото са негативни. `"This is spam"` е `denied` в нашия test, независимо дали sentiment е neutral. В production трябва да обособиш независими model version, moderation policy, thresholds и compliance review.

### Проверка на event types

```bash
curl -fsS http://127.0.0.1:5080/events
```

Провери дали има поне по един от:
- `globex.review.submitted`
- `globex.review.moderated`
- `globex.review.denied`
- `globex.review.sentiment`

**Не** очаквай глобален ред между двете независими processing branches.

## 5. Idempotency, backpressure и failure handling

**Idempotency:** в local state резултатите се записват по стабилен `reviewId` с `TryAdd`. В PostgreSQL има `review_id UUID PRIMARY KEY` и `INSERT ... ON CONFLICT DO NOTHING`. Това защитава approval persistence от повторно изпълнение. Все пак при Kafka/Knative redelivery е възможно **повторно излъчване на derived events**, защото SQL commit и Kafka publish не участват в една атомарна транзакция. Това е **at-least-once**, не exactly-once end-to-end.

**Backpressure:** двата локални `Channel<Review>` имат капацитет 1024 с режим `Wait`. При изчерпване publisher чака, докато има място. Това предотвратява безкраен ръст на queue паметта, но означава, че latency на `POST` се увеличава. При Kafka тези проблеми се управляват чрез partitions/consumer groups/lag, quotas и retention.

**Delivery failures:** локалните workers логват грешка, но **нямат durable retry**; не ги приемай за production message processing. Kafka consumer loop прави seek/retry и commit след успешни side-effects. За production добави ограничен retry, dead-letter queue, alerts, poison-message policy, outbox/inbox и мониторинг на consumer lag.

**Privacy:** в този курс се използват **само синтетични ревюта**. Реални клиентски данни не се изпращат към публичен model endpoint. При production провери GDPR, retention, encryption, redaction и дали denied текстове трябва да се съхраняват или изобщо да участват в sentiment dashboard.

## 6. Самопроверка

1. Защо `negative` review не трябва автоматично да е `denied`?
2. Каква е разликата между `moderation policy` и `sentiment model`?
3. Защо два Kafka consumer groups са по-удачни от един общ group за независимите процесори?
4. Какво означава `HTTP 202` в система с eventual consistency?
5. Какво се случва, ако Postgres записът е успял, но Kafka publish на derived event се провали?
6. Защо `reviewId` трябва да е стабилен при retries и replay?

**Насоки:** (1) мнение срещу abuse; (2) publishability срещу sentiment; (3) всеки group получава собствено копие от потока; (4) само accepted, не completed; (5) duplicate/partial effects — нужен е outbox design; (6) idempotency.

## 7. Troubleshooting и cleanup

| Проблем | Провери | Корекция |
|---|---|---|
| Review остава pending | Локалният process и stderr | `dotnet run` отново; може да има worker exception |
| Всички са neutral | Текстът съдържа непознати за demo lexicon думи | Използвай английските sample fixtures; това не е multilingual model |
| Denied се показва публично | `/reviews/approved` и `ReviewRules.Moderate` | Провери логиката и забранените токени, не променяй тестовете |
| Няма Kafka topics | `REVIEWS_MODE=local` | За реален broker следвай Lab 13-C |
| `Address already in use` | Port 5080 | Спри собственото foreground приложение или стар PID |
| `NU1301` | NuGet restore | Провери proxy и NuGet достъп |

**Cleanup:** Ctrl+C в терминала с ASP.NET Core API. In-memory results изчезват; няма създадени external topics, Postgres schema или OpenShift ресурси.

**Критерий:** можеш да докажеш, че moderation и sentiment са независими, че negative ≠ denied, и да обясниш идемпотентността/at-least-once ограниченията.
