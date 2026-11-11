# OrderPlacement API — migration guide (v1 to v2)

**Who should read this?** API consumers using `POST /v1/placeorder` with `firstName` and `lastName`. Read the [official Red Hat versioning pattern](https://www.solutionpatterns.io/solution-pattern-api-versioning/api-versioning/index.html) for the enterprise scenario.

## Changes

| Contract | Endpoint | Accepted JSON fields | Consumer impact |
|---|---|---|---|
| **1.0.0** | `POST /v1/placeorder` | Required `firstName`, `lastName`, `sku`, `quantity` | Initial client |
| **1.1.0** | `POST /v1/placeorder` | Same required fields; optional `deliveryInstructions` | Old 1.0.0 clients continue working |
| **2.0.0** | `POST /v2/placeorder` | Required `fullName`, `sku`, `quantity`; optional `deliveryInstructions` | **Breaking change** — migrate payload and endpoint |

Do not assume `fullName = firstName + " " + lastName` is a universally correct identity representation. The demo concatenates synthetic names only to explain migration. Real domains may require a separate canonical name model, data migration and legal review.

## Migration procedure

1. Inventory every client, its owner, credentials and consumed paths.
2. Change the client URL from `/v1/placeorder` to `/v2/placeorder`.
3. Change request body from `{ "firstName": "Alex", "lastName": "Ivanov", "sku": "BOOK-1", "quantity": 2 }` to `{ "fullName": "Alex Ivanov", "sku": "BOOK-1", "quantity": 2 }`.
4. Repeat negative tests: v2 rejects v1 fields; v1 rejects `fullName`-only payload.
5. Test in a staging environment against both endpoints while `/v1` still works; coordinate with provider.
6. Use per-version API analytics to verify v1 usage goes to zero; contact remaining consumers before retirement.
7. Change developer portal documentation/ActiveDocs and release notes; update gateway mapping rules, API Products or Application Plans as needed.
8. Only then implement sunset, monitor `410 Gone`, remove old route/backends after the support period and retain audit data according to policy.

## Lifecycle policy example — illustrative, not a real date commitment

- **Announcement:** publish new contract and changelog to consumers.
- **Deprecation:** document intention to retire v1. Use `Deprecation` (RFC 9745) header, **without** changing successful v1 behavior.
- **Sunset:** communicate a future retirement time with `Sunset` (RFC 8594). The local lab uses **2027-01-01** and **2027-06-30** as fictional dates.
- **Retirement:** gateway denies v1; local simulation returns `410 Gone` while v2 remains available.
- **Removal:** after monitoring and any retention obligations, remove the v1 Service/Route/Deployment.

OpenAPI `info.version` is the semantic contract revision (1.0.0/1.1.0/2.0.0); URI `/v1` or `/v2` identifies a **major compatibility line**. They are related but not the same thing.

### Alternative versioning models

| Strategy | Example | Trade-off |
|---|---|---|
| URL major version | `/v1/placeorder`, `/v2/placeorder` | Easy to discover and route; endpoints evolve |
| Custom header | `X-Api-Version: 2` | Stable URI; more difficult caches/diagnostics |
| Endpoint name | `/placeorder_v2` | Simple but proliferates names |
| Separate API product / application plan | distinct 3scale Products | Easier adoption tracking and retirement; more gateway configuration |

Do not use all approaches simultaneously without a coherent strategy. This module **implements URL versioning**, as in the original Red Hat solution pattern.

## References

[Original Red Hat API Versioning Solution Pattern](https://www.solutionpatterns.io/solution-pattern-api-versioning/api-versioning/index.html) · [Architecture](https://www.solutionpatterns.io/solution-pattern-api-versioning/api-versioning/02-architecture.html) · [Workshop](https://www.solutionpatterns.io/solution-pattern-api-versioning/api-versioning/03-demo.html) · [RFC 9745](https://www.rfc-editor.org/rfc/rfc9745) · [RFC 8594](https://www.rfc-editor.org/rfc/rfc8594).
