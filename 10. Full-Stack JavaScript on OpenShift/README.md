# Module 10 — Full-Stack JavaScript Applications on OpenShift

**Този модул свързва основите на OpenShift (Module 09) с архитектурните API и distributed-systems Modules 11–15.** Ще построиш и публикуваш истинско full-stack JavaScript приложение: **Shorties URL Shortener** с browser UI, Node.js frontend, Node.js backend, Node.js redirector и PostgreSQL. Всяко приложение има собствен source code, Dockerfile и startup configuration. Включени са пет пълни практически упражнения, очаквани резултати, проверки, troubleshooting, cleanup и автоматизирани GitHub Actions тестове.

**Основен източник:** [Red Hat Developer — How to deploy full-stack JavaScript applications in OpenShift](https://developers.redhat.com/learn/openshift/how-deploy-full-stack-javascript-applications-openshift), Don Schenck, първоначално публикуван 5 февруари 2024 г. Оригиналът е learning path с **6 resources (Overview + пет практични части)** и 1 час и 25 минути. Той включва Podman, Quay.io, frontend image, OpenShift PostgreSQL template, Node.js backend чрез Source-to-Image (S2I), environment variables и microservice от готов image.

**Нашата адаптация:** запазваме **всички пет задачи**, но предоставяме самодостатъчен код. Оригиналният redirector image използва Go; тук за последователност със заглавието и независимост от чужд registry използваме собствен Node.js redirector. Добавени са Docker Compose и Postgres за доказано изпълним локален end-to-end път, при което **само frontend се публикува през Route**. Това не е C# модул — JavaScript/Node.js са съзнателна цел на оригинала.

## 1. Какво ще научиш?

- Да подготвиш Node.js 22, Git, Bash, Docker/Podman и OpenShift CLI \`oc\`.
- Да изградиш frontend от JavaScript source и да провериш **локално** същия HTTP интерфейс, който после работи в контейнер.
- Да различаваш image build, image registry, ImageStream, Deployment, Service и OpenShift Route.
- Да използваш **Podman build → Quay push → OpenShift pull**, както в оригинала, или включения **OpenShift binary Docker build** без външен registry акаунт.
- Да създадеш PostgreSQL от \`postgresql-ephemeral\` template **само когато наистина е наличен** и да инициализираш предоставения SQL.
- Да създадеш backend от source чрез S2I (при наличен Node builder), с реален Docker build fallback.
- Да използваш \`Secret\`, \`oc set env\`, \`/healthz\` и \`/readyz\` за свързване на услугите.
- Да добавиш redirector като отделен контейнерен microservice и да провериш HTTP 201 при създаване на URL и **302 Location** при отваряне.
- Да диагностицираш DNS/Service, погрешни env variables, image pull, PostgreSQL startup, 502/503, RBAC/quota и loss of data при ephemeral storage.

**Предварителни знания:** [Kubernetes 00–08](../README.md) и [Module 09 — OpenShift](../09.%20OpenShift/README.md); не се изисква предварителен JavaScript опит. Използваният Node.js source е малък, а всеки компонент е обяснен.

## 2. Пълна архитектура

\`\`\`mermaid
flowchart LR
    U["Browser — HTML, CSS, JS"] -->|"HTTPS Route (OpenShift)"| FE["Frontend Node.js / reverse proxy"]
    FE -->|"POST /shorten via Service DNS"| BE["Backend Node.js"]
    FE -->|"GET /r/code via Service DNS"| R["Redirector Node.js"]
    BE -->|"SQL INSERT"| DB[("PostgreSQL short_links")]
    R -->|"SQL SELECT"| DB
    DB -.->|"Shared synthetic lab state"| BE
\`\`\`

| Слой | Отговорност | Локален адрес | OpenShift ресурс |
|---|---|---|---|
| Frontend | Статичен HTML/JS, \`/api/shorten\`, \`/r/:code\`, \`/api/status\` | \`127.0.0.1:3110\` | \`m10-frontend\` Service + **един HTTPS Route** |
| Backend | Валидация на target URL, генериране на short code, SQL INSERT | \`127.0.0.1:3111\` | \`m10-backend\` ClusterIP |
| Redirector | SELECT по short code, HTTP 302 или 404 | \`127.0.0.1:3112\` | \`m10-redirector\` ClusterIP |
| PostgreSQL | Durable table \`short_links\` | \`127.0.0.1:5439\` | \`m10-postgres\` Service, ephemeral DB в 10-C |

**Защо не изложим backend и database?** Browser работи чрез **един** публичен frontend URL; frontend proxy достъпва другите услуги вътрешно с DNS. Така не са нужни CORS за публични backend адреси и не излагаме случайно DB connection string на клиента. Това **не** е пълна production security architecture: за реална услуга трябва auth, rate limits, anti-abuse/SSRF policy, audit, lifecycle и explicit network policy.

### Sequence: Shorten → Redirect

\`\`\`mermaid
sequenceDiagram
    participant U as User/browser
    participant F as Frontend
    participant B as Backend
    participant PG as PostgreSQL
    participant R as Redirector
    U->>F: POST /api/shorten URL
    F->>B: POST /shorten
    B->>PG: INSERT code,target_url
    PG-->>B: COMMIT
    B-->>U: 201 via Frontend
    U->>F: GET /r/code
    F->>R: GET /r/code
    R->>PG: SELECT target_url
    R-->>U: 302 Location via Frontend
\`\`\`

**Коректността не идва от картинката**, а от изпълними тестове: \`tools/verify.py\` проверява frontend, backend, redirector, валидиране на входа, SQL запис, HTTP redirects и persistence след рестарт.

## 3. Пет упражнения по оригиналния Red Hat learning path

| Упражнение | Сценарий | Проверка |
|---|---|---|
| **10-A** | [Environment, Git, Node и локално приложение](./labs/LAB-01-ENVIRONMENT-LOCAL.md) | Node syntax, frontend 200/502, пълен local Compose |
| **10-B** | [Frontend image, Podman/Quay и OpenShift Route](./labs/LAB-02-FRONTEND-CONTAINER.md) | Container build, 1/1 Ready и frontend HTTPS |
| **10-C** | [PostgreSQL template, Secret и SQL schema](./labs/LAB-03-POSTGRESQL.md) | \`postgresql-ephemeral\` (ако съществува), \`short_links\`, internal DNS |
| **10-D** | [Backend от source — S2I, env и readiness](./labs/LAB-04-BACKEND-S2I.md) | S2I/Docker build, \`/readyz\`, POST 201 |
| **10-E** | [Redirector image и завършен 4-tier stack](./labs/LAB-05-REDIRECTOR-INTEGRATION.md) | HTTPS Route → PostgreSQL → HTTP 302 |

**Ред:** 10-A → B → C → D → E. Всички source files, Dockerfiles, SQL и тестови scripts са в настоящия модул. **A може да се изпълни напълно без OpenShift; B–E изискват реален разрешен Project и налични platform prerequisites.** Ако template или S2I builder липсва, това е **явно ограничение**, а не причина да инсталираш Operators със cluster-admin. В B/D има Docker-build fallback; C честно изисква template, когато упражнява именно template-based deployment.

## 4. От чист checkout — един локален тест без OpenShift

Изисквания: Docker Engine/Compose v2, Bash, Python 3.10+, Git, свободни localhost портове **3110, 3111, 3112, 5439**, интернет за първо изтегляне на image/npm packages. Node 22 е необходим за **самостоятелния** frontend/syntax test, но пълният Docker stack компилира и стартира приложенията **в контейнерите**.

\`\`\`bash
git clone https://github.com/pirocorp/Kubernetes.git
cd "Kubernetes/10. Full-Stack JavaScript on OpenShift"
python3 scripts/check-links.py
python3 tools/init_env.py
bash scripts/verify-compose.sh
\`\`\`

**Очаквано:** \`ALL MODULE 10 REAL FULL-STACK INTEGRATION CHECKS PASSED\`. Тестът използва **реален PostgreSQL 17.6**, а не fake datastore, и проверява, че създаден short link още работи след рестарт на **трите Node услуги**. Можеш да отвориш \`http://127.0.0.1:3110\` и да видиш Shorties UI.

**Възпроизводимост:** трите Node.js проекта включват `package-lock.json`; Dockerfile-ите използват `npm ci` и GitHub Actions проверява истинска npm инсталация. При промяна на dependencies обнови и lockfile. Преди PR #36 да бъде слят, след `git clone` изпълни от корена на репото `git switch feat/module-10-fullstack-openshift-renumber-2026`; след merge в `main` това не е нужно.

Отделен тест на frontend без Docker/DB:

\`\`\`bash
bash scripts/verify-node.sh
\`\`\`

**Очаквано:** HTML и JavaScript 200, \`/api/status\` показва degraded dependencies, \`POST /api/shorten\` връща **очаквано 502** за липсващ backend.

### Локален cleanup

\`\`\`bash
docker compose down
\`\`\`

Това оставя Postgres data volume. **Само ако желаеш да изтриеш учебните линкове:**

\`\`\`bash
docker compose down -v
\`\`\`

Няма \`docker system prune\` или изтриване на чужди контейнерни ресурси. Локалният \`.env\` е \`0600\`, случаен и Git-ignored; не публикувай стойностите му.

## 5. Защо тези техники са важни?

**Source-to-Image (S2I)**: OpenShift builder приема source и генерира runnable container image, като инсталира зависимости и спазва build strategy. **Dockerfile build**: използва конкретни layer инструкции, включени в кода; може да се изпълни локално с Podman/Docker или в OpenShift binary build. **Готов image**: може да се инсталира директно, без rebuild на source; но трябва да имаш увереност в supply chain и версиите. **ImageStream**: OpenShift abstraction над образи/тагове, с възможност за следене на updates.

**Deployment конфигурация**: \`oc set env\` променя environment-а на Pod template и предизвиква **rollout**, а не автоматично повторно build-ване на image. **Secret** е namespaced API resource за credentials; не поставяй пароли в source, README, frontend JS, URLs или командния history. **Routes** са за външни приложения; вътрешните database и microservices се достъпват през \`Service\` и DNS.

**Readiness ≠ Liveness**: \`/healthz\` доказва, че HTTP процесът работи; \`/readyz\` изпълнява SQL \`SELECT 1\` и може да върне 503 при недостъпна DB. В production добави readiness probes към Deployment-ите, resources limits, TLS, credential rotation и monitoring.

**Ephemeral PostgreSQL**: данните може да изчезнат при Pod recreate — приемливо за временен lab, **не** за production. Локалният Compose демонстрира persistence с Docker named volume, различна конфигурация от OpenShift template.

## 6. Структура на проекта

\`\`\`text
10. Full-Stack JavaScript on OpenShift/
├── README.md
├── compose.yaml
├── sql/init.sql
├── src/
│   ├── frontend/
│   │   ├── Dockerfile, package.json, package-lock.json, server.mjs
│   │   └── public/{index.html,app.js,styles.css}
│   ├── backend/{Dockerfile,package.json,package-lock.json,server.mjs}
│   └── redirector/{Dockerfile,package.json,server.mjs}
├── openshift/{README.md,frontend-route.yaml}
├── tools/{init_env.py,prepare_oc.py,verify.py,verify_cluster.py}
├── scripts/{check-links.py,verify-node.sh,verify-compose.sh}
└── labs/
    ├── LAB-01-ENVIRONMENT-LOCAL.md
    ├── LAB-02-FRONTEND-CONTAINER.md
    ├── LAB-03-POSTGRESQL.md
    ├── LAB-04-BACKEND-S2I.md
    └── LAB-05-REDIRECTOR-INTEGRATION.md
\`\`\`

## 7. Troubleshooting — бърз справочник

| Проблем | Диагноза | Корекция |
|---|---|---|
| \`docker compose\` липсва | \`docker compose version\` | Инсталирай Compose v2 / провери Docker service |
| Port \`3110/5439\` зает | \`ss -lnt\` | Спри своя предишен process/container |
| ImagePullBackOff | \`oc describe pod\` | Registry/pull secrets/image name |
| Forbidden build | \`oc auth can-i create builds\` | Namespace RBAC/quota; не заобикаляй ограниченията |
| PostgreSQL template липсва | \`oc get template -n openshift postgresql-ephemeral\` | OpenShift template lab е условен; работи с Compose |
| S2I Node builder липсва | \`oc get is -n openshift\` | Docker-strategy fallback от 10-D |
| Backend 503 | \`oc logs deploy/m10-backend\` | Secret, DB DNS, credentials, SQL init |
| Frontend 502 | \`oc logs deploy/m10-frontend\` | Internal Service URLs, backend/redirector |
| Short redirect 404 | Code не е в DB | Създай нов code, провери SQL |
| UI работи, но \`/api/status\` degraded | Другите услуги още не са deploy-нати | Завърши Labs B–E |

**Пълен cleanup** на OpenShift ресурсите е в [Lab 10-E, раздел 8](./labs/LAB-05-REDIRECTOR-INTEGRATION.md). Не използвай \`oc delete project\`, \`docker system prune\` или чужди cluster resources.

## 8. Самопроверка

1. Защо backend и redirector не се публикуват през Route, след като frontend може да ги извиква чрез Service DNS?
2. Каква е разликата между build на image от source, push към registry и \`oc new-app\` от готов image?
3. Кога S2I е полезен и кога предпочиташ Dockerfile?
4. Каква е ролята на \`postgresql-ephemeral\` и какъв е рискът при рестарт?
5. Каква е разликата между \`/healthz\` и \`/readyz\`?
6. Защо frontend получава \`BACKEND_URL\` и \`REDIRECTOR_URL\` чрез Deployment env, а не ги вгражда в browser JS?
7. Как доказваш, че HTTP 302 наистина използва PostgreSQL, а не memory state?
8. Какви са условията, при които backend връща 400, 503 или 201?

**Насоки:** (1) internal DNS/least exposure; (2) build/artifact/deploy; (3) builder versus explicit Docker layers; (4) quick test but not durable; (5) process versus dependencies; (6) browser separation; (7) SQL + restart integration test; (8) invalid URL / DB unavailable / success.

## Официални Red Hat източници

- [Red Hat — Full-stack JavaScript OpenShift Learning Path](https://developers.redhat.com/learn/openshift/how-deploy-full-stack-javascript-applications-openshift)
- [Part 1 — Set up Node.js/OpenShift](https://developers.redhat.com/learning/learn:openshift:how-deploy-full-stack-javascript-applications-openshift/resource/resources:set-your-working-environment-nodejs-and-openshift-development)
- [Part 2 — Build frontend image and deploy](https://developers.redhat.com/learning/learn:openshift:how-deploy-full-stack-javascript-applications-openshift/resource/resources:run-application-locally-then-build-container-front-end-and-deploy-it-openshift)
- [Part 3 — PostgreSQL template](https://developers.redhat.com/learning/learn:openshift:how-deploy-full-stack-javascript-applications-openshift/resource/resources:deploy-database-openshift)
- [Part 4 — Backend, S2I, environment](https://developers.redhat.com/learning/learn:openshift:how-deploy-full-stack-javascript-applications-openshift/resource/resources:deploy-back-end-and-connect-it-database-and-front-end)
- [Part 5 — Add existing image and connect services](https://developers.redhat.com/learning/learn:openshift:how-deploy-full-stack-javascript-applications-openshift/resource/resources:deploy-new-microservice-existing-image-and-connect-all-services)

Материалите са собствена педагогическа адаптация на Red Hat learning path, не дословен copy/paste. Сценарият и основните технологични learning objectives са запазени.
