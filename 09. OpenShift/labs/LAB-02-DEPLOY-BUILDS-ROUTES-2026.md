# Lab 09-B — Deployment, S2I Build, Route, Scaling & Monitoring (2026)

> **Пълно, самодостатъчно упражнение за Red Hat Developer Sandbox.** Не изисква cluster-admin, нов Project или собствен kubeadm cluster. Изпълни в личния Sandbox Project с `oc` + Bash. Ориентировъчно 60–90 минути. Проверка: **само статична**; runtime не е изпълняван.
>
> **Оригиналите на Red Hat:** [Foundations](https://developers.redhat.com/learn/openshift/foundations-openshift), [Git през Console](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:install-application-source-code-github-repository-using-openshift-web-console), [Image чрез oc](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:install-application-linux-container-image-using-oc-cli-tool), [Source чрез oc](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:install-application-source-code-using-oc-cli-tool), [GUI scaling](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:scale-applications-using-openshift-web-console), [CLI scaling](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:scale-applications-using-oc-cli-tool) и [Metrics](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:view-performance-information-using-openshift-web-console).

## 1. Preflight

Ползвай Sandbox от [Red Hat](https://developers.redhat.com/developer-sandbox). Първо изпълни [Lab 09-A](./LAB-01-SANDBOX-CLI-2026.md) за безопасен login с изолиран KUBECONFIG. Тук следва **пълен self-contained source setup**; при изолирана среда без Git repo, файловете са дадени по-долу. Нужни са работещи `oc`, `curl`, Bash, достъп към публичния UBI registry и Python package index от cluster Builds. Използваните image tags са `ubi9/httpd-24:latest` и `ubi9/python-312:latest`: Python 3.12 е фиксиран на minor ниво, но tags **не са immutable digests**, затова при execution записвай разрешения digest и не твърдиш production pin.

```bash
oc whoami
oc project
oc version
oc auth can-i create deployments.apps
oc auth can-i create services
oc auth can-i create routes.route.openshift.io
oc auth can-i create buildconfigs.build.openshift.io
oc get deployment,svc,route,cm,bc,is
mkdir -p lab09b/source
cd lab09b
```

**Очаквано:** валиден собствен Project; create permissions = `yes`. Ако BuildConfig е забранен, изпълни само B1 и отбележи B2 като блокиран от разрешенията. **Не** ползвай `oc adm policy add-scc-to-user`. Имената `m09-*` трябва да са свободни.

## 2. B1 — Deployment директно от готов image

**Какво учим:** образът не е Build; Deployment управлява Pods, Service избира Pods, Route публикува Service. Red Hat [UBI9 httpd-24](https://catalog.redhat.com/en/software/containers/ubi9/httpd-24/61a60c3e3e9240fca360f74a) използва HTTP port 8080 и е предназначен за unprivileged контейнер.

### 2.1. Подготви собствен HTML и ConfigMap

```bash
cat > index.html <<'EOF'
<!doctype html>
<html lang="bg"><meta charset="utf-8">
<title>OpenShift Module 09</title>
<h1>OpenShift image deployment - module 09</h1>
<p>Apache HTTPD in a Kubernetes Deployment.</p>
</html>
EOF
oc create configmap m09-html --from-file=index.html
```

### 2.2. Файл image.yaml — копирай съдържанието точно

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: m09-image
  labels:
    lab: module09b
spec:
  replicas: 1
  selector:
    matchLabels: {app: m09-image}
  template:
    metadata:
      labels: {app: m09-image}
    spec:
      containers:
      - name: httpd
        image: registry.access.redhat.com/ubi9/httpd-24:latest
        ports:
        - {name: http, containerPort: 8080}
        volumeMounts:
        - {name: page, mountPath: /var/www/html/index.html, subPath: index.html, readOnly: true}
        readinessProbe:
          httpGet: {path: /, port: http}
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests: {cpu: 50m, memory: 128Mi}
          limits: {cpu: 300m, memory: 512Mi}
      volumes:
      - name: page
        configMap: {name: m09-html}
---
apiVersion: v1
kind: Service
metadata:
  name: m09-image
spec:
  type: ClusterIP
  selector: {app: m09-image}
  ports:
  - {name: http, port: 8080, targetPort: http}
```

Създай локален файл с име `image.yaml` и горното YAML съдържание; не са нужни други файлове.

```bash
oc apply --dry-run=client -f image.yaml
oc apply -f image.yaml
oc rollout status deploy/m09-image --timeout=180s
oc create route edge m09-image --service=m09-image --port=http --insecure-policy=Redirect
oc get deployment/m09-image service/m09-image route/m09-image
oc get endpointslice -l kubernetes.io/service-name=m09-image
IMAGE_HOST="$(oc get route m09-image -o jsonpath='{.spec.host}')"
curl -fsS "https://$IMAGE_HOST/" | grep 'OpenShift image deployment'
```

**Очаквано:** 1 Ready replica, един Service с endpoint, Route с HTTPS URL и HTML с очаквания текст. `HTTP 503` → `oc describe pod -l app=m09-image`, `oc get endpointslice...`; `404` → `oc logs deploy/m09-image` и `ConfigMap` mount; `ImagePullBackOff` → registry достъп. При отказ за Route може временно `oc port-forward svc/m09-image 18080:8080` и локален `curl http://localhost:18080`, но това **не доказва Route**.

## 3. B2 — Build от локален Python 3.12 source (S2I)

**Защо:** старото упражнение използва Ruby 2.2/CentOS 7. Вместо това създаваме Flask приложение от включен тук source, без непиннат чужд repository. Python builder [UBI9 Python 3.12](https://catalog.redhat.com/en/software/containers/rhel9/python-312/657b088123df896ebfacf1f0) има S2I workflow.

### 3.1. Пълни source files

```bash
cat > source/requirements.txt <<'EOF'
Flask==3.1.2
gunicorn==23.0.0
EOF
cat > source/app.py <<'PY'
import os
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.get("/")
def index():
    return jsonify(service="m09-source", version=os.getenv("APP_VERSION", "v1"))

@app.get("/healthz")
def healthz():
    return "ok\n"

@app.get("/echo")
def echo():
    return jsonify(message=request.args.get("message", ""))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
PY
```

### 3.2. S2I build, image stream и app

```bash
oc import-image m09-python-312 --from=registry.access.redhat.com/ubi9/python-312:latest --confirm
oc get istag m09-python-312:latest -o jsonpath='{.image.dockerImageReference}{"\n"}'
oc new-build --name=m09-source --binary --strategy=source --image-stream=m09-python-312:latest
oc start-build m09-source --from-dir=source --follow --wait
oc get builds
oc get imagestream m09-source
oc new-app --image-stream=m09-source:latest --name=m09-source
oc set env deployment/m09-source APP_MODULE=app:app APP_VERSION=v1
oc rollout status deployment/m09-source --timeout=240s
oc get svc m09-source -o yaml
```

**Очаквано:** Build phase `Complete`, ImageStream `m09-source:latest`, Deployment Ready, Service на **8080**. Ако генерираният Service има различен port/name, използвай реалния `Service.spec.ports` вместо да копираш на сляпо последващия Route command.

```bash
oc create route edge m09-source --service=m09-source --port=8080 --insecure-policy=Redirect
SOURCE_HOST="$(oc get route m09-source -o jsonpath='{.spec.host}')"
curl -fsS "https://$SOURCE_HOST/healthz"
curl -fsS "https://$SOURCE_HOST/"
curl -fsS "https://$SOURCE_HOST/echo?message=hello"
oc logs deployment/m09-source --tail=30
```

**Очаквано:** `ok`, JSON с `"version":"v1"` и JSON с `"message":"hello"`. Ако build fail-не, използвай `oc get builds` и `oc logs build/ИМЕ_ОТ_СПИСЪКА`; ако приложението не стартира, провери `APP_MODULE` и Flask/gunicorn installation logs.

### 3.3. Същият код от Git през Web Console (пълно упражнение)

За да покрием и оригиналния урок **Import from Git**, същият source е включен като реални файлове **в настоящото GitHub repository**:
- [app.py](./examples/python-hello/app.py)
- [requirements.txt](./examples/python-hello/requirements.txt)
- [.s2i/environment](./examples/python-hello/.s2i/environment)

**След като PR с този lab бъде слят в main** (преди това линкът към main няма файловете), отвори Red Hat Sandbox Web Console и:
1. Избери личния Project → **+Add / Import from Git** или съответния source-to-image wizard.
2. Git URL: `https://github.com/pirocorp/Kubernetes.git`; Git reference **main** (за възпроизводимост на конкретен момент използвай SHA на merge commit вместо подвижен main, ако интерфейсът предлага Git reference).
3. Context directory: `09. OpenShift/labs/examples/python-hello` (интервалът в името на parent folder е част от пътя).
4. Builder: избери **Python 3.12 / UBI9** ако е наличен; не избирай исторически Python 3.9 / UBI8 или Ruby 2.2. Ако такъв builder **липсва** в каталога, първо провери наличните builder images; Binary S2I B2 остава изпълнимият основен път.
5. Name/label: `m09-git`; Resource type: **Deployment** (не DeploymentConfig); Route: **Enabled**; Create.
6. Намери Build и прегледай log до **Complete**; виж `oc get bc,is,deploy,svc,route` и `oc rollout status deploy/m09-git --timeout=240s`.
7. Намери Route hostname: `oc get route m09-git -o jsonpath='{.spec.host}'`. В браузър посети `https://HOST/healthz`; очаква се `ok`. Ако Route не е генериран, създай го с реалния Service port.
8. Cleanup: `oc delete route/m09-git deploy/m09-git svc/m09-git bc/m09-git is/m09-git --ignore-not-found`, проверявай и други обекти, създадени от wizard, преди да изтриваш.

**Обяснение:** Git S2I и Binary S2I произвеждат еднакъв клас image, но първият клонира source от Git, а вторият качва локална директория. При UI различия ползвай реалните полета `Git Repo URL / Context Dir / Builder / Name / Deployment / Route` — не се доверявай на снимка от 2023 г.

## 4. B3 — Scaling, rolling update и metrics

```bash
oc scale deploy/m09-source --replicas=2
oc rollout status deploy/m09-source --timeout=240s
oc get deploy m09-source -o jsonpath='{.status.readyReplicas}{" / "}{.spec.replicas}{"\n"}'
oc get pods -l app=m09-source -o wide
oc get endpointslice -l kubernetes.io/service-name=m09-source
```

**Очаквано:** `2 / 2` и 2 endpoints, ако quotas позволяват. В Web Console → Deployment → `m09-source` → Replicas редактирай **3** (само при достатъчна quota) и виж промяната с `oc get deploy`. После върни 2. При `Pending` смъкни replicas на 1 и виж events/resourcequota; това е shared sandbox.

```bash
oc scale deploy/m09-source --replicas=2
oc set env deploy/m09-source APP_VERSION=v2
oc rollout status deploy/m09-source --timeout=240s
curl -fsS "https://$SOURCE_HOST/" | grep '"version":"v2"'
oc rollout history deploy/m09-source
oc rollout undo deploy/m09-source
oc rollout status deploy/m09-source --timeout=240s
curl -fsS "https://$SOURCE_HOST/" | grep '"version":"v1"'
oc get events --sort-by=.lastTimestamp
oc top pods
oc get hpa
```

**Очаквано:** v2, после v1; `oc top pods` връща метрики **само ако** Metrics API/rights са налични. HPA може да липсва — **ръчното scaling не е HPA**. Web Console → Pods/Builds/Topology/Events/Metrics дава същите наблюдения; UI layout е версия-зависим.

## 5. Common failures

| Симптом | Провери | Не прави |
|---|---|---|
| `Forbidden` create Route/BuildConfig | `oc auth can-i create ...` | Не давай cluster-admin |
| Build Failed/Pending | `oc get builds`, `oc logs build/ИМЕ`, quota, egress | Не заменяй library с непроверен tag |
| ImagePullBackOff | `oc describe pod`, registry CA/DNS | Не използвай непознат root-only image |
| CrashLoopBackOff | `oc logs deploy/...`, `APP_MODULE`, port, mount | Не отменяй SCC |
| HTTPS 503 | Service selector, EndpointSlices, Ready Pods | Не търси Route порт на случаен принцип |
| metrics unavailable | `oc top pods`, права, UI | Не инсталирай monitoring operator |
| Not enough CPU/memory for 2–3 replicas | `oc describe pod`, `oc get resourcequota` | Върни count 1 |

## 6. Cleanup (само личните ресурси от този lab)

```bash
oc delete route/m09-image route/m09-source --ignore-not-found
oc delete deployment/m09-image deployment/m09-source --ignore-not-found
oc delete service/m09-image service/m09-source --ignore-not-found
oc delete configmap/m09-html --ignore-not-found
oc delete buildconfig/m09-source --ignore-not-found
oc delete imagestream/m09-source imagestream/m09-python-312 --ignore-not-found
oc get builds -l buildconfig=m09-source
oc get deploy,svc,route,bc,is,cm
cd ..
```

Ако има останали build records, премахни **само** имената от `oc get builds -l buildconfig=m09-source` (не изтривай всички Builds). Локалната директория `lab09b/` съдържа само тези source files и може да се изтрие след проверка на `pwd`. **Не** изтривай Project, чужди приложения или стандартния kubeconfig.

## 7. Acceptance criteria / version scope

- [ ] Изпълнен HTTPD Deployment с ConfigMap, Service и работещ HTTPS Route.
- [ ] Създаден Python source code, S2I BuildConfig и успешен Build/ImageStream.
- [ ] JSON от `/healthz`, `/` и `/echo`.
- [ ] GUI/CLI scaling до 2 (3 опционално), environment rolling update v1→v2→rollback.
- [ ] Проверени Pods, Service endpoints, Build logs и наличните metrics.
- [ ] Пълно премахване само на създадените lab resources.

**API:** `apps/v1` Deployment, `v1` Service/ConfigMap, OpenShift `route.openshift.io/v1` и `build.openshift.io/v1`. Приложението работи в проект на Sandbox, **не** на kubeadm+Calico cluster. **Потенциална външна нестабилност:** pull от registry, Python packages и Sandbox build quota. Статичният audit не доказва live compatibility; няма гаранция, че current Sandbox предлага BuildConfig permissions.
