# Lab 10-D — Backend от source: OpenShift S2I, environment и database readiness

**Цел:** внедри **истински Node.js backend** от наличния source code, свържи го с PostgreSQL чрез Secret, configure-вай frontend чрез environment variables и провери health/readiness. Източник: [Red Hat — Backend S2I and environment variables](https://developers.redhat.com/learning/learn:openshift:how-deploy-full-stack-javascript-applications-openshift/resource/resources:deploy-back-end-and-connect-it-database-and-front-end).

## 1. Предпоставки и файлове

- Собствен OpenShift Project с `oc` и достатъчни namespace права за BuildConfig, Build, ImageStream, Deployment, Service, Secret и env modification.
- **Подготвена PostgreSQL** от [Lab 10-C](./LAB-03-POSTGRESQL.md) с `m10-postgres`, `short_links` table и `m10-db-url` Secret. Ако пропускаш предишните упражнения, изпълни **раздели 2–6 на 10-C**, преди този lab.
- Frontend от [Lab 10-B](./LAB-02-FRONTEND-CONTAINER.md) е необходим **само за пълната browser проверка** в раздел 5. Ако липсва, можеш да тестваш backend през port-forward.
- Файлове: [server.mjs](../src/backend/server.mjs), [package.json](../src/backend/package.json), [Dockerfile](../src/backend/Dockerfile).
- Проверка за **Node.js S2I builder image stream** (актуалният stream/tag зависи от инсталацията); примерът използва `nodejs:22-ubi9` само ако реално е наличен. **Няма задължителен GitHub fork** — build използва binary source upload от настоящия checkout.

## 2. Preflight

```bash
oc whoami
oc project
oc get secret/m10-db-url service/m10-postgres
oc get imagestream -n openshift | grep -i nodejs || true
oc auth can-i create buildconfigs.build.openshift.io
oc auth can-i create builds.build.openshift.io
oc auth can-i create deployments.apps
test -f src/backend/package.json
test -f src/backend/server.mjs
```

**Очаквано:** DB Secret и Service съществуват; имаш необходимите права. Ако Node.js S2I builder не е наличен, използвай **документирания Docker build fallback от раздел 3.2** — това е реален working path, не липсващ материал.

## 3. Source-to-Image — действителен build от source code

**3.1. Използвай наличен Node.js builder** (примерен ImageStream tag `nodejs:22-ubi9`, провери, че cluster го има):

```bash
oc new-build --name=m10-backend --binary --strategy=source \
  --image-stream=nodejs:22-ubi9
oc start-build m10-backend --from-dir=src/backend --follow --wait
oc get builds -l buildconfig=m10-backend
oc get imagestream/m10-backend
```

**Очаквано:** S2I изтегля/получава Node.js source, инсталира npm dependency `pg`, подготвя runnable image и Build става `Complete`. Source-to-Image превръща source в готов образ чрез builder image; **не е същото като Dockerfile build**.

**3.2. Надежден Docker-strategy fallback**, когато съответният S2I ImageStream липсва:

```bash
# Само ако не е създаден същият BuildConfig от 3.1:
oc new-build --name=m10-backend --binary --strategy=docker
oc start-build m10-backend --from-dir=src/backend --follow --wait
oc get imagestream/m10-backend
```

Използва включения `src/backend/Dockerfile` и Node.js 22. **Избери само единия build strategy**, не изпълнявай двата без cleanup на BuildConfig.

## 4. Deployment и database Secret

```bash
oc new-app --name=m10-backend --image-stream=m10-backend:latest
oc set env deployment/m10-backend --from=secret/m10-db-url
oc rollout status deployment/m10-backend --timeout=300s
oc get svc/m10-backend
oc logs deployment/m10-backend --tail=40
```

**Очаквано:** Service на 8080 и Ready Pod. Backend има `DATABASE_URL` от Secret, а `/readyz` прави действително `SELECT 1` към PostgreSQL. Ако Pod е Ready само защото няма probes, това **не доказва** database connectivity — тествай endpoint.

**Port-forward за тест без публичен Route:**

**Терминал A:**

```bash
oc port-forward service/m10-backend 3111:8080
```

**Терминал B:**

```bash
curl -fsS http://127.0.0.1:3111/healthz
curl -fsS http://127.0.0.1:3111/readyz
curl -sS -i -H 'Content-Type: application/json' \
  -d '{"url":"https://example.org/training"}' \
  http://127.0.0.1:3111/shorten
```

**Очаквано:** `ok`, `ready`, HTTP 201 с JSON `code` и `path`. При `503 database_unavailable` провери PostgreSQL Service, таблица, Secret, DNS и network policy. Спри port-forward с Ctrl+C.

## 5. Свържи frontend с backend чрез environment variable

Ако имаш Deployment от Lab 10-B:

```bash
oc set env deployment/m10-frontend BACKEND_URL=http://m10-backend:8080
oc rollout status deployment/m10-frontend --timeout=300s
M10_ROUTE="$(oc get route m10-frontend -o jsonpath='{.spec.host}')"
curl -fsS "https://$M10_ROUTE/api/status"
```

**Очаквано:** JSON `{"frontend":true,"backend":true,"database":true,"redirector":false}` — последният слой още не е внедрен. **Защо `BACKEND_URL` не е HTTPS Route?** Frontend се намира в същия namespace и използва internal Service DNS. Browser никога не извиква backend директно, следователно не са нужни CORS и публичен backend hostname.

## 6. Readiness, reliability и конфигурационни промени

Разликата между:
- `GET /healthz`: процесът е жив, без скъпа проверка на зависимости.
- `GET /readyz`: приложението реално може да отвори DB connection.
- `oc rollout status`: Deployment е обновен/стартиран, но качеството на HTTP service зависи от readiness probes и dependency health.

**В production:** не използвай immutable image tag `latest` за проследяване на release; pin digest, добави readinessProbe към `/readyz`, request limits, Secret rotation, resource limits, SLO metrics. С тази учебна конфигурация доказваме функционалния endpoint с тест, а не заявяваме автоматично SLA.

## 7. Troubleshooting

| Проблем | Проверка | Действие |
|---|---|---|
| S2I builder не съществува | `oc get is -n openshift` | Използвай Docker-strategy от 3.2 |
| Build fail по npm | `oc logs build/ИМЕ` | Проверка на registry/NuGet? **npm registry**, DNS/proxy |
| Pod CrashLoop | `oc logs deploy/m10-backend --previous` | Липсва DATABASE_URL или runtime error |
| `readyz` връща 503 | Secret + PostgreSQL logs | Преглед на DB credentials и таблицата |
| Frontend дава 502 | `oc get svc m10-backend` | Вътрешен DNS/Service, BACKEND_URL |
| Невалиден URL | HTTP 400 invalid_url | Използвай абсолютен `http/https` без userinfo |

## 8. Cleanup

Ако продължаваш към Lab 10-E, **не изтривай backend**. Иначе:

```bash
oc delete deployment/m10-backend service/m10-backend --ignore-not-found
oc delete buildconfig/m10-backend imagestream/m10-backend --ignore-not-found
oc delete builds -l buildconfig=m10-backend --ignore-not-found
```

Secret-ът `m10-db-url` и database `m10-postgres` са собственост на Lab 10-C; премахни ги чрез **неговия cleanup**, ако приключваш курса.

**Приемане:** S2I или Docker build от **предоставен JS source**, работещ backend без публичен Route, DB-backed HTTP 201 и конфигуриран frontend чрез env variable.
