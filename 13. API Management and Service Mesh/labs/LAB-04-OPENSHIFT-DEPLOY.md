# Lab 13-D — OpenShift: Travelz и контролирано Partner API

**Цел:** реално deployment упражнение с два Agency backend-а, Portal и Partner gateway: четири Deployments, пет Services и HTTPS Route. **Без инсталиран Istio това все още не е Service Mesh.** Истинската мрежова политика се добавя в [Lab 13-E](./LAB-05-REAL-ISTIO-MESH.md).

**Основен източник:** [Red Hat — Travelz API Management & Service Mesh](https://www.solutionpatterns.io/solution-pattern-apim-servicemesh/comprehensive-service-architecture/03-demo.html).

## 1. Предпоставки

Личен [Red Hat Developer Sandbox](https://developers.redhat.com/developer-sandbox) или друг разрешен OpenShift Project с права за BuildConfig, Build, ImageStream, Deployment, Service, ServiceAccount, Secret и Route. Локално: Bash, Git, Python 3.10+, `oc` и `curl`; не се изисква локален .NET SDK — компилацията е в Docker strategy build.

Build nodes трябва да достигат `mcr.microsoft.com` (.NET 10) и Python image registry; необходима е quota за **4 runtime Pods и 2 последователни Build Pods**. Всички файлове са включени: [Dockerfile](../Dockerfile), [partner.Dockerfile](../container/partner.Dockerfile), [partner_gateway.py](../tools/partner_gateway.py), [base.yaml](../openshift/base.yaml). Работна директория — коренът на Module 13.

### 1.1. Preflight

```bash
oc whoami
oc project
oc version
oc auth can-i create buildconfigs.build.openshift.io
oc auth can-i create builds.build.openshift.io
oc auth can-i create imagestreams.image.openshift.io
oc auth can-i create deployments.apps
oc auth can-i create services
oc auth can-i create serviceaccounts
oc auth can-i create routes.route.openshift.io
oc auth can-i create secrets
oc get resourcequota
oc get deploy,svc,route,sa,bc,is,secret -l training=module13
test -s openshift/base.yaml
test -s container/partner.Dockerfile
test -s tools/partner_gateway.py
```

**Очаквано:** всички `can-i` → `yes`, правилен личен Project, достатъчна quota и **няма съществуващи чужди `m13-*` ресурси**. Ако Sandbox не позволява Docker strategy build, **спри тук** и използвай локалните Labs 13-A–13-C; не заобикаляй SCC/RBAC и не инсталирай Operator.

## 2. Изгради C# контейнерния образ

```bash
oc new-build --name=m13-travelz-image --binary --strategy=docker
oc start-build m13-travelz-image --from-dir=. --follow --wait
oc get builds -l buildconfig=m13-travelz-image
TRAVEL_IMAGE="$(oc get istag m13-travelz-image:latest -o jsonpath='{.image.dockerImageReference}')"
test -n "$TRAVEL_IMAGE" || { echo 'Travelz image missing'; false; }
printf 'Travelz image: %s\n' "$TRAVEL_IMAGE"
```

**Очаквано:** Build `Complete`, ImageStream и реално image reference. При Failed/Pending използвай `oc describe bc m13-travelz-image`, `oc get builds` и `oc logs build/ИМЕ`. Build success **не доказва** Deployment readiness.

## 3. Изгради отделен Python partner gateway image

Временно подготви контекст, съдържащ точно Dockerfile и Python source. Не променяй root Dockerfile и не клонирай чужд пример:

```bash
M13_BUILD_DIR="$(mktemp -d)"
cp container/partner.Dockerfile "$M13_BUILD_DIR/Dockerfile"
cp tools/partner_gateway.py "$M13_BUILD_DIR/partner_gateway.py"
oc new-build --name=m13-partner-image --binary --strategy=docker
oc start-build m13-partner-image --from-dir="$M13_BUILD_DIR" --follow --wait
rm -f -- "$M13_BUILD_DIR/Dockerfile" "$M13_BUILD_DIR/partner_gateway.py"
rmdir -- "$M13_BUILD_DIR"
unset M13_BUILD_DIR
PARTNER_IMAGE="$(oc get istag m13-partner-image:latest -o jsonpath='{.image.dockerImageReference}')"
test -n "$PARTNER_IMAGE" || { echo 'Partner image missing'; false; }
printf 'Partner image: %s\n' "$PARTNER_IMAGE"
```

**Очаквано:** втори Build `Complete`, непривилегирован Python контейнер на порт 8080. При build interruption временният `M13_BUILD_DIR` може да остане; изтривай само неговите собствени файлове след проверка на пътя.

## 4. Secret и четири Deployment-а

```bash
python3 tools/keys.py bootstrap
umask 077
oc create secret generic m13-partner-keys --from-env-file=.runtime/keys.env
sed -e "s|TRAVEL_IMAGE_PLACEHOLDER|$TRAVEL_IMAGE|g" \
    -e "s|PARTNER_IMAGE_PLACEHOLDER|$PARTNER_IMAGE|g" \
    openshift/base.yaml | oc apply --dry-run=client -f -
sed -e "s|TRAVEL_IMAGE_PLACEHOLDER|$TRAVEL_IMAGE|g" \
    -e "s|PARTNER_IMAGE_PLACEHOLDER|$PARTNER_IMAGE|g" \
    openshift/base.yaml | oc apply -f -
oc rollout status deployment/m13-agency-v1 --timeout=300s
oc rollout status deployment/m13-agency-v2 --timeout=300s
oc rollout status deployment/m13-portal --timeout=300s
oc rollout status deployment/m13-partner --timeout=300s
oc get deploy,svc,route,sa -l training=module13
oc get endpointslice -l kubernetes.io/service-name=m13-agency-v1
oc get endpointslice -l kubernetes.io/service-name=m13-agency-v2
oc get endpointslice -l kubernetes.io/service-name=m13-partner
```

**Очаквано:** четири Ready Deployments, пет Services (`m13-agency`, `m13-agency-v1`, `m13-agency-v2`, `m13-portal`, `m13-partner`), три ServiceAccounts и един Route. Portal използва `AGENCY_URL=http://m13-agency-v1:8080` до въвеждането на Istio; партньорите използват директно v2 чрез gateway. **ClusterIP сам по себе си не гарантира mTLS или zero-trust.** Route използва edge TLS.

## 5. Тествай вътрешния и външния трафик

В **терминал 1** (остави да работи):

```bash
oc port-forward service/m13-portal 5510:8080
```

В **терминал 2**:

```bash
curl -fsS http://127.0.0.1:5510/portal/Paris
```

**Очаквано:** `channel=travel-portal`, `quote.version=v1` и correlation ID. Спри port-forward с Ctrl+C след теста.

Partner API:

```bash
M13_HOST="$(oc get route m13-partner -o jsonpath='{.spec.host}')"
test -n "$M13_HOST"
set -a
. .runtime/keys.env
set +a
python3 tools/partner_client.py --base-url "https://$M13_HOST" --partner red --count 1
python3 tools/partner_client.py --base-url "https://$M13_HOST" --partner blue --count 1
python3 tools/partner_metrics.py --base-url "https://$M13_HOST"
```

**Очаквано:** двама партньори с HTTP 200, `version=v2` и отделни metrics. Помощните Python инструменти четат тайните от environment и не ги отпечатват. Не използвай `curl -k` и не изпращай secrets в URL.

## 6. Troubleshooting

| Проблем | Проверка | Корекция |
|---|---|---|
| Build Forbidden | `oc auth can-i create ...` | Не заобикаляй RBAC |
| Build Failed | `oc logs build/ИМЕ` | Registry/network/image достъп |
| ImagePullBackOff | `oc describe pod -l app=m13-partner` | ImageStream/pull права |
| Pod CrashLoopBackOff | `oc logs deployment/m13-partner --previous` | Secret, container port, build |
| Route 503 | `oc get endpointslice -l kubernetes.io/service-name=m13-partner` | Service selector и Pod Ready |
| Portal 502 | `oc logs deployment/m13-portal` | Agency v1 Service/DNS/network |
| Partner 401/429 | API key или quota | Проверявай без да печаташ secrets; изчакай 15 сек |

## 7. Cleanup — само собствени ресурси

**Ако продължаваш с Lab 13-E, не изпълнявай cleanup сега.** След Module 14-E първо премахни Istio policies, после base resources.

```bash
oc delete route/m13-partner --ignore-not-found
oc delete deployment/m13-agency-v1 deployment/m13-agency-v2 deployment/m13-portal deployment/m13-partner --ignore-not-found
oc delete service/m13-agency service/m13-agency-v1 service/m13-agency-v2 service/m13-portal service/m13-partner --ignore-not-found
oc delete serviceaccount/m13-agency-sa serviceaccount/m13-portal-sa serviceaccount/m13-partner-sa --ignore-not-found
oc delete secret/m13-partner-keys --ignore-not-found
oc delete buildconfig/m13-travelz-image buildconfig/m13-partner-image --ignore-not-found
oc delete builds -l buildconfig=m13-travelz-image --ignore-not-found
oc delete builds -l buildconfig=m13-partner-image --ignore-not-found
oc delete imagestream/m13-travelz-image imagestream/m13-partner-image --ignore-not-found
oc get deploy,svc,route,sa,secret,bc,is -l training=module13
unset TRAVEL_IMAGE PARTNER_IMAGE M13_HOST PARTNER_RED_KEY PARTNER_BLUE_KEY ADMIN_KEY
```

Не изтривай Project, namespace, operator, чужди builds, kubeconfig или други secrets.

**Приемане:** четири ready Pods, пет Services, вътрешен v1 Portal, външен HTTPS v2 Partner API и отделни credentials/analytics. Реален Istio се проверява в следващия lab.