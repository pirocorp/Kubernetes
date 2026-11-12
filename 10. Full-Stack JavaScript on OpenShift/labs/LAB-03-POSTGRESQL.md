# Lab 10-C — PostgreSQL в OpenShift: template, Secret, SQL initialization и Service DNS

**Цел:** инстанцирай database в собствения OpenShift Project и я направи достъпна **само за вътрешни услуги**. Това следва [Red Hat — Deploy a database to OpenShift](https://developers.redhat.com/learning/learn:openshift:how-deploy-full-stack-javascript-applications-openshift/resource/resources:deploy-database-openshift), но използва **генерирана случайна парола вместо фиксираната демонстрационна парола от оригинала**.

## 1. Предпоставки

- `oc` CLI с login към собствен OpenShift Sandbox/Project; read access до template `postgresql-ephemeral` в namespace `openshift`.
- Namespace-scoped права за resource-ите, генерирани от template (обикновено DeploymentConfig, Service и евентуално Secret).
- Python >=3.10, Bash и файловете [sql/init.sql](../sql/init.sql), [tools/init_env.py](../tools/init_env.py), [tools/prepare_oc.py](../tools/prepare_oc.py).
- Работна директория **коренът на Module 10**. Не е нужно да си изпълнил Lab 10-A или 10-B. Не се изисква локален PostgreSQL/Node.js.
- Template е **условна platform prerequisite**: не всички версии/инсталации на OpenShift предлагат `postgresql-ephemeral`. Ако липсва, **не** търси случаен чужд image или cluster-admin privileges. Изпълни напълно функционалния Docker Compose Lab 10-A, а OpenShift пътя маркирай като инфраструктурно недостъпен.

## 2. Preflight — установи дали template действително е наличен

```bash
oc whoami
oc project
oc get template -n openshift postgresql-ephemeral
oc describe template -n openshift postgresql-ephemeral
oc auth can-i create deploymentconfigs.apps.openshift.io
oc auth can-i create services
oc get dc/m10-postgres svc/m10-postgres 2>/dev/null || true
```

**Очаквано:** template е наличен и избраният Project е твой. Използвай `oc process -n openshift postgresql-ephemeral --parameters`, за да видиш точния списък параметри, валиден в твоя cluster. Ако `can-i` е `no`, lab-ът е блокиран по RBAC и не трябва да заобикаляш политиките.

**Какво е template?** Това е параметризирана конфигурация на OpenShift, която генерира Kubernetes/OpenShift resources. Нито template, нито Project сами по себе си гарантират постоянна база. `postgresql-ephemeral` има **ефимерно хранилище** — при пресъздаване на Pod данните могат да се загубят. Не използвай такъв deployment за production.

## 3. Генерирай credentials, без да ги commit-ваш

```bash
python3 tools/init_env.py
python3 tools/prepare_oc.py
ls -l .env .runtime/postgres.params .runtime/database.env
```

**Очаквано:** файловете са с разрешения `0600`. `.runtime/postgres.params` съдържа `DATABASE_SERVICE_NAME=m10-postgres`, `POSTGRESQL_USER=shorties`, `POSTGRESQL_DATABASE=shorties` и случайно генериран password; `.runtime/database.env` съдържа вътрешния `DATABASE_URL`. Паролите **не се отпечатват** и файловете са Git-ignored.

Внимавай: в предишни Red Hat примери паролата се показва директно в командния ред. Тук умишлено използваме env/param file и `Secret`, за да не остава в shell history.

## 4. Създай базата от реалния template

```bash
oc process -n openshift postgresql-ephemeral \
  --param-file=.runtime/postgres.params -o name
oc process -n openshift postgresql-ephemeral \
  --param-file=.runtime/postgres.params | oc apply -f -
oc get svc/m10-postgres dc/m10-postgres
oc rollout status dc/m10-postgres --timeout=300s
```

**Очаквано:** Service `m10-postgres` на PostgreSQL порт 5432 и Ready database Pod от `DeploymentConfig`. Ако template генерира `Deployment` вместо `DeploymentConfig` в твоя cluster, виж resource types от `oc process ... -o name` и използвай реалния kind; не гадай името/спецификата на платформата.

**Service discovery:** backend може да използва `m10-postgres:5432` без host IP и без публичен Route. В Kubernetes DNS името се резолвира в ClusterIP endpoint. **Не излагай PostgreSQL чрез Route или публичен LoadBalancer**.

## 5. Създай таблицата от предоставения SQL file

Установи действителния Pod; template обикновено използва label `name=m10-postgres`, но провери с `oc get pods --show-labels`:

```bash
oc get pods --show-labels
M10_DB_POD="$(oc get pods -l name=m10-postgres -o jsonpath='{.items[0].metadata.name}')"
test -n "$M10_DB_POD" || { echo 'Cannot find database Pod; inspect labels'; false; }
oc exec -i "$M10_DB_POD" -- psql -U shorties -d shorties < sql/init.sql
oc exec "$M10_DB_POD" -- psql -U shorties -d shorties -c '\dt'
```

**Очаквано:** таблица `short_links`, PK `code`, `target_url` и `created_at`. SQL е **идемпотентен** чрез `CREATE TABLE IF NOT EXISTS`. Ако `psql` липсва в контейнера, template image не отговаря на описаната конфигурация — не продължавай към backend, докато DB не е подготвена.

## 6. Създай собствен Secret за приложенията

```bash
oc create secret generic m10-db-url --from-env-file=.runtime/database.env
oc get secret/m10-db-url
```

**Очаквано:** Secret с ключ `DATABASE_URL`. В следващите Labs 10-D и 10-E го добавяме към Deployment-ите чрез `oc set env ... --from=secret/m10-db-url`; не поставяме connection string в Docker image, README или Git.

## 7. Troubleshooting

| Симптом | Проверка | Решение |
|---|---|---|
| Template NotFound | `oc get templates -n openshift` | Не е наличен — използвай локалния Compose път |
| `oc process` отхвърля параметър | `oc process ... --parameters` | Съобрази имената с реалния template |
| Forbidden | `oc auth can-i ...` | Нямаш права; не изисквай cluster-admin за demo |
| DB Pod не е Ready | `oc describe pod` / logs | ImagePull, quota, resources |
| Таблица липсва | `oc exec ... psql ... '\dt'` | Подай `sql/init.sql` |
| Няма m10-postgres Service | `oc get svc` | Провери template параметъра DATABASE_SERVICE_NAME |
| `Secret already exists` | `oc get secret m10-db-url` | Не презаписвай чужд Secret |

## 8. Cleanup и приемане

Ако продължаваш към 10-D и 10-E, **остави** PostgreSQL и Secret работещи. За самостоятелен lab:

```bash
oc delete secret/m10-db-url --ignore-not-found
oc delete dc/m10-postgres svc/m10-postgres --ignore-not-found
```

Ако template е създал други objects, виж точния списък от `oc process ... -o name` и премахни **само своите** ресурси. Ефимерните DB данни могат да изчезнат след изтриване; не използвай production информация.

**Приемане:** PostgreSQL е стартирана от template, SQL таблицата съществува, има вътрешен Service и Secret, и никакъв database endpoint не е публичен.
