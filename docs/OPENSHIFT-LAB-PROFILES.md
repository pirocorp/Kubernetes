# OpenShift lab profiles — Modules 09–15

This guide makes **platform prerequisites explicit**. It does not claim that an arbitrary Developer Sandbox includes Virtualization, Istio, Knative or managed CDC services. **External third-party teaching images in Kubernetes Modules 01–07 remain out of scope.**

## Choose a profile

| Profile | Required | Exercises | Boundary |
|---|---|---|---|
| **L — local** | Docker/Compose; module-specific .NET, Node, Python | 10-A, 11-A–D, 12-A–D, 13-A–C, 14-A–D, 15-A–D | Real local Kafka/CDC where indicated; no OpenShift operators |
| **S — Developer Sandbox / namespace** | Own OpenShift Project, `oc`, namespace RBAC, quotas, network/image access | 09-A–D, 10-B–E, 11-E, 12-E, 13-D when permissions permit | Does not grant VM, mesh, Knative or managed services |
| **P — operator-enabled OpenShift** | Existing operator control planes and admin-provisioned dependencies, plus S | 09-E VM, 13-E Istio, 14-E Knative KafkaSource, 15-E managed CDC | Cannot be fully supplied by repository YAML or a restricted Sandbox |

**Never install cluster-scoped Operators or elevate privileges inside a shared Developer Sandbox.** If P is unavailable, a fallback may teach some skills but **must not** be recorded as a completed VM/Istio/Knative deployment.

Run a read-only capabilities check with your own current context (from repo root):

```bash
oc whoami
oc project
oc version
bash scripts/check-openshift-profile.sh m09-vm
# or m13-mesh | m14-knative | m15-cdc
```

The script checks only namespace API discovery and RBAC — a successful check is **not** a live operator health or end-to-end test. Do not share kubeconfig, tokens or Secret values.

## Module 09-E — Virtualization

Requires platform-installed OpenShift Virtualization/KubeVirt, CDI/DataVolumes, a **permitted Linux VM template/boot image** in the Console Catalog, working PVC storage, VM quotas and namespaced VirtualMachine rights.

```bash
bash scripts/check-openshift-profile.sh m09-vm
oc api-resources --api-group=kubevirt.io
oc api-resources --api-group=cdi.kubevirt.io
```

The administrator must make a suitable boot template/storage available; application developers must inspect the actual Project quota and VM state. Follow [09-E full cutover](../09.%20OpenShift/labs/LAB-05-VIRTUALIZATION-CUTOVER-2026.md). If Virtualization is absent, the lab's **container-only Route cutover** is executable but **does not prove the VM lifecycle**. Check VM Running state before any rollback; limited Sandbox sessions can stop VMs.

## Module 10-C — template-free PostgreSQL

The [complete database lab](../10.%20Full-Stack%20JavaScript%20on%20OpenShift/labs/LAB-03-POSTGRESQL.md) now includes two **owned namespace manifests**:

- [Deployment + 1Gi PVC](../10.%20Full-Stack%20JavaScript%20on%20OpenShift/openshift/postgres-pvc.yaml): dynamic PVC + StorageClass required, persistent across Pod recreation if correctly bound.
- [Deployment + emptyDir](../10.%20Full-Stack%20JavaScript%20on%20OpenShift/openshift/postgres-ephemeral.yaml): no StorageClass needed, data are ephemeral.
- Original Red Hat `postgresql-ephemeral` template: optional third path, **not** a prerequisite for Labs 10-D/E.

All modes supply `m10-postgres:5432` and `m10-db-url`, without a public DB Route.

## Module 13-E — real Istio Service Mesh

Requires an installed and **healthy** service mesh control plane, namespace enrollment/allowed revision, functional sidecar injector and namespaced rights for `VirtualService`, `DestinationRule`, `PeerAuthentication` and `AuthorizationPolicy`.

```bash
bash scripts/check-openshift-profile.sh m13-mesh
oc get pods -l training=module13 -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].name}{"\n"}{end}'
```

Check actual **`istio-proxy` sidecars** after injection, before enabling STRICT mTLS. Then [13-E](../13.%20API%20Management%20and%20Service%20Mesh/labs/LAB-05-REAL-ISTIO-MESH.md) must demonstrate real 80/20, unauthorized identity rejection and rollback. [13-C](../13.%20API%20Management%20and%20Service%20Mesh/labs/LAB-03-TRAFFIC-CANARY-RESILIENCE.md) is only a deterministic local routing **simulation**.

## Module 14-E — Knative Eventing and KafkaSource

Requires platform-installed/healthy OpenShift Serverless Knative Eventing, Broker implementation and KafkaSource controller; user rights to Broker/Trigger/KafkaSource; an accessible **lab Kafka** broker with the four source/topics described by the [14-E lab](../14.%20Event-Driven%20Sentiment%20Analysis/labs/LAB-05-OPENSHIFT-KNATIVE.md).

```bash
bash scripts/check-openshift-profile.sh m14-knative
oc api-resources --api-group=eventing.knative.dev
oc api-resources --api-group=sources.knative.dev
```

The source example uses a plaintext Kafka listener, **not SASL/TLS**; only use an authorized isolated training network. Platform admin supplies the **actual** Kafka bootstrap DNS and topics. Require `Ready=True` for Broker, KafkaSource, Triggers plus actual HTTP callbacks. [14-C](../14.%20Event-Driven%20Sentiment%20Analysis/labs/LAB-03-KAFKA-STORAGE-DASHBOARD.md) demonstrates **real local Kafka/Postgres/Influx** but not a live Knative Broker. The local callback fixture proves the callback **contract**, not the controller.

## Module 15-E — external managed CDC

Requires two separately credentialed PostgreSQL DBs, a real Debezium PostgreSQL connector with publication/replication slot, a reachable Kafka broker and **four** CDC topics, healthy Elasticsearch, plus network/DNS permissions from the application namespace.

```bash
bash scripts/check-openshift-profile.sh m15-cdc
# The platform administrator must verify separately:
# PostgreSQL ownership/access, Debezium task RUNNING, WAL slot,
# topic existence and consumer lag, Elasticsearch index/health.
```

The [15-E runbook](../15.%20CDC%20Legacy%20Modernization/labs/LAB-05-OPENSHIFT-RUNBOOK.md) explains the application-specific configurations. **Its Kafka client is plaintext and Elasticsearch client HTTP**; enterprise SASL/TLS cannot be enabled simply by inventing a Secret. If managed dependencies are not provisioned, [15-B–D](../15.%20CDC%20Legacy%20Modernization/labs/LAB-02-DEBEZIUM-KAFKA.md) provide **real end-to-end CDC** from Docker Compose, without falsely claiming a deployed managed OpenShift stack.

## What constitutes completion

For every practical module record (1) selected L/S/P profile and code commit, (2) actual namespace and **PASS/BLOCKED** preflight without credentials, (3) Ready resources **plus** the module's functional HTTP/SQL/event/security assertion, (4) selective cleanup of owned resources. A skipped external prerequisite is a **blocked lab**, not a pass. Successful static CI is **not** proof of a working live OpenShift cluster.
