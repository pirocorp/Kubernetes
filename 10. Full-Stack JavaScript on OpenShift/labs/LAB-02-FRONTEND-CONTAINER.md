# Lab 10-B — Frontend: локален image, registry и OpenShift Route

**Цел:** прехвърли същия frontend от локална Node среда в OpenShift чрез container image. Източник: [Red Hat — Run locally, build and deploy frontend](https://developers.redhat.com/learning/learn:openshift:how-deploy-full-stack-javascript-applications-openshift/resource/resources:run-application-locally-then-build-container-front-end-and-deploy-it-openshift).

## 1. Предпоставки

- Личен/разрешен OpenShift Project и `oc login` (виж [Module 09](../../09.%20OpenShift/README.md)).
- `oc` CLI, Git, Bash; за **локално build + push към registry** — Podman, registry account и разрешено image pull от cluster.
- Възможност за **namespace-scoped Docker-strategy binary build** в OpenShift — това е **основният безплатен път** на този lab, който не изисква външен registry account.
- Права за BuildConfig, ImageStream, Deployment, Service и Route; свободни имена `m10-frontend` в собствения Project.
- Всички файлове са предоставени в [src/frontend](../src/frontend/server.mjs) — Node server, HTML, JS, CSS, Dockerfile, package.json. Работна директория = корен на Module 10.

## 2. Preflight

```bash
oc whoami
oc project
oc auth can-i create buildconfigs.build.openshift.io
oc auth can-i create builds.build.openshift.io
oc auth can-i create imagestreams.image.openshift.io
oc auth can-i create deployments.apps
oc auth can-i create routes.route.openshift.io
oc get deployment/m10-frontend service/m10-frontend route/m10-frontend 2>/dev/null || true
test -s src/frontend/Dockerfile
```

**Очаквано:** всички `can-i` са `yes`, избран е собственият namespace и няма чужди `m10-frontend` ресурси. Ако няма build права, не заобикаляй quota/SCC; използвай локалния Lab 10-A.

## 3. Основен път: построи frontend image в OpenShift

```bash
oc new-build --name=m10-frontend --binary --strategy=docker
oc start-build m10-frontend --from-dir=src/frontend --follow --wait
oc get builds -l buildconfig=m10-frontend
oc get imagestream/m10-frontend
```

**Очаквано:** build завършва `Complete`, образът е наличен в собствения ImageStream. `src/frontend/Dockerfile` използва Node.js 22 и unprivileged runtime UID. Backend, redirector и database **не са необходими за старта на frontend**.

```bash
oc new-app --name=m10-frontend --image-stream=m10-frontend:latest
oc rollout status deployment/m10-frontend --timeout=300s
oc get service/m10-frontend
oc apply -f openshift/frontend-route.yaml
M10_ROUTE="$(oc get route m10-frontend -o jsonpath='{.spec.host}')"
test -n "$M10_ROUTE"
curl -fsS "https://$M10_ROUTE/healthz"
curl -fsS "https://$M10_ROUTE/" | head -c 300
```

**Очаквано:** HTTPS Route и `ok` от /healthz; HTML с Shorties. UI се зарежда, но **System health показва backend/database/redirector unavailable** — те се внедряват в следващите labs. Това не е грешка.

**Защо HTTPS edge Route, а не `oc expose` с plain HTTP?** За browser-facing service предпочитаме TLS termination и redirect от insecure HTTP. [frontend-route.yaml](../openshift/frontend-route.yaml) съдържа точната конфигурация; не добавяй фиктивен hostname.

## 4. Допълнителен Red Hat път: Podman → Quay.io → OpenShift

Това възпроизвежда оригиналната идея за **локално компилиран image, качен в registry, после изтеглен от OpenShift**. Не е задължително за изпълнение на курса. Използвай **своя registry акаунт**, не чужд image или credentials:

```bash
podman --version
read -r -p "Your Quay.io namespace: " M10_QUAY_NAMESPACE
test -n "$M10_QUAY_NAMESPACE"
podman build -t "quay.io/$M10_QUAY_NAMESPACE/m10-shorties-front:1" src/frontend
podman login quay.io
podman push "quay.io/$M10_QUAY_NAMESPACE/m10-shorties-front:1"
```

Ако image е публичен или е конфигуриран pull secret, той може да се използва от OpenShift. Ако вече имаш Deployment от раздел 3, **не създавай второ приложение със същото име**; избери едната доставка:

```bash
oc set image deployment/m10-frontend \
  "m10-frontend=quay.io/$M10_QUAY_NAMESPACE/m10-shorties-front:1"
oc rollout status deployment/m10-frontend --timeout=300s
```

Ако контейнерът в deployment не се казва `m10-frontend`, провери `oc get deploy/m10-frontend -o yaml` и използвай действителното container name. При private Quay image трябва да добавиш **собствен** OpenShift pull secret — не поставяй пароли в Git.

## 5. Проверки и диагностика

```bash
oc get deploy,svc,route -l app=m10-frontend
oc get pod -l deployment=m10-frontend
oc logs deployment/m10-frontend --tail=60
oc describe deployment/m10-frontend
```

**Очаквано:** `1/1 Ready` (при quota и network), Service на 8080, Route с TLS и HTTP 200. Ако selector labels се различават по версия на OpenShift, използвай `oc get pods` за точните имена.

| Проблем | Проверка | Корекция |
|---|---|---|
| Forbidden build | `oc auth can-i create builds...` | Липса на RBAC/quota; без cluster-admin escalation |
| ImagePullBackOff | `oc describe pod` | Registry credentials/visibility |
| CrashLoopBackOff | `oc logs deploy/m10-frontend --previous` | Node runtime и PORT |
| TLS Route missing | `oc get route m10-frontend -o yaml` | Проверка на router/Route permissions |
| HTML работи, но API е 502 | Няма backend deployment | Очаквано преди Lab 10-D |

## 6. Cleanup

**Ако продължаваш към 10-C–E, остави frontend resource-ите.** За самостоятелен cleanup само в собствения Project:

```bash
oc delete route/m10-frontend --ignore-not-found
oc delete deployment/m10-frontend service/m10-frontend --ignore-not-found
oc delete buildconfig/m10-frontend imagestream/m10-frontend --ignore-not-found
oc delete builds -l buildconfig=m10-frontend --ignore-not-found
```

Не изтривай чужди Images, Projects или Operators. **Приемане:** един и същ JS frontend работи локално и под HTTPS Route в OpenShift и разбираш разликата между build, image registry, Deployment, Service и Route.
