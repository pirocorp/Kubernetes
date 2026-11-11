# Lab 09-C — MariaDB, Secrets, PVC, failure/recovery (2026)

> **Самодостатъчен lab:** 45–60 минути, **само в личния Red Hat Developer Sandbox Project**, Bash + `oc`. Създава собствена база с **непродукционни данни**. Изисква динамично provisioning StorageClass и право за PVC/Deployment/Service/Secret.
>
> **Оригинални уроци:** [Foundations: Databases using oc](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:work-databases-openshift-using-oc-cli-tool), [Foundations: Databases using Web Console](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:work-databases-openshift-web-console); [Kubernetes Sandbox: MariaDB](https://developers.redhat.com/learning/learn:openshift:learn-kubernetes-using-developer-sandbox/resource/resources:create-and-populate-database-mariadb).
>
> **Корекции:** не използваме `mariadb:latest` image, root password `admin`, base64 demo Secret, PVC от 5 GiB без проверка на quota или `kubectl delete all` като cleanup. Вместо това използваме [SCLorg MariaDB 10.11 CentOS Stream 9](https://github.com/sclorg/mariadb-container) image, проектиран за OpenShift с arbitrary UIDs, и 1Gi PVC. Tag `latest` е подвижен на patch ниво — при използване в production се pin-ва immutable digest.

## 1. Preflight

Активен [Red Hat Developer Sandbox](https://developers.redhat.com/developer-sandbox), личен Project, `oc` от конзолата (същия cluster), Bash, `git` и `openssl`. Не използвай Cluster Setup кластер от Modules 00–08.

```bash
oc whoami
oc project
oc version
oc auth can-i create persistentvolumeclaims
oc auth can-i create secrets
oc auth can-i create deployments.apps
oc auth can-i create services
oc get storageclass
oc get resourcequota
oc get deploy/m09-db pvc/m09-db-data secret/m09-db-creds 2>/dev/null || true
git clone --depth=1 https://github.com/pirocorp/Kubernetes.git m09-course
export M09_MARIADB_DIR="$PWD/m09-course/09. OpenShift/labs/examples/mariadb"
test -s "$M09_MARIADB_DIR/db.yaml"
test -s "$M09_MARIADB_DIR/seed.sql"
cp "$M09_MARIADB_DIR/db.yaml" ./db.yaml
```

**Очаквано:** правата са `yes`, има подходящ **default StorageClass** или явен препоръчан StorageClass. Ако не е дефиниран default, **не** прилагай PVC преди да зададеш правилния `storageClassName` в следващия YAML (вземи го от администраторската конфигурация). **Ако имената са заети от чуждо упражнение, спри.**

## 2. Създай Secret без hardcoded пароль в Git

Тази последователност **не** записва plaintext password в command history, repo или YAML. Secret остава в OpenShift и се защитава с RBAC, но **base64 не е шифроване**. Не публикувай `oc get secret -o yaml` в споделени документи, логове или screenshots.

```bash
umask 077
DB_CREDS_FILE="$(mktemp)"
printf 'MYSQL_USER=quotes\nMYSQL_DATABASE=quotesdb\n' > "$DB_CREDS_FILE"
printf 'MYSQL_PASSWORD=%s\n' "$(openssl rand -hex 24)" >> "$DB_CREDS_FILE"
oc create secret generic m09-db-creds --from-env-file="$DB_CREDS_FILE"
rm -f -- "$DB_CREDS_FILE"
unset DB_CREDS_FILE
oc get secret m09-db-creds -o jsonpath='{.metadata.name}{"\n"}'
```

**Очаквано:** `m09-db-creds` е създаден, но паролата никъде не се отпечатва. Изпълни командите в една сесия. Ако `oc create secret` не успее, изтрий **само** временния файл чрез `rm -f "$DB_CREDS_FILE"` преди повторение.

## 3. Пълен манифест — db.yaml

**Готов файл:** [db.yaml](./examples/mariadb/db.yaml) вече е включен в хранилището. Командите в preflight го копират в работната директория, така че **не е необходимо да преписваш YAML на ръка**. Съдържанието му е:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: m09-db-data
  labels: {lab: module09c}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: m09-db
  labels: {lab: module09c}
spec:
  replicas: 1
  strategy:
    type: Recreate
  selector:
    matchLabels: {app: m09-db}
  template:
    metadata:
      labels: {app: m09-db, lab: module09c}
    spec:
      containers:
      - name: mariadb
        image: quay.io/sclorg/mariadb-1011-c9s:latest
        imagePullPolicy: IfNotPresent
        env:
        - name: MYSQL_USER
          valueFrom: {secretKeyRef: {name: m09-db-creds, key: MYSQL_USER}}
        - name: MYSQL_PASSWORD
          valueFrom: {secretKeyRef: {name: m09-db-creds, key: MYSQL_PASSWORD}}
        - name: MYSQL_DATABASE
          valueFrom: {secretKeyRef: {name: m09-db-creds, key: MYSQL_DATABASE}}
        ports:
        - {name: mysql, containerPort: 3306}
        volumeMounts:
        - {name: data, mountPath: /var/lib/mysql/data}
        startupProbe:
          tcpSocket: {port: mysql}
          failureThreshold: 30
          periodSeconds: 5
        readinessProbe:
          tcpSocket: {port: mysql}
          periodSeconds: 5
        resources:
          requests: {cpu: 100m, memory: 256Mi}
          limits: {cpu: 750m, memory: 1Gi}
      volumes:
      - name: data
        persistentVolumeClaim: {claimName: m09-db-data}
---
apiVersion: v1
kind: Service
metadata:
  name: m09-db
  labels: {lab: module09c}
spec:
  selector: {app: m09-db}
  type: ClusterIP
  ports:
    - {name: mysql, port: 3306, targetPort: mysql}
```

**Смисъл:** PVC е отделен от Pod, а Deployment е с `Recreate`, за да избегнем едновременно стартиране на две MariaDB instances върху една filesystem data directory. Това е **учебно single-instance решение**, не HA database архитектура.

## 4. Deployment — избери един от двата начина

И двата метода използват **същия** [db.yaml](./examples/mariadb/db.yaml) и вече създадения Secret `m09-db-creds`. **Изпълни само един метод**, а после общите проверки в 4.3.

### 4.1. Метод A — чрез `oc` CLI (препоръчван)

```bash
oc apply --dry-run=client -f db.yaml
oc apply -f db.yaml
```

### 4.2. Метод B — чрез OpenShift Web Console

1. Провери, че Secret `m09-db-creds` е създаден от раздел 2.
2. В личния Project отвори **+Add → Import YAML** (или съответния YAML editor в наличната версия).
3. Отвори [db.yaml](./examples/mariadb/db.yaml), постави **целия файл** и избери **Create**. YAML не съдържа пароли.
4. В **Workloads → Deployments** потърси `m09-db`; в **Storage → PersistentVolumeClaims** — `m09-db-data`.
5. Ако липсва Import YAML в дадена конзола, изпълни Метод A. **Не** създавай втори DB deployment със същите или други имена.

### 4.3. Общи проверки

```bash
oc get pvc m09-db-data
oc rollout status deployment/m09-db --timeout=300s
oc get pods -l app=m09-db
oc get service m09-db
oc get endpointslice -l kubernetes.io/service-name=m09-db
oc logs deployment/m09-db --tail=50
```

**Очаквано:** PVC `Bound`, 1/1 DB Pod Ready, endpoint за TCP 3306 и успешна MariaDB initialization в логовете. Ако PVC е `Pending`, виж `oc describe pvc m09-db-data`; ако image не се изтегли, `oc describe pod -l app=m09-db`. Ако SCC или filesystem permissions откажат достъп, **не** пускай DB като root — установи дали image и StorageClass поддържат arbitrary UIDs.

## 5. SQL schema и реална заявка

Изпълни готовия [seed.sql](./examples/mariadb/seed.sql) през CLI **вътре в DB Pod**; паролата се чете от environment конфигурацията на контейнера, а не от локалния shell. Не добавяй публична Route към база данни.

```bash
oc exec -i deployment/m09-db -- bash -lc \
  'exec mariadb -h 127.0.0.1 -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' \
  < "$M09_MARIADB_DIR/seed.sql"
```

**Очаквано:** таблица с 3 реда. **Не** приемай само `Deployment Ready` за доказателство, че данните са правилно записани. За GUI: в Web Console разгледай Deployment `m09-db`, Pod logs, PVC и Service; **не** показвай Secret values. За наблюдение на данните може да използваш Pod terminal със същите SQL команди, ако платформата го позволява.

## 6. Failure/recovery: Delete Pod, не PVC

```bash
OLD_DB_POD="$(oc get pods -l app=m09-db -o jsonpath='{.items[0].metadata.name}')"
test -n "$OLD_DB_POD"
oc delete pod "$OLD_DB_POD"
oc rollout status deployment/m09-db --timeout=300s
oc wait --for=condition=Ready pod -l app=m09-db --timeout=300s
oc get pods -l app=m09-db
oc get pvc m09-db-data
oc exec deployment/m09-db -- bash -lc 'mariadb -h 127.0.0.1 -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "SELECT COUNT(*) AS rows_after_recovery FROM quotes;"'
```

**Очаквано:** нов Pod name, същият PVC `Bound` и стойност 3 след рестарта. **Пазенето на данните не е гарантирано от самия Deployment** — PVC изисква persistent backing store. Recovery може да се забави от topology/volume attach или sandbox quota. Ако вече е изтекла 30-дневната среда, не приемай persistence.

## 7. Troubleshooting

| Симптом | Диагноза | Следващо действие |
|---|---|---|
| `PVC Pending` | Липса на default StorageClass/quota | `oc describe pvc m09-db-data`; storage permissions |
| Pod `CrashLoopBackOff` | Init/volume/secret проблем | `oc logs deploy/m09-db --previous`; `oc describe pod` |
| MariaDB `Access denied` | Wrong Secret keys или DB init state | `oc describe deploy m09-db` и non-secret env key names; **не печатай стойностите** |
| `Table doesn't exist` | Seed SQL не е изпълнен | Повтори първата SQL команда |
| Pod recreated, данните липсват | Грешен mount, изтрит PVC, нова DB init | `oc get pvc` и logs; не твърди data protection |
| DB Service no endpoints | Pod не е Ready / selectors | `oc get endpointslice ...`, `oc get pods --show-labels` |
| Secret values изтекли в logs | Секретен инцидент | Ротирай паролата/creds; не комитвай |

## 8. Cleanup — данните се изтриват

**Предупреждение:** следващите команди изтриват **учебната** database и PVC. Не ги изпълнявай върху production данни. При StorageClass reclaim policy `Retain` може да се наложи администраторска грижа за останал PV.

```bash
oc delete deployment/m09-db --ignore-not-found
oc delete service/m09-db --ignore-not-found
oc delete pvc/m09-db-data --ignore-not-found
oc delete secret/m09-db-creds --ignore-not-found
oc get deploy,svc,pvc,secret
```

Изтрий локалните `db.yaml` и `m09-course/` **само ако** са създадени чрез стъпките по-горе и не съдържат други твои файлове. Не трий целия Project, не премахвай други PVC или Secrets.

## 9. Критерии за приемане

- [ ] Обясняваш защо Secret (и base64 ≠ encryption) е по-добър от фиксирана парола в Git.
- [ ] PVC Bound, Pod Ready, Service 3306, 3 SQL реда.
- [ ] След Pod deletion: нов Pod, същите SQL данни.
- [ ] Не използваш root-only image, hostPath, cluster-admin или публична Route за DB.
- [ ] Cleanup изтрива **само** собствените objects и storage.

**API:** `v1` PVC/Secret/Service, `apps/v1` Deployment; MariaDB 10.11 image family, dynamic PVC StorageClass от Sandbox. Това не е резервно копие на DB или production HA configuration. Версиите и upstream registry достъп се проверяват на датата на изпълнение.
