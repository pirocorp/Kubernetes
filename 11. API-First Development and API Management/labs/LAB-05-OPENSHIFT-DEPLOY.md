# Lab 11-E — Deploy an API-first ASP.NET Core API on OpenShift

**Цел:** build на контейнерния образ, Deployment, Service и HTTPS Route, без нарушаване на OpenAPI договора. Използваме познатия OpenShift workflow от Module 09, но **Module 11 има собствен код и файлове**.

**OpenShift environment:** [S profile](../../docs/OPENSHIFT-LAB-PROFILES.md) with own Project/namespace-level build and Route rights. Real 3scale remains enterprise-only; the local gateway does not prove that its Operator is installed.

## Предпоставки

- Преминат локален [Lab 11-C](./LAB-03-ASPNET-IMPLEMENTATION.md), или поне прочетен Source/Contract; действителният API е изцяло включен в Module 11.
- Личен [Red Hat Developer Sandbox](https://developers.redhat.com/developer-sandbox) **или** разрешен OpenShift cluster; `oc` login и **Project** selector; Bash, Git, Python 3.10+, `curl`; свободни namespace quota и ingress Router.
- Достъп до Red Hat-compatible OpenShift **Docker strategy BuildConfig/Build/ImageStream** (или алтернативен външен build+push към разрешен registry). **Sandbox не гарантира всички build права**: това е външна prerequisite, не разрешение да заобикаляш SCC.
- Работна директория: **коренът на Module 11**; файловете са [Dockerfile](../Dockerfile), [openshift/api.yaml](../openshift/api.yaml), [ASP.NET Core source](../src/ProductsApi/Program.cs). Не се изисква нов Project или cluster-admin.
- Конфигурацията е за **.NET 10 runtime на порт 8080**; namespace **не е фиксиран** в манифеста, за да не се променя чуждо пространство. Не използвай default Kubernetes kubeadm/Calico context.

## 1. Проверка на средата

```bash
oc whoami
oc project
oc version
oc auth can-i create deployments.apps
oc auth can-i create services
oc auth can-i create routes.route.openshift.io
oc auth can-i create secrets
oc auth can-i create buildconfigs.build.openshift.io
oc auth can-i create builds.build.openshift.io
oc auth can-i create imagestreams.image.openshift.io
oc get deployment/m11-products-api service/m11-products-api route/m11-products-api 2>/dev/null || true
```

**Очаквано:** `yes` за всички необходими действия, избран личен Project и **свободни имена** `m11-products-api`, `m11-products-key`, `m11-products-build`. Ако правата за BuildConfig/Build липсват, **спри OpenShift Build пътя**. Използването на външен OCI registry изисква собствена разрешена repository, image push credentials и `pullSecret`, които не са универсални за всички акаунти.

## 2. Започни Build от локален source

Не използваме неизвестен remote Git sample. `Dockerfile` произвежда .NET 10 image с HTTP port 8080.

```bash
oc new-build --name=m11-products-build --binary --strategy=docker
oc start-build m11-products-build --from-dir=. --follow --wait
oc get builds -l buildconfig=m11-products-build
oc get imagestream m11-products-build
IMAGE_REFERENCE="$(oc get istag m11-products-build:latest -o jsonpath='{.image.dockerImageReference}')"
test -n "$IMAGE_REFERENCE" || { echo 'Build image не е наличен'; false; }
printf 'Image resolved: %s\n' "$IMAGE_REFERENCE"
```

**Очаквано:** `Build Complete`, ImageStream tag `m11-products-build:latest`, разрешен Docker image reference. Това **не** е същото като успешен Deployment. Ако Build е Pending/Failed, виж `oc get builds`, `oc describe bc m11-products-build`, `oc logs build/ИМЕ`, quota и image registry egress. Не повишавай SCC privileges като workaround.

## 3. Secret и манифести

Използвай **собствен**, нов API key. Не го добавяй в Git, screenshot или публичен terminal output:

```bash
export API_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
umask 077
M11_SECRET_FILE="$(mktemp)"
printf 'API_KEY=%s\n' "$API_KEY" > "$M11_SECRET_FILE"
oc create secret generic m11-products-key --from-env-file="$M11_SECRET_FILE"
rm -f -- "$M11_SECRET_FILE"
unset M11_SECRET_FILE
sed "s|IMAGE_PLACEHOLDER|$IMAGE_REFERENCE|g" openshift/api.yaml | oc apply --dry-run=client -f -
sed "s|IMAGE_PLACEHOLDER|$IMAGE_REFERENCE|g" openshift/api.yaml | oc apply -f -
oc rollout status deployment/m11-products-api --timeout=240s
oc get deployment/m11-products-api service/m11-products-api route/m11-products-api
oc get endpointslice -l kubernetes.io/service-name=m11-products-api
```

**Очаквано:** Deployment `1/1 Ready`, Service на `8080` с EndpointSlice и Route със `spec.port.targetPort: http`. Външният router извършва **edge TLS**, а вътрешният Service е HTTP. Файлът използва `apps/v1`, `v1` и `route.openshift.io/v1` APIs. Ограниченията за security context са описани в манифеста.

## 4. Проверки по договор и диагностика

```bash
ROUTE_HOST="$(oc get route m11-products-api -o jsonpath='{.spec.host}')"
test -n "$ROUTE_HOST"
curl -fsS "https://$ROUTE_HOST/healthz"
curl -fsS -H "X-Api-Key: $API_KEY" "https://$ROUTE_HOST/v1/products"
python3 tools/contract_check.py --base-url "https://$ROUTE_HOST"
oc logs deployment/m11-products-api --tail=40
oc get events --sort-by=.lastTimestamp
```

**Очаквано:** `ok`, продуктов каталог и успешен contract smoke suite. След нов Deployment in-memory продуктите се рестартират до началния каталог; упражнението не демонстрира persistence.

**Failure cases:**

| Симптом | Проверка | Корекция |
|---|---|---|
| `Forbidden` | `oc auth can-i create ...` | Не заобикаляй RBAC/SCC; избери разрешена учебна среда |
| `ImagePullBackOff` | `oc describe pod -l app=m11-products-api` | Registry image reference/pull rights |
| `CrashLoopBackOff` | `oc logs deploy/m11-products-api --previous` | Secret `API_KEY`, container port, startup exceptions |
| Route 503 | EndpointSlice, readiness, Route admission | Проверка на Service selector и Pod Ready |
| HTTPS certificate error | Router cert, host, доверие | Не използвай `curl -k` като основен тест |
| `401` с коректен URL | Ключът от същия текущ Secret ли е? | Не печатай тайната; коригирай локалната конфигурация |

## 5. Enterprise API Management — следващ слой, не скрита предпоставка

В реален OpenShift проект API gateway (**3scale/APIcast**) се разполага пред backend Service и прилага authentication, plans, mapping rules, quotas и analytics. [Официална документация за 3scale](https://docs.redhat.com/en/documentation/red_hat_3scale_api_management/2.16/html/getting_started/launching-apis).

**В този lab Route публикува API директно**, което е валидно за учебен тест с API key, но **НЕ** демонстрира реален 3scale onboarding. Ако имаш лицензирана/управлявана 3scale инсталация, правилният корпоративен workflow е: API Product → Backend → Application Plan → credentials → mapping rules → APIcast staging → validation → production promotion. Конкретните ресурси и credential IDs са специфични за акаунта и не могат да бъдат предварително измислени. За упражняване на логиката без тях използвай [Lab 11-D](./LAB-04-API-MANAGEMENT.md).

## Cleanup

**Само в избрания личен Project** и само след като потвърдиш учебните имена:

```bash
oc delete route/m11-products-api --ignore-not-found
oc delete deployment/m11-products-api service/m11-products-api --ignore-not-found
oc delete secret/m11-products-key --ignore-not-found
oc delete buildconfig/m11-products-build imagestream/m11-products-build --ignore-not-found
oc delete builds -l buildconfig=m11-products-build --ignore-not-found
oc get deploy,svc,route,secret,bc,is
unset API_KEY IMAGE_REFERENCE ROUTE_HOST
```

Не изтривай Project, чужди ресурси или други API ключове. Ако има residual Builds без selector label, изтрий **само** реалните свързани с този lab имена.

**Критерий за успешно упражнение:** successful Build, `1/1 Ready`, HTTPS Route, `401` без ключ, `200` с ключ, съответствие с contract smoke suite, селективен cleanup. **Не е извършван live cluster тест**.
