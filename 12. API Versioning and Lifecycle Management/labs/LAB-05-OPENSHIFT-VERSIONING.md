# Lab 12-E — OpenShift: independent v1/v2 backends and path-based Routes

**Учебна цел:** да разгърнеш две версионни API линии в OpenShift с **два отделни Deployments и Services** и един публичен hostname с различни пътища `/v1` и `/v2`. Да превключиш lifecycle само на v1, без да прекъсваш v2.

**Оригинален източник:** [Red Hat API Versioning — Implementation Workshop](https://www.solutionpatterns.io/solution-pattern-api-versioning/api-versioning/03-demo.html). В оригинала използват Quarkus, 3scale, Argo CD и оператори с cluster-admin. Тук основният вариант е самостоятелен **ASP.NET Core/.NET 10** OpenShift lab с ограничен Project access и **без инсталация на 3scale**.

**OpenShift environment:** [S profile](../../docs/OPENSHIFT-LAB-PROFILES.md) with Docker-build/ImageStream and Route privileges; optional 3scale/GitOps needs separately provisioned enterprise resources.

## 1. Предпоставки

- Личен [Red Hat Developer Sandbox](https://developers.redhat.com/developer-sandbox) или друг OpenShift cluster, в който имаш разрешен Project, достатъчна CPU/RAM quota и права за `BuildConfig`, `Build`, `ImageStream`, `Deployment`, `Service`, `Route` и `Secret`.
- Локални Bash, Git, Python 3.10+, `oc` CLI и `curl`. **Не** е необходим локален .NET SDK: Docker strategy build компилира .NET вътре в container build stage.
- Достъп от build nodes до `mcr.microsoft.com` за SDK/runtime 10 образите и до NuGet за framework dependencies. Ако Sandbox няма разрешено Docker strategy build или image registry е недостъпен, **не** заобикаляй SCC/RBAC — изпълни локалните Labs 12-A–12-D.
- Двата Routes използват **един и същ hostname и различни path prefixes**, и трябва да бъдат в **същия namespace**; това е поддържан OpenShift path routing, но зависи от admission/ingress config.
- Изпълни от **корена на Module 12**. Готовите файлове са [Dockerfile](../Dockerfile), [workloads.yaml](../openshift/workloads.yaml), [route-v1.yaml](../openshift/route-v1.yaml) и [route-v2.yaml](../openshift/route-v2.yaml). Няма скрити manifests.

### 1.1. Preflight (провери **преди** промени)

```bash
oc whoami
oc project
oc version
oc auth can-i create buildconfigs.build.openshift.io
oc auth can-i create builds.build.openshift.io
oc auth can-i create imagestreams.image.openshift.io
oc auth can-i create deployments.apps
oc auth can-i create services
oc auth can-i create routes.route.openshift.io
oc auth can-i create secrets
oc get deploy/m12-order-v1 deploy/m12-order-v2 2>/dev/null || true
oc get svc/m12-order-v1 svc/m12-order-v2 2>/dev/null || true
oc get route/m12-order-v1 route/m12-order-v2 2>/dev/null || true
oc get secret/m12-order-key bc/m12-order-image is/m12-order-image 2>/dev/null || true
```

**Очаквано:** всички `can-i` са `yes`, имената `m12-*` са свободни. Ако някой ресурс вече съществува и не е от твой предишен lab, **спри**, не го презаписвай. Използвай [Module 09 CLI onboarding](../../09.%20OpenShift/labs/LAB-01-SANDBOX-CLI-2026.md), ако още нямаш `oc` context.

## 2. Build image от включения C# source

```bash
oc new-build --name=m12-order-image --binary --strategy=docker
oc start-build m12-order-image --from-dir=. --follow --wait
oc get builds -l buildconfig=m12-order-image
oc get imagestream/m12-order-image
M12_IMAGE_REF="$(oc get istag m12-order-image:latest -o jsonpath='{.image.dockerImageReference}')"
test -n "$M12_IMAGE_REF"
printf 'Resolved image: %s\n' "$M12_IMAGE_REF"
```

**Очаквано:** Build `Complete`, ImageStream `m12-order-image:latest` и реален image reference. **Build Complete ≠ Deployment Ready**. Провери `oc get builds`, `oc describe bc m12-order-image`, `oc logs build/ИМЕ` при отказ. Ако се ползва подвижният .NET образ `10.0`, за production избери и проверявай immutable digest; това е учебен пример.

## 3. Secret, два Deployments и два Services

Генерирай **своя** API key, а не демонстрационната парола от чужд walkthrough:

```bash
umask 077
export API_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
M12_KEY_FILE="$(mktemp)"
printf 'API_KEY=%s\n' "$API_KEY" > "$M12_KEY_FILE"
oc create secret generic m12-order-key --from-env-file="$M12_KEY_FILE"
rm -f -- "$M12_KEY_FILE"
unset M12_KEY_FILE
sed "s|IMAGE_PLACEHOLDER|$M12_IMAGE_REF|g" openshift/workloads.yaml | oc apply --dry-run=client -f -
sed "s|IMAGE_PLACEHOLDER|$M12_IMAGE_REF|g" openshift/workloads.yaml | oc apply -f -
oc rollout status deployment/m12-order-v1 --timeout=300s
oc rollout status deployment/m12-order-v2 --timeout=300s
oc get deploy,svc -l training=module12
oc get endpointslice -l kubernetes.io/service-name=m12-order-v1
oc get endpointslice -l kubernetes.io/service-name=m12-order-v2
```

**Очаквано:** и двата Deployments са `1/1 Ready`, Services са порт 8080 и имат endpoints. v1 Pod има `ALLOWED_MAJOR=v1`, v2 Pod — `ALLOWED_MAJOR=v2`. Двете версии могат да се scale/rollout-ват поотделно, въпреки че учебният образ съдържа една codebase.

**Сигурност:** `API_KEY` е в Secret; `runAsNonRoot`, drop capabilities, readiness и resource limits са включени. Една споделена учебна тайна **не е** enterprise application-plan authentication.

## 4. Path-based Routes: един host, два Services

Първо създай **v1 Route** с автоматично генериран hostname; чак след това създай **v2 Route със същия hostname**, но `/v2` path:

```bash
oc apply --dry-run=client -f openshift/route-v1.yaml
oc apply -f openshift/route-v1.yaml
M12_ROUTE_HOST="$(oc get route m12-order-v1 -o jsonpath='{.spec.host}')"
test -n "$M12_ROUTE_HOST"
sed "s|HOST_PLACEHOLDER|$M12_ROUTE_HOST|g" openshift/route-v2.yaml | oc apply --dry-run=client -f -
sed "s|HOST_PLACEHOLDER|$M12_ROUTE_HOST|g" openshift/route-v2.yaml | oc apply -f -
oc get routes.route.openshift.io m12-order-v1 m12-order-v2
oc describe route m12-order-v1
oc describe route m12-order-v2
```

**Очаквано:** първият Route обслужва `https://HOST/v1/placeorder`, вторият `https://СЪЩИЯ-HOST/v2/placeorder`. И двата трябва да са **Admitted** от router. Ако v2 е отхвърлен с `HostAlreadyClaimed`, провери, че и двата ресурса са в **един и същ Project**, имат различен `spec.path` и спазват ingress policy; **не** променяй cluster-scoped admission policy заради упражненията.

**Защо няма Route за `/healthz`?** Path-based routes публикуват само `/v1` и `/v2`. Readiness се проверява **вътре в клъстера** от kubelet; общият endpoint `/healthz` умишлено не е публичен на този hostname.

## 5. HTTP contract tests през общия hostname

```bash
python3 tools/check.py --base-url "https://$M12_ROUTE_HOST" --v1-status active
python3 consumers/client.py --version 1.0.0 --base-url "https://$M12_ROUTE_HOST"
python3 consumers/client.py --version 2.0.0 --base-url "https://$M12_ROUTE_HOST"
oc logs deployment/m12-order-v1 --tail=30
oc logs deployment/m12-order-v2 --tail=30
```

**Очаквано:** v1.0 и v1.1 clients продължават с `/v1`, v2 работи с `/v2`, двата отрицателни cross-version теста връщат HTTP 400. Ако Python изведе TLS certificate error, провери Route сертификата и trust store; **не** изключвай TLS проверката за основния тест.

## 6. Отделен v1 lifecycle rollout

Този сценарий демонстрира **backend-side** deprecation, а не реално 3scale policy. v2 остава без промени:

```bash
oc set env deployment/m12-order-v1 V1_LIFECYCLE=deprecated
oc rollout status deployment/m12-order-v1 --timeout=300s
python3 tools/check.py --base-url "https://$M12_ROUTE_HOST" --v1-status deprecated
oc set env deployment/m12-order-v1 V1_LIFECYCLE=sunset
oc rollout status deployment/m12-order-v1 --timeout=300s
python3 tools/check.py --base-url "https://$M12_ROUTE_HOST" --v1-status sunset
oc set env deployment/m12-order-v1 V1_LIFECYCLE=active
oc rollout status deployment/m12-order-v1 --timeout=300s
```

**Очаквано:** v1 `201 → 201 + RFC lifecycle headers → 410 → 201` след rollback; v2 винаги `201`. Поради rolling restart на v1 и ограничени Sandbox ресурси е възможно кратко прекъсване. Това **не доказва zero downtime**, production HA или 3scale analytics.

## 7. Истински 3scale и GitOps — при налична enterprise среда

В [оригиналния Red Hat walkthrough](https://www.solutionpatterns.io/solution-pattern-api-versioning/api-versioning/03-demo.html) 3scale конфигурацията е версионирана с GitOps/Argo CD. Проектът настройва Backend, Product, Mapping Rules, Application Plans, API credentials, ActiveDocs и promote staging → production. Използва и cluster-admin, Ansible и оператори за initial setup (original tested on OpenShift **4.15**).

**Не изпълнявай стария Ansible installer върху Developer Sandbox.** Той не е prerequisites-free, а старата версия не гарантира съвместимост с текущ OpenShift.

При подходящ корпоративен клъстер запази GitOps workflow за:
1. `1.0.0` — Product/Backend за `/v1`, ActiveDocs и първи consumer credentials.
2. `1.1.0` — backward-compatible backend/contract, нови mapping/version metrics, старите клиенти работят.
3. `2.0.0` — нов `/v2` Backend или отделен Product и Application Plan.
4. **Измервай** usage по major version; осигури portal release notes и migration notifications.
5. Скрий стария план от **нови записвания**, преди да прекъснеш съществуващите клиенти. Оттегли v1 едва след одобрен retirement plan.

Това е **професионална архитектурна процедура, не изпълним 3scale lab**: credentials, Operator versions, APIcast routes и permission model се определят от реалната организация и не могат да бъдат измислени.

## 8. Troubleshooting и селективен cleanup

| Симптом | Диагностика | Какво правиш |
|---|---|---|
| Build Failed | `oc get builds`, `oc logs build/ИМЕ` | Проверка на registry egress, Docker strategy rights |
| `ImagePullBackOff` | `oc describe pod -l app=m12-order-v1` | Достъп до ImageStream/reference |
| `CrashLoopBackOff` | `oc logs deploy/m12-order-v1 --previous` | Secret и `API_KEY`, bind port, invalid env |
| v2 Route not admitted | `oc describe route m12-order-v2` | Същ namespace/host, различен path, ingress policy |
| 503 / empty endpoints | `oc get endpointslice ...`, `oc get pods` | Изчакай Ready; съответствие Service selector |
| v2 отговаря 404 на /v1 | `ALLOWED_MAJOR=v2` | Очаквано — ползвай правилния Route |
| API test `401` | Локалният `API_KEY` и Secret съвпадат ли? | Не разпечатвай Secret; ротирай при компрометиране |

**Cleanup само на ресурсите с префикс `m12-` в личния Project:**

```bash
oc delete route/m12-order-v2 route/m12-order-v1 --ignore-not-found
oc delete deployment/m12-order-v1 deployment/m12-order-v2 --ignore-not-found
oc delete service/m12-order-v1 service/m12-order-v2 --ignore-not-found
oc delete secret/m12-order-key --ignore-not-found
oc delete buildconfig/m12-order-image imagestream/m12-order-image --ignore-not-found
oc delete builds -l buildconfig=m12-order-image --ignore-not-found
oc get deploy,svc,route,secret,bc,is
unset API_KEY M12_ROUTE_HOST M12_IMAGE_REF
```

Не изтривай Project, други Builds, kubeconfig или чужди secrets.

**Приемане:** два независимо управлявани Deployments, два Services, два Route paths на **един hostname**, работещи v1/v2 contracts и изолирана lifecycle промяна на v1.
