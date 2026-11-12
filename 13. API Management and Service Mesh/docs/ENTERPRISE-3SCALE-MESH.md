# Enterprise design: 3scale API Management + OpenShift Service Mesh

**Този документ е архитектурна справка**, а не инсталационен скрипт. Разглежда четирите бизнес сценария на [оригиналния Red Hat Comprehensive Service Architecture Solution Pattern](https://www.solutionpatterns.io/solution-pattern-apim-servicemesh/comprehensive-service-architecture/index.html) за Travelz.

## 1. Защо API Management и Service Mesh са допълващи се?

| Област | API Management / 3scale | Service Mesh / Istio |
|---|---|---|
| Основен трафик | North–South / Inter-domain (партньори и business units) | East–West / Intra-domain (service-to-service) |
| Identity | API applications, partner credentials, plans | Workload identities (service accounts / mTLS) |
| Policy | Quotas, onboarding, request analytics, API products | Routing, authorization, retries, mTLS, destination policies |
| Operations | Developer Portal, APIcast, usage reporting | Envoy sidecars, control plane, Kiali, telemetry |
| Цел | Управление на отношения с API consumers | Надеждна и защитена взаимовръзка между workloads |

Няма универсално правило, че целият вътрешен HTTP трафик не се нуждае от API governance или че външен клиент винаги минава единствено през APIcast. Това са **граници по отговорност**, а не догма за топологията.

## 2. Четирите стъпки на Travelz

### Scenario 1 — Разрастване на Travelz Online

Travel Portal е консуматор, Travel Agency предоставя quote услуги. Istio sidecar proxy свързва workloads в mesh, отговорен за routing, service identity, mutual TLS, access policy и telemetry. В [Lab 12-E](../labs/LAB-05-REAL-ISTIO-MESH.md) използваме `VirtualService` (80/20), `DestinationRule`, `PeerAuthentication STRICT` и `AuthorizationPolicy`, без да променяме C# бизнес логиката.

### Scenario 2 — Отваряне към external partners

Публичните партньори Red Company/Blue Company използват управляем Partner API и получават v2, докато вътрешният portal може да използва v1/v2. В enterprise 3scale това е продукт, backend и APIcast endpoint, а API договорът може да бъде публикуван чрез Developer Portal/ActiveDocs.

**Каноничен учебен договор:** [Travelz Partner OpenAPI 3.0.3](../contracts/travelz-partner-v1.openapi.json). Endpoint `GET /partner/travels/{city}`, `X-Partner-Key` и документирани `200/401/429/502` response models.

### Scenario 3 — North–South security и business plans

3scale Product/Backend, Application Plans, Client credentials, developer registration и API analytics могат да осигурят договорни квоти и проследяване по партньор. В [Lab 12-B](../labs/LAB-02-PARTNER-API-MANAGEMENT.md) имаме **локална учебна** key authentication + counters + rate limits, но няма реални 3scale Accounts, plan creation, invoicing или signup.

За продукционен onboarding се нуждаеш от организационна политика и разрешена 3scale среда. Не използвай фиксираните демонстрационни credentials от историческите walkthrough материали.

### Scenario 4 — Управление и на inter-domain traffic

Оригиналът показва `threescale-wasm-auth` за авторизация и отчетност **директно в Istio sidecars**. Концептуално това свързва 3scale usage policies и Service Mesh dataplane. Важно: **Red Hat 3scale 2.16 изрично отбелязва, че този WASM модул е deprecated и неподдържан в OpenShift Service Mesh 3.** Следователно:

- **Не** инсталирай стария `threescale-wasm-auth:v1.0.0`.
- **Не** копирай старите `WasmPlugin` tokens/конфигурация към OpenShift Service Mesh 3.
- **Не** твърди, че наличието на `WasmPlugin` CRD означава поддръжка на точно този 3scale модул.
- Предпочитаната учебна архитектура е **3scale/APIcast за управляван partner API** + **поддържан OpenShift Service Mesh за вътрешна service security**; за допълнителна integration избери официално поддържана конфигурация спрямо конкретните версии и support matrix.

**Документация на производителя:** [Red Hat 3scale 2.16 — Operating 3scale, Chapter 11, WebAssembly module](https://docs.redhat.com/en/documentation/red_hat_3scale_api_management/2.16/html/operating_red_hat_3scale_api_management/), [Red Hat OpenShift Service Mesh 3.3 — Installing / Sidecar Injection](https://docs.redhat.com/en/documentation/red_hat_openshift_service_mesh/3.3/html-single/installing/index), [OpenShift Service Mesh support lifecycle](https://access.redhat.com/support/policy/updates/openshift_operators).

## 3. Deployment responsibilities

**Platform team:** проверява supported OpenShift/Service Mesh/3scale versions, control plane и route/security policies, наблюдаемост, certificate issuer, RBAC, upgrade/migration, SLO, recovery.

**API Provider:** дефинира OpenAPI contract, API Product, lifecycle, backend endpoints, app plans, mappings, release policy, use-case governance.

**Application team:** гарантира readiness, resilience, timeouts, safe retries на idempotent endpoints, логове и telemetry context; versioned microservices и backward compatibility.

**API Consumer/Partner:** съхранява credentials безопасно, спазва quotas, тества contract changes, мигрира версии преди sunset.

**Security team:** управлява API keys/OIDC, workload identities, мрежови граници, secrets, audit, incident response и policy assurance.

## 4. Примерен enterprise migration checklist

- [ ] Verify current Red Hat support matrix: OpenShift, Service Mesh 3.x, 3scale, Kiali/observability addons.
- [ ] Decide North–South APIcast location and TLS trust boundaries.
- [ ] Identify mesh members, namespaces, service accounts and default/per-revision sidecar injection.
- [ ] Publish OpenAPI 3 contract and partner onboarding documentation.
- [ ] Map Partner Product → Backend → Application Plan → credentials; apply auth and quotas in supported configuration.
- [ ] Deploy stable v1 and candidate v2 Agency workloads; allow **only tested** GET retries/canary policies.
- [ ] Verify Envoy sidecars, mTLS STRICT, AuthorizationPolicy and negative access tests.
- [ ] Verify per-partner API metrics separately from per-workload network metrics.
- [ ] Establish incident rollback, post-deployment validation, API version migration and lifecycle approvals.
- [ ] Keep operators, namespace-scoped resources and secrets under least-privilege GitOps workflows; do not commit credentials.

## 5. Какво не може да бъде универсално самодостатъчно

3scale Product IDs, APIcast configuration, real partner keys, Istio control-plane revisions, gateway certificates, namespace membership и operator permissions **се предоставят от реалната организация**. Не може да се измислят работещи стойности в обучението. Затова Labs 12-A–12-C са напълно локални; 12-D и 12-E са **изпълними само при декларираните инфраструктурни prerequisites**.

**Оригинални източници:** [Introduction](https://www.solutionpatterns.io/solution-pattern-apim-servicemesh/comprehensive-service-architecture/index.html) · [Architecture](https://www.solutionpatterns.io/solution-pattern-apim-servicemesh/comprehensive-service-architecture/02-architecture.html) · [Walkthrough](https://www.solutionpatterns.io/solution-pattern-apim-servicemesh/comprehensive-service-architecture/03-demo.html).