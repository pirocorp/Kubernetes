# Lab 12-E — Истински Istio Service Mesh: canary, mTLS, authorization и observability

**Цел:** да изпълниш **реална mesh политика** върху вече разгърнатите Travelz услуги — sidecar injection, Istio `VirtualService`/`DestinationRule`, 80/20 canary, `PeerAuthentication STRICT` и `AuthorizationPolicy`. **Не** е локалният Python router от Lab 12-C.

**Оригинален източник:** [Red Hat Architecture](https://www.solutionpatterns.io/solution-pattern-apim-servicemesh/comprehensive-service-architecture/02-architecture.html), [Walkthrough](https://www.solutionpatterns.io/solution-pattern-apim-servicemesh/comprehensive-service-architecture/03-demo.html). **Актуализиране:** OpenShift Service Mesh 3.x използва Sail Operator / Istio. Не следвай старите инструкции за OpenShift 4.12 с cluster-admin и Ansible.

## 1. Незаменими prerequisites

1. Изпълнен [Lab 12-D](./LAB-04-OPENSHIFT-DEPLOY.md): собствени Ready Deployments `m12-agency-v1`, `m12-agency-v2`, `m12-portal` и `m12-partner` плюс Services/ServiceAccounts в **един Project**. Ако започваш директно оттук, първо изпълни всички команди на 12-D; необходимият код/файлове са в същия Module 12.
2. Администратор вече е инсталирал и конфигурирал **поддържан Istio control plane/sidecar injection webhook**, който **открива твоя Project**. В рамките на личен Developer Sandbox това може да **не е налично**.
3. Имаш namespace-scoped права за Istio CRDs: `DestinationRule`, `VirtualService`, `PeerAuthentication`, `AuthorizationPolicy`; можеш да обновяваш **само твоите** Deployments. **Не инсталираш оператор, не променяш cluster-wide настройки или injection label на споделен namespace.**
4. Всички подлежащи на политика Workloads трябва да имат успешно inject-нати Envoy sidecars. Ако cluster използва **non-default Istio revision**, трябва да знаеш точния, предоставен от администратора `istio.io/rev`. Няма универсална стойност.
5. Bash, `oc`, Python 3.10+ и терминал с временен port-forward; Kiali/Prometheus/Jaeger са **допълнителни**, ако администраторът ги е предоставил.

**Ако няма реален Service Mesh, този lab е блокиран по външно изискване; Labs 12-A–12-D остават изпълними.** Не обозначавай локалната симулация като успешен Istio тест.

### 1.1. Preflight — провери първо

```bash
oc whoami
oc project
oc get deploy m12-agency-v1 m12-agency-v2 m12-portal m12-partner
oc get svc m12-agency m12-agency-v1 m12-agency-v2 m12-portal m12-partner
oc api-resources | grep -E 'virtualservices|destinationrules|peerauthentications|authorizationpolicies'
oc auth can-i create virtualservices.networking.istio.io
oc auth can-i create destinationrules.networking.istio.io
oc auth can-i create peerauthentications.security.istio.io
oc auth can-i create authorizationpolicies.security.istio.io
oc auth can-i patch deployments.apps
oc get virtualservices.networking.istio.io
oc get destinationrules.networking.istio.io
```

**Очаквано:** всички четири Istio CRD вида са видими, всички `can-i` са `yes`, няма чужди `m12-agency` политики, control plane е реално работещ. Ако CRD или injection service липсва, **спри** и използвай обучението за архитектурните концепции без live mesh.

## 2. Включи sidecar injection само за четирите собствено създадени Deployments

**Случай A — default Istio revision**, разрешена е pod-level injection настройка:

```bash
for d in m12-agency-v1 m12-agency-v2 m12-portal m12-partner; do
  oc patch deployment "$d" --type=merge \
    -p '{"spec":{"template":{"metadata":{"labels":{"sidecar.istio.io/inject":"true"}}}}}'
  oc rollout status "deployment/$d" --timeout=300s
done
oc get pods -l training=module12 \
  -o jsonpath='{range .items[*]}{.metadata.name}{" : "}{.spec.containers[*].name}{"\n"}{end}'
```

**Очаквано:** всеки от четирите application Pods съдържа `app` **и** `istio-proxy` (обичайно `2/2 Ready`). Label в Deployment само по себе си **не доказва injection**; проверката на реалния Pod е задължителна. Ако няма Envoy sidecars, **не прилагай STRICT mTLS**.

**Случай B — non-default revision:** не гадай revision. Използвай точно `istio.io/rev=ИМЕ`, съобщено от администратора, върху Pod template на **твоите** Deployments; след rollout повтори проверката. Не променяй shared namespace labels или cluster installation. В такъв случай премахни вече ненужната pod injection настройка само след изрично потвърждение на revision-specific configuration.

## 3. Реален weighted traffic: DestinationRule + VirtualService

Файловете са включени:
- [destination-rule.yaml](../mesh/destination-rule.yaml) — Istio subsets от labels `version=v1` и `version=v2`.
- [canary-80-20.yaml](../mesh/canary-80-20.yaml) — route към v1 (80%) и v2 (20%), timeout и retry policy.
- [rollback-v1.yaml](../mesh/rollback-v1.yaml) — 100% към v1.

```bash
oc apply --dry-run=client -f mesh/destination-rule.yaml
oc apply --dry-run=client -f mesh/canary-80-20.yaml
oc apply -f mesh/destination-rule.yaml
oc apply -f mesh/canary-80-20.yaml
oc set env deployment/m12-portal AGENCY_URL=http://m12-agency:8080
oc rollout status deployment/m12-portal --timeout=300s
oc get destinationrule m12-agency -o yaml
oc get virtualservice m12-agency -o yaml
```

**Защо Portal първоначално използваше `m12-agency-v1`?** Без mesh това е предвидим single-version Service. Сега превключваме към `m12-agency`, който избира и двата backend Pod-а, а **Istio sidecar** прилага действителния route policy.

В **терминал 1**:

```bash
oc port-forward service/m12-portal 5510:8080
```

В **терминал 2**, от Module 12 root:

```bash
python3 tools/mesh_sample.py --base-url http://127.0.0.1:5510 --count 40
```

**Очаквано:** HTTP 200 и отговори и от v1, и от v2. **Не изисквай точно 32/8** — истинският weighted routing е статистически; използвай 40+ заявки и наблюдавай тенденцията, Envoy/Prometheus/Kiali, ако са налични. Ако излизат само v1, провери реалните sidecars, route конфигурацията, DestinationRule host/subsets, service endpoints и кеширани конфигурации. Прекрати port-forward с Ctrl+C.

## 4. STRICT mTLS + ServiceAccount-based authorization

**Изпълни само след потвърдено `istio-proxy` във всички Travelz Pods.** [policy-mtls.yaml](../mesh/policy-mtls.yaml) създава:
- `PeerAuthentication` с `STRICT` за **само Agency Pods** (selector `app=m12-agency`).
- `AuthorizationPolicy ALLOW`, допускаща само `m12-portal-sa` и `m12-partner-sa` (workload identities от mTLS) за `GET /api/travels/*`.

```bash
oc apply --dry-run=client -f mesh/policy-mtls.yaml
oc apply -f mesh/policy-mtls.yaml
oc get peerauthentication m12-agency-strict -o yaml
oc get authorizationpolicy m12-agency-allow-clients -o yaml
oc get pods -l training=module12
```

**Проверка на разрешени заявки:** повтори Portal теста от раздел 3 (след кратко изчакване за Envoy policy propagation) и Partner API теста от Lab 12-D. Portal и Partner имат **собствени ServiceAccounts**. Тяхната source identity трябва да се валидира от Envoy, а не от произволен клиентски HTTP header.

### 4.1. Негативен authorization тест

Включен е [probe-denied.yaml](../mesh/probe-denied.yaml) със собствен `m12-probe-sa` и `curl` контейнер. Създай го **само ако ImagePull и Pod injection са разрешени**:

```bash
oc apply -f mesh/probe-denied.yaml
oc wait --for=condition=Ready pod/m12-probe-denied --timeout=240s
oc get pod m12-probe-denied -o jsonpath='{.spec.containers[*].name}{"\n"}'
oc exec pod/m12-probe-denied -c curl -- \
  curl -sS -o /dev/null -w 'HTTP %{http_code}\n' \
  http://m12-agency:8080/api/travels/Paris
```

**Очаквано:** probe има `curl` + `istio-proxy` и получава **HTTP 403** от policy, докато Portal/Partner са разрешени. Ако `503`, не го отбелязвай като успешен authorization test: провери CNI, mTLS/sidecars, identity и Envoy config. Ако получиш `200`, това е **сериозен признак**, че policy не е приложена/трафикът я заобикаля; спри теста и диагностицирай. **Kubernetes `oc port-forward` не доказва mTLS enforcement**, защото може да заобиколи нормалния inbound proxy datapath.

## 5. Canary rollback и наблюдение

За 100% v1 traffic:

```bash
oc apply -f mesh/rollback-v1.yaml
oc get virtualservice m12-agency -o yaml
```

Повтори `python3 tools/mesh_sample.py --base-url http://127.0.0.1:5510 --count 30` **докато port-forward е стартиран отново**. **Очаквано:** само `v1`, след като конфигурацията се разпространи. Върни 80/20:

```bash
oc apply -f mesh/canary-80-20.yaml
```

При налични Kiali/Prometheus виж graph/metrics за `m12-portal → m12-agency`, service versions, response codes и latency. Логовете с `X-Correlation-Id` **не са еквивалент** на Jaeger/OpenTelemetry distributed traces. Последните изискват реално configured collector/sampling/tracing integrations.

**Security boundary:** mTLS защитава **east-west** трафика между mesh workloads. Публичният Partner Route използва **edge TLS**, а Partner gateway прилага демонстрационен partner key, но това **не е лицензирана 3scale инсталация**.

## 6. Разграничение от остарелия 3scale WASM plugin

Оригиналният Red Hat pattern използва `threescale-wasm-auth` за директна 3scale authorization/reporting в Istio sidecars. **Според Red Hat 3scale 2.16 този модул е deprecated и неподдържан от OpenShift Service Mesh 3.** Не копирай показаните стари `WasmPlugin` инструкции, tokens или OCI image в настоящия lab.

За актуален enterprise дизайн използвай **поддържан 3scale/APIcast** за North–South и **OpenShift Service Mesh 3** за East–West, или избери друга официално поддържана policy integration след проверка на продуктовата матрица. Виж [ENTERPRISE-3SCALE-MESH.md](../docs/ENTERPRISE-3SCALE-MESH.md).

## 7. Troubleshooting

| Симптом | Проверка | Действие |
|---|---|---|
| Istio CRDs липсват | `oc api-resources` | Това не е mesh-capable cluster; не инсталирай Operator |
| Missing sidecar | `oc get pods -l training=module12 -o jsonpath=...` | Проверка на revision, injector, namespace selection |
| Mixed 503/200 | `oc get endpointslice -l kubernetes.io/service-name=m12-agency` | Istio policy, service selectors, Envoy routes |
| 403 за разрешен Portal | ServiceAccount, proxy identity | Провери `m12-portal-sa` и policy, не премахвай blindly authentication |
| Probe връща 200 | Policy bypass/incorrect selector | Спрете упражненията по security, анализирай control plane |
| Кратко прекъсване при rollout | Resource quota/една replica | Няма zero-downtime гаранция |
| Kiali недостъпно | Addon не е инсталиран | Проверявай чрез `oc` и test clients; Kiali не е prerequisite |

## 8. Cleanup — правилният ред

**Първо** премахни само собствените Istio security и routing policies, после възстанови Portal към direct v1 Service:

```bash
oc delete -f mesh/probe-denied.yaml --ignore-not-found
oc delete -f mesh/policy-mtls.yaml --ignore-not-found
oc set env deployment/m12-portal AGENCY_URL=http://m12-agency-v1:8080
oc delete virtualservice/m12-agency destinationrule/m12-agency --ignore-not-found
for d in m12-agency-v1 m12-agency-v2 m12-portal m12-partner; do
  oc patch deployment "$d" --type=merge \
    -p '{"spec":{"template":{"metadata":{"labels":{"sidecar.istio.io/inject":null,"istio.io/rev":null}}}}}'
done
oc get virtualservice,destinationrule,peerauthentication,authorizationpolicy
```

**Не** променяй споделени namespace labels или администраторски Istio resources. Ако mesh control plane не е реагирал на removal, изчакай rollout и провери env/Pod templates. След това изпълни точно [cleanup от Lab 12-D](./LAB-04-OPENSHIFT-DEPLOY.md) за четирите Deployments, Services, Secrets, BuildConfigs и Routes.

**Приемане:** реални Envoy sidecars, VirtualService 80/20, DestinationRule subsets, STRICT mTLS, разрешен Portal, отказан чужд ServiceAccount, управляем rollback и безопасен cleanup — **само при действително наличен mesh**.