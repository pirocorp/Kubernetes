# Lab 13-B — North–South: партньори, API ключове, quotas и analytics

**Цел:** Travelz предоставя контролирани API-та на външните **Red Company** и **Blue Company**. Различаваме business API management от вътрешното service-to-service управление. Оригинален сценарий: [Red Hat — Engaging with Partners / North-South](https://www.solutionpatterns.io/solution-pattern-apim-servicemesh/comprehensive-service-architecture/03-demo.html).

## 1. Предпоставки

- .NET SDK 10, Python 3.10+, Bash, работна директория = Module 13 root.
- Отворени портове 5100–5300; ако има стари процеси от предишния lab, ги спри по описания начин.
- Кодът е включен: [partner_gateway.py](../tools/partner_gateway.py), [partner_client.py](../tools/partner_client.py), [partner_metrics.py](../tools/partner_metrics.py), [verify.py](../tools/verify.py). **Не** се изискват 3scale, Operator, 3scale license или OpenShift.

```bash
# Ако Lab 13-A още работи, първо го спри, за да изчистим in-memory rate-limit counters.
bash scripts/stop.sh
bash scripts/start.sh
set -a
# Единствено собственият файл, създаден от tools/keys.py — не source-вай чужди файлове.
. .runtime/keys.env
set +a
```

**Очаквано:** health checks са зелени, двете demo credentials са налични само в environment.

## 2. Защо 3scale, а не само Istio?

**3scale API Management** предоставя product onboarding, developer applications, ключове/credentials, application plans, quotas и usage analytics. **Service Mesh** е фокусиран върху workload identities, traffic management, mTLS и observability между услуги. Двете решения могат да се комбинират, но изпълняват различни задачи.

Тук `partner_gateway.py` е **учебен HTTP proxy**:
- Red partner: **3 заявки на 15 секунди**.
- Blue partner: **6 заявки на 15 секунди**.
- Без валиден `X-Partner-Key`: **401 Unauthorized**.
- При надвишен лимит: **429 Too Many Requests**.
- Външните партньори получават **само v2** от `agency-v2:5102`.
- Admin-only `/_metrics` е защитен с отделен `X-Admin-Key`.

**Нито един от тези механизми не е пълноценна 3scale Application Plan/Developer Portal интеграция.**

## 3. Изпълни проверките

```bash
python3 tools/verify.py partner
python3 tools/partner_metrics.py --base-url http://127.0.0.1:5300
```

**Очаквано:** Red връща последователно `200, 200, 200, 429`, Blue връща `200`. Метриките съдържат поне `requests_red`, `requests_blue` и `limited_red`.

Можеш да извикаш partner поотделно (след като изтече 15-секундният прозорец или рестартираш само собствените локални процеси):

```bash
python3 tools/partner_client.py --partner red --count 1 --base-url http://127.0.0.1:5300
python3 tools/partner_client.py --partner blue --count 1 --base-url http://127.0.0.1:5300
```

Използваме Python client, който **чете ключовете от environment** и не ги показва в терминала или command arguments. Не поставяй secret в URL/query string и не commit-вай `.runtime/keys.env`.

## 4. Как изглежда корпоративната 3scale архитектура?

| Travelz нужда | Реален 3scale ресурс | Демонстрация |
|---|---|---|
| Публикуване на Partner API | Product + Backend + APIcast | Partner gateway + v2 Agency upstream |
| Red/Blue registration | Developer Accounts/Applications | Два локални ключа |
| Различни условия на ползване | Application Plans | Различни фиксирани лимити |
| Authorization | Credential/Policy validation | `X-Partner-Key` |
| Usage monitoring | Methods/Metrics/Analytics | In-memory counters |
| Developer discovery | Developer Portal + OpenAPI | Документацията на Module 13 |

Red Hat оригиналът включва реални partner приложения, 3scale portal и self-signup. **Тези UI/акаунтни процеси не се симулират**: реалната платформа изисква инсталиран и конфигуриран 3scale, различни application credentials и собствена governance политика. В [архитектурната справка](../docs/ENTERPRISE-3SCALE-MESH.md) е описан enterprise вариантът.

## 5. Failure scenarios

| Симптом | Диагноза | Действие |
|---|---|---|
| `401` с Red key | Използваш друг файл/процес | Спри/start от същата директория; зареди съществуващия `.runtime/keys.env` |
| Red дава 429 по-рано | Лимитът не се нулира между тестовете | Изчакай 15 сек или рестартирай учебния gateway |
| Partner API 502 | v2 Agency не работи | `cat .runtime/agency-v2.log`, `cat .runtime/gateway.log` |
| Admin metrics 401 | Няма `ADMIN_KEY` | Зареди го чрез `source .runtime/keys.env` |
| Невалиден HTTPS certificate | Този lab е само на 127.0.0.1 HTTP | В Lab 13-D се тества edge TLS Route |

## 6. Cleanup

```bash
unset PARTNER_RED_KEY PARTNER_BLUE_KEY ADMIN_KEY
bash scripts/stop.sh
```

Не изтривай ключовете, ако ще изпълняваш Labs 13-C/D. Когато приключиш, изтрий **само** собствения `.runtime/keys.env`. Няма Kubernetes ресурси.

**Приемане:** наблюдавани 401/200/429, Red и Blue имат различен лимит, v2 е единственият partner backend, metrics са защитени с admin key.