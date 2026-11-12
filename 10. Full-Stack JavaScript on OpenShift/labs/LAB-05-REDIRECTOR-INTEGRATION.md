# Lab 10-E — Redirector image, свързване на услугите и крайна интеграция

**Цел:** завърши оригиналния Red Hat [full-stack JavaScript learning path](https://developers.redhat.com/learn/openshift/how-deploy-full-stack-javascript-applications-openshift): добави redirector microservice от готов container image, свържи го с PostgreSQL и frontend чрез environment variables и докажи истински HTTP **201 → 302**. Оригиналният Red Hat redirector е Go image; нашият учебен вариант е **Node.js със собствен source**, за да е самодостатъчен.

## 1. Изисквания и preflight

За live OpenShift упражнението са нужни личен/разрешен Project, работещ \`oc\`, права за BuildConfig/Build/ImageStream/Deployment/Service/Secret и достатъчна quota. **Не инсталирай Operators и не използвай cluster-admin.** Задължителни са ресурсите от другите три упражнения:

- **10-B:** \`m10-frontend\` Deployment, Service и HTTPS Route (с [frontend-route.yaml](../openshift/frontend-route.yaml)).
- **10-C:** \`m10-postgres\` DB Service, създадена \`short_links\` таблица и \`m10-db-url\` Secret с \`DATABASE_URL\`.
- **10-D:** \`m10-backend\` Deployment/Service, readyz=200 и \`BACKEND_URL=http://m10-backend:8080\` на frontend.

**Не предполагай, че тези ресурси са останали след cleanup.** Ако започваш направо от 10-E, изпълни последователно **10-B раздели 2–3, 10-C раздели 2–6 и 10-D раздели 2–5**. Това са точните, включени в репото prerequisite инструкции. За работа **без cluster** изпълни [10-A](./LAB-01-ENVIRONMENT-LOCAL.md) — пълният stack е наличен в Docker Compose.

От корена на Module 10:

\`\`\`bash
oc whoami
oc project
oc get deployment/m10-frontend deployment/m10-backend
oc get service/m10-frontend service/m10-backend service/m10-postgres
oc get route/m10-frontend secret/m10-db-url
oc auth can-i create buildconfigs.build.openshift.io
oc auth can-i create builds.build.openshift.io
oc auth can-i create imagestreams.image.openshift.io
oc auth can-i create deployments.apps
test -f src/redirector/server.mjs
test -f src/redirector/Dockerfile
\`\`\`

**Очаквано:** всички собствени ресурси са налични, всички \`can-i\` са \`yes\`, frontend и backend работят. Ако са липсващи — първо изпълни точно посочените раздели, без да използваш чужди именувани resources.

## 2. Какво прави redirector-ът?

Short URL \`/r/{code}\` не е просто HTTP endpoint: redirector прави **SELECT target_url FROM short_links WHERE code=$1** в PostgreSQL и изпраща **HTTP 302 с Location**. При липсващ code връща 404, при DB отказ — 503. Не извиква публичен backend Route, не държи данни в собствена памет и не излага database извън namespace.

\`\`\`mermaid
sequenceDiagram
    participant U as Browser
    participant F as Frontend Node.js
    participant B as Backend Node.js
    participant P as PostgreSQL
    participant R as Redirector Node.js
    U->>F: POST /api/shorten {url}
    F->>B: POST /shorten
    B->>P: INSERT short_links(code,target_url)
    B-->>U: HTTP 201 via Frontend
    U->>F: GET /r/code
    F->>R: GET /r/code
    R->>P: SELECT target_url
    R-->>F: HTTP 302 Location
    F-->>U: HTTP 302 Location
\`\`\`

## 3. Image-first OpenShift deployment

**Идеята на Red Hat:** първо се доставя **готов image**, после се свързва конфигурацията. В този курс подготвяме този image от предоставения source — не използваме чужд Go image с неизвестни dependencies. \`Dockerfile\` съдържа Node.js 22, \`pg\` client, непривилегирован runtime UID и порт 8080.

\`\`\`bash
oc new-build --name=m10-redirector --binary --strategy=docker
oc start-build m10-redirector --from-dir=src/redirector --follow --wait
oc get builds -l buildconfig=m10-redirector
oc get imagestream/m10-redirector
oc new-app --name=m10-redirector --image-stream=m10-redirector:latest
oc set env deployment/m10-redirector --from=secret/m10-db-url
oc rollout status deployment/m10-redirector --timeout=300s
oc get deployment/m10-redirector service/m10-redirector
oc logs deployment/m10-redirector --tail=40
\`\`\`

**Очаквано:** Build \`Complete\`, \`m10-redirector\` Pod е Ready, Service слуша 8080, \`DATABASE_URL\` се зарежда от Secret. Това е **deployment от вече построен image**, а не още едно S2I упражнение. Не стартирай командите ако имаш чужд \`m10-redirector\` Deployment — имената трябва да са свободни в твоя Project.

## 4. Независима проверка на redirector Service

Отвори **терминал A**:

\`\`\`bash
oc port-forward service/m10-redirector 3112:8080
\`\`\`

В **терминал B**:

\`\`\`bash
curl -fsS http://127.0.0.1:3112/healthz
curl -fsS http://127.0.0.1:3112/readyz
curl -sS -o /dev/null -w 'Unknown code: %{http_code}\n' \
  http://127.0.0.1:3112/r/unknown
\`\`\`

**Очаквано:** \`ok\`, \`ready\` и HTTP \`404\` за неизвестния short code. При \`503 database_unavailable\` проверявай първо \`DATABASE_URL\`, PostgreSQL Service DNS, credentials, таблицата и DB Pod; \`/healthz\` самостоятелно не е readiness proof. Спри port-forward с Ctrl+C.

## 5. Свържи всичко чрез OpenShift environment variables

Frontend извиква backend и redirector **по вътрешен Service DNS**. Публичен е само неговият edge-TLS Route. Browser не получава директни DB/Service addresses.

\`\`\`bash
oc set env deployment/m10-frontend \
  BACKEND_URL=http://m10-backend:8080 \
  REDIRECTOR_URL=http://m10-redirector:8080
oc rollout status deployment/m10-frontend --timeout=300s
oc get deployment/m10-frontend -o jsonpath='{.spec.template.spec.containers[0].env}'
M10_ROUTE="$(oc get route m10-frontend -o jsonpath='{.spec.host}')"
test -n "$M10_ROUTE"
curl -fsS "https://$M10_ROUTE/api/status"
\`\`\`

**Очаквано:**

\`\`\`json
{"frontend":true,"backend":true,"database":true,"redirector":true}
\`\`\`

Ако някоя стойност е \`false\`, не продължавай — прегледай \`oc get pods\`, \`oc get svc\`, \`oc logs\`, DNS, Service endpoints и Secret. Не използвай \`curl -k\` за заобикаляне на TLS сертификат.

## 6. Пълен приемателен тест от публичния HTTPS Route

\`\`\`bash
python3 tools/verify_cluster.py --base-url "https://$M10_ROUTE"
\`\`\`

**Очаквано:** валидира се \`GET /\` и browser JS, грешен URL дава 400, валиден URL дава 201 и валиден short code, \`GET /r/code\` дава **302 Location** към оригиналния URL. Проверката **не следва** redirect-а към външен website. Синтетичните тестови записи отиват в собствената учебна DB.

В браузър отвори \`https://$M10_ROUTE\`, въведи \`https://example.org/training\`, създай кратък URL и го отвори. **Не** тествай със secret-bearing вътрешни адреси или production данни.

### Защо това е важна OpenShift практика?

| Слой | Namespace resource | Публичен? |
|---|---|---|
| Browser UI / reverse proxy | Route → Service \`m10-frontend:8080\` | **Да, HTTPS** |
| Shorten backend | \`m10-backend:8080\` | Не |
| Redirector | \`m10-redirector:8080\` | Не |
| PostgreSQL | \`m10-postgres:5432\` | Не |

Вътрешната комуникация минава по Services и DNS; \`oc set env\` обновява Pod template и предизвиква **rollout**, а не автоматично нова image компилация. Чети секцията за Deployment и Secrets в [Module 09](../../09.%20OpenShift/README.md).

## 7. Troubleshooting

| Проблем | Проверка | Корекция |
|---|---|---|
| \`Forbidden\` при build | \`oc auth can-i create builds.build.openshift.io\` | Липса на RBAC; не е разрешено повишаване на привилегии |
| ImagePullBackOff | \`oc describe pod\` | ImageStream/build output и registry |
| redirector \`/readyz\` → 503 | \`oc logs deploy/m10-redirector\` | DB Secret/Service, таблица |
| frontend status показва redirector=false | \`oc get svc m10-redirector\` | Проверка на \`REDIRECTOR_URL\` и DNS |
| \`GET /r/code\` → 404 | SQL запис или неправилен code | Създай нов short URL и използвай получения code |
| \`GET /r/code\` → 502 | Frontend не може да достигне redirector | NetworkPolicy, env, Pod readiness |
| UI се зарежда, но POST → 502 | Backend не е Ready | \`BACKEND_URL\`, logs, \`/readyz\` |
| HTTPS Route не работи | \`oc describe route m10-frontend\` | Router/host, edge TLS |
| След Pod restart няма линкове | 10-C вариант B/C (ефимерна DB) | Очаквано; за PVC persistence избери вариант A още при първоначалното deployment |

## 8. Cleanup — в правилния ред

Ако преглеждаш готовото приложение, остави всичко. За край на Module 10, изтрий **само** собствените namespace resources (без cluster-wide промени):

\`\`\`bash
oc delete route/m10-frontend --ignore-not-found
oc delete deployment/m10-frontend deployment/m10-backend \
  deployment/m10-redirector --ignore-not-found
oc delete service/m10-frontend service/m10-backend \
  service/m10-redirector --ignore-not-found
oc delete buildconfig/m10-frontend buildconfig/m10-backend \
  buildconfig/m10-redirector --ignore-not-found
oc delete imagestream/m10-frontend imagestream/m10-backend \
  imagestream/m10-redirector --ignore-not-found
oc delete builds -l buildconfig=m10-frontend --ignore-not-found
oc delete builds -l buildconfig=m10-backend --ignore-not-found
oc delete builds -l buildconfig=m10-redirector --ignore-not-found
oc delete secret/m10-db-url --ignore-not-found
oc delete deployment/m10-postgres service/m10-postgres --ignore-not-found
oc delete pvc/m10-postgres-data --ignore-not-found  # само ако данните вече не трябват
oc delete secret/m10-postgres-auth --ignore-not-found
# само ако използва оригиналния template вариант C:
oc get dc/m10-postgres >/dev/null 2>&1 && oc delete dc/m10-postgres
oc get deploy,svc,route,bc,is,dc
unset M10_ROUTE
\`\`\`

**Ако template C създава допълнителни обекти**, използвай записания изход от \`oc process -n openshift postgresql-ephemeral ... -o name\` от 10-C, за да изтриеш единствено собствените ресурси. При вариант A PVC има отделен data lifecycle; при B/C данните са ефимерни. Не изтривай Projects, Operators или чужди приложения.

**Критерий:** нов microservice от build image, конфигурация чрез Secret/Service DNS, цялостен browser → frontend → backend/redirector → PostgreSQL поток и успешен HTTPS 201→302 тест.
