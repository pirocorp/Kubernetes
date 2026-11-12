# Lab 10-C — PostgreSQL в OpenShift: независим Deployment, Secret, SQL и Service DNS

**Цел:** да подготвиш истинска PostgreSQL база в собствения OpenShift Project, достъпна **само чрез вътрешния Service**. Учебният път е самостоятелен дори ако Red Hat platform template \`postgresql-ephemeral\` липсва. Оригиналното упражнение с template остава като **опция C**, когато е достъпно.

**Резултат:** \`m10-postgres:5432\`, таблица \`short_links\`, Secret \`m10-db-url\` с \`DATABASE_URL\` за 10-D/10-E. Базата няма Route. **Тук не се използват външните исторически учебни images от Modules 01–07.**

## 1. Предпоставки и варианти

- Активен разрешен OpenShift Project и \`oc\` login, Bash, Python 3.10+, \`git\`. Работна директория: **коренът на Module 10**.
- Права за \`Deployment\`, \`Service\`, \`Secret\` и за избрания вариант също \`PVC\`. Няма нужда от \`cluster-admin\`, инсталиране на оператори или Docker build.
- Достъп на cluster node-овете до \`quay.io/sclorg/postgresql-16-c9s:20250214\`, image на [SCL.org за OpenShift](https://github.com/sclorg/postgresql-container). Ако image pull е забранен от платформата, не заобикаляй политиките.
- Собствените [postgres-ephemeral.yaml](../openshift/postgres-ephemeral.yaml) и [postgres-pvc.yaml](../openshift/postgres-pvc.yaml) манифести, [sql/init.sql](../sql/init.sql), \`tools/init_env.py\` и \`tools/prepare_oc.py\` са в репото.

| Вариант | Изискване | Съхранение | Подходящ за |
|---|---|---|---|
| **A — Deployment + PVC (препоръчан)** | Разрешен PVC и работещ default StorageClass или динамично provision-ване | 1Gi PVC, данните могат да преживеят Pod recreate | Постоянни връзки между Labs 10-C–E |
| **B — Deployment + emptyDir** | Само обичайни namespace права; не изисква PVC | Ефимерни данни; при Pod recreate се губят | Sandbox без StorageClass |
| **C — Red Hat template (оригиналният път)** | Наличен \`postgresql-ephemeral\` template и права за генерираните resources | Ефимерно | Упражняване на OpenShift Templates |

Не променяй режима в средата на упражнението върху съществуваща база — това може да изтрие данните или да остави несъвместими ресурси. **A или B е пълноценен OpenShift lab**, не заместител с локален Compose.

## 2. Preflight — права, имена, storage и template

От корена на Module 10:

\`\`\`bash
oc whoami
oc project
oc auth can-i create deployments.apps
oc auth can-i create services
oc auth can-i create secrets
oc auth can-i create persistentvolumeclaims
oc get deployment/m10-postgres service/m10-postgres pvc/m10-postgres-data \
  secret/m10-postgres-auth secret/m10-db-url 2>/dev/null || true
oc get dc/m10-postgres 2>/dev/null || true
oc get storageclass 2>/dev/null || true
oc get template postgresql-ephemeral -n openshift 2>/dev/null || true
\`\`\`

**Очаквано:** Deployment/Service/Secret permissions = \`yes\`, избраният Project е твой и няма предварително съществуващи чужди \`m10-*\` ресурси. Ако PVC е разрешен и има работещ default StorageClass, избери A; иначе B. Случаен StorageClass не е гарантиран и \`oc get storageclass\` може да върне \`Forbidden\`; това **не блокира B**. Само за C трябва да е наличен template. Ако имената съществуват и не са от твой предишен lab — **спри**.

## 3. Подготви credentials без пароли в Git или shell history

\`\`\`bash
python3 tools/init_env.py
python3 tools/prepare_oc.py
test -s .runtime/database.env
test -s .runtime/postgres.params
test -s .runtime/postgres-auth.env
stat -c '%a %n' .env .runtime/postgres.params .runtime/database.env .runtime/postgres-auth.env
\`\`\`

**Очаквано:** \`0600\` за всички файлове. \`postgres-auth.env\` има \`POSTGRESQL_USER\`, \`POSTGRESQL_DATABASE\`, \`POSTGRESQL_PASSWORD\`; \`database.env\` има \`DATABASE_URL=postgresql://shorties:...@m10-postgres:5432/shorties\`. Паролата не се отпечатва. \`.runtime/\` и \`.env\` са Git-ignored.

## 4. Създай PostgreSQL — избери САМО ЕДИН път

### A — Namespace Deployment + PVC

\`\`\`bash
oc create secret generic m10-postgres-auth --from-env-file=.runtime/postgres-auth.env
oc apply -f openshift/postgres-pvc.yaml
oc get pvc/m10-postgres-data
oc wait --for=jsonpath='{.status.phase}'=Bound pvc/m10-postgres-data --timeout=180s
oc rollout status deployment/m10-postgres --timeout=300s
oc get service/m10-postgres deployment/m10-postgres pvc/m10-postgres-data
\`\`\`

Ако PVC остава Pending, \`oc describe pvc/m10-postgres-data\` ще покаже storage quota, липсващ provisioner или StorageClass. **Не** сменяй на B чрез \`oc apply\` върху същия Deployment/PVC. Първо изтрий **само собствените** ресурси на lab-а (виж раздел 8), тогава стартирай B върху чиста среда. Recreate strategy е умишлена: не стартираме две PostgreSQL инстанции върху една data директория.

### B — Namespace Deployment + emptyDir

\`\`\`bash
oc create secret generic m10-postgres-auth --from-env-file=.runtime/postgres-auth.env
oc apply -f openshift/postgres-ephemeral.yaml
oc rollout status deployment/m10-postgres --timeout=300s
oc get service/m10-postgres deployment/m10-postgres
\`\`\`

**Очаквано:** един Ready PostgreSQL Pod и вътрешен Service на порт 5432. При нов Pod \`emptyDir\` се губи и таблицата трябва да се създаде повторно. Това е същото съзнателно ограничение като стария template.

### C — Оригинален OpenShift \`postgresql-ephemeral\` template

\`\`\`bash
oc get template postgresql-ephemeral -n openshift
oc process -n openshift postgresql-ephemeral --parameters
oc process -n openshift postgresql-ephemeral \
  --param-file=.runtime/postgres.params -o name
oc process -n openshift postgresql-ephemeral \
  --param-file=.runtime/postgres.params | oc apply -f -
oc get service/m10-postgres
\`\`\`

Прегледай действителния \`oc process ... -o name\` output и проследи създадения workload:

\`\`\`bash
oc get dc/m10-postgres 2>/dev/null || oc get deployment/m10-postgres
oc rollout status dc/m10-postgres --timeout=300s 2>/dev/null || \
  oc rollout status deployment/m10-postgres --timeout=300s
\`\`\`

Template параметрите и ресурсните kind-ове зависят от инсталацията — следвай **реалния** \`oc process\` изход. Ако template липсва, избери A или B; няма нужда да прекъсваш OpenShift учебната последователност.

## 5. Инициализирай SQL и провери действителната база

И трите пътя използват един и същ Service и следващите команди:

\`\`\`bash
oc get pods --show-labels
M10_DB_POD="$(oc get pods -l name=m10-postgres -o jsonpath='{.items[0].metadata.name}')"
test -n "$M10_DB_POD" || { echo 'Cannot find m10-postgres Pod — inspect labels'; false; }
oc exec -i "$M10_DB_POD" -- psql -U shorties -d shorties < sql/init.sql
oc exec "$M10_DB_POD" -- psql -U shorties -d shorties -c '\dt'
oc get endpoints m10-postgres
\`\`\`

Ако C template използва друг label, избери собственото DB Pod име от \`oc get pods --show-labels\` и задай \`M10_DB_POD\` ръчно; не копирай чуждо Pod име. **Очаквано:** таблица \`short_links\` с \`code\`, \`target_url\`, \`created_at\`, endpoint на 5432. SQL е идемпотентен. Наличен Deployment сам по себе си не доказва успешна SQL инициализация.

## 6. Secret за backend/redirector

\`\`\`bash
oc create secret generic m10-db-url --from-env-file=.runtime/database.env
oc get secret/m10-db-url
\`\`\`

Този Secret съдържа \`DATABASE_URL\`; Labs **10-D и 10-E** го подават с \`oc set env --from=secret/m10-db-url\`. Не излагай PostgreSQL чрез Route/NodePort и не печатай encoded Secret-а.

## 7. Troubleshooting

| Симптом | Проверка | Решение |
|---|---|---|
| Template NotFound | \`oc get template -n openshift postgresql-ephemeral\` | Използвай manifest A/B |
| PVC Pending | \`oc describe pvc m10-postgres-data\` | StorageClass/quota/permissions; след пълен cleanup избери B |
| Pod ImagePullBackOff | \`oc describe pod -l app=m10-postgres\` | Достъп до позволения публичен PostgreSQL registry; без заобикаляне на policy |
| CrashLoopBackOff | \`oc logs deploy/m10-postgres --previous\` | Secret ключове, image, writable volume и OpenShift SCC |
| Service без Endpoints | \`oc get pods -l app=m10-postgres; oc get endpoints m10-postgres\` | Провери Ready Pod и \`app=m10-postgres\` selector |
| Няма таблица | \`oc exec "$M10_DB_POD" -- psql -U shorties -d shorties -c '\dt'\` | Пусни \`sql/init.sql\` |
| \`m10-db-url\` exists | \`oc get secret m10-db-url\` | Не презаписвай чужди secrets |
| След restart няма данни | \`oc get pvc; oc describe pod\` | При B/C е очаквано; за A провери Bound PVC и дали е същият |

## 8. Cleanup и приемане

**Ако продължаваш към 10-D/10-E, НЕ изпълнявай cleanup тук.** За самостоятелния lab след потвърждение, че учебните данни не са необходими:

\`\`\`bash
oc delete deployment/m10-postgres service/m10-postgres --ignore-not-found
oc delete pvc/m10-postgres-data --ignore-not-found  # Изтрива persistent lab data при Delete reclaim!
oc delete secret/m10-postgres-auth secret/m10-db-url --ignore-not-found
# Само ако е създаден от template вариант C:
oc get dc/m10-postgres >/dev/null 2>&1 && oc delete dc/m10-postgres
\`\`\`

При вариант C може да има и други ресурси; сравни със запазения \`oc process ... -o name\` и изтрий **само собствените**. Не изтривай Project или чужди resources. Провери \`oc get deployment,dc,svc,pvc,secret\` и не трий други ресурси. Изтрий \`.runtime\` само ако съдържа единствено твоите лабораторни временни файлове.

**Приемане:** \`Service/m10-postgres\` на 5432, Ready PostgreSQL Pod, SQL \`short_links\` таблица, \`m10-db-url\` Secret, без публичен Route. При A имаш \`Bound\` PVC; при B е ясно, че данните са ефимерни. OpenShift упражнението се изпълнява **без задължителен platform template**.
