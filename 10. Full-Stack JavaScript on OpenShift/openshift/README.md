# Module 10 OpenShift manifests and deployment paths

The complete commands, prerequisites, validation and selective cleanup are in the corresponding hands-on labs:

- [10-B — Frontend container and Route](../labs/LAB-02-FRONTEND-CONTAINER.md)
- [10-C — PostgreSQL template](../labs/LAB-03-POSTGRESQL.md)
- [10-D — Backend Source-to-Image and configuration](../labs/LAB-04-BACKEND-S2I.md)
- [10-E — Existing redirector image and four-tier integration](../labs/LAB-05-REDIRECTOR-INTEGRATION.md)

Included resource: [frontend-route.yaml](./frontend-route.yaml), which exposes only the website over HTTPS. Backend, redirector and database remain internal ClusterIP Services. The official Red Hat learning path exposes additional Routes, but doing so is unnecessary for this design because the frontend implements a safe internal reverse proxy.

The exercises are fully reproducible locally with Docker Compose; live OpenShift labs need an authorized Project, quota, supported Node.js builder or Docker build strategy, and the `postgresql-ephemeral` template for the template-specific lab. Check all prerequisites before applying cluster resources. The course never installs Operators or alters shared namespaces.
