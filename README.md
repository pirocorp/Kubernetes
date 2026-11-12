# Kubernetes & OpenShift — self-contained hands-on course

**16 modules (00–15)** · **Kubernetes 1.37 baseline** · Ubuntu Server 24.04 LTS · containerd 2.x · Calico 3.33 (VXLAN; BGP disabled)

> **Start here.** This `README.md` is the **single course guide and navigation hub**. Each module's own README contains its explanations, current hands-on labs, expected results, troubleshooting and cleanup. **Modules 01–08 also preserve the complete original 2021 lecture notes** for comparison. The [original root-level foundations lecture](./README-LEGACY-FOUNDATIONS.md) is archived intact and available for study.

> **Verification boundary:** The Kubernetes 1.37 modules 00–08 have been **statically audited** for prerequisites, source references, command paths, manifest versions, expected results and cleanup. **They have not been executed end-to-end on a live Kubernetes 1.37 cluster**; actual success requires accessible VMs, images/charts and permissions. Other modules have their own distinct validation status; a passing CI run is not proof of a real OpenShift deployment.

## Getting started

1. **Read [Module 00 — resources and blueprint](./00.%20Resources/README.md)** to understand the original learning objectives and assessment scope.
2. **Build your lab cluster** by following [Module 02 — integrated Kubernetes 1.37 setup](./02.%20Cluster%20Setup%20and%20Management/README.md#kubernetes-137-integrated-labs), sections **0–8**. The default topology is one control-plane VM and two worker VMs. Check that all nodes are `Ready`, Calico is healthy and your workstation `kubectl` context works.
3. **Study [Module 01](./01.%20Core%20Concepts/Readme.md)**, then return to Module 02 for its optional homework and advanced cluster management; continue through Modules 03–08 in order. **Complete one lab at a time**, including its verification and cleanup.
4. **Take [Module 08 — practice exam](./08.%20Exam%20Preparation/README.md#kubernetes-137-integrated-labs)** after the preceding modules. Continue with Module 09 OpenShift, then Modules 10–15 for full-stack, API, service-mesh, event-driven and CDC projects.

**Recommended lab sequence:** 02 setup → 01 → 02 homework/extensions → 03 → 04 → 05 → 06 → 07 → 08 exam → 09 → 10 → 11 → 12 → 13 → 14 → 15.

## Modules and learning outcomes

| Module | Full lesson / lab | Learning outcome |
|---|---|---|
| 00 — Resources | [Module 00 README](./00.%20Resources/README.md) | Exam blueprint and course prerequisites; not a runnable lab |
| 01 — Core Concepts | [Integrated Module 01 README](./01.%20Core%20Concepts/Readme.md) | Four tasks: Namespaces, labels, Pods, NodePort Service, declarative files and optional kind |
| 02 — Cluster Setup & Management | [Integrated Module 02 README](./02.%20Cluster%20Setup%20and%20Management/README.md) | Basic/HA kubeadm clusters, etcd, upgrades, Calico; Minikube/kind/Vagrant homework |
| 03 — Security & Policies | [Integrated Module 03 README](./03.%20Security%20and%20Policies/README.md) | X.509 users, RBAC, quota/LimitRange, Calico NetworkPolicy allow/deny tests |
| 04 — Storage & Persistence | [Integrated Module 04 README](./04.%20Storage%20and%20Persistence/README.md) | NFS, ConfigMaps/Secrets, three PVC/PV StatefulSet, Retain, supported Git init-container alternative |
| 05 — Advanced Concepts | [Integrated Module 05 README](./05.%20Advanced%20Concepts/README.md) | Init containers, HTTP page, F5 NGINX HTTPS fanout, Traefik and modern HPA |
| 06 — Observability & Troubleshooting | [Integrated Module 06 README](./06.%20Observability%20and%20Troubleshooting/README.md) | Broken scenarios and corrected manifests, NFS StatefulSet, logging/probes/debug |
| 07 — Templating & Helm | [Integrated Module 07 README](./07.%20Templating%20Tools%20and%20Package%20Management/README.md) | sed, Kustomize overlays, Helm chart and ConfigMap HTML/SVG |
| 08 — Exam Preparation | [Integrated Module 08 README](./08.%20Exam%20Preparation/README.md) | Nine-task/36-point, three-namespace practice exam with setup and separate solutions |
| 09 — OpenShift | [OpenShift](./09.%20OpenShift/README.md) | Projects, Builds, Routes, security, storage and virtualization |
| 10 — Full-stack JavaScript on OpenShift | [URL Shortener](./10.%20Full-Stack%20JavaScript%20on%20OpenShift/README.md) | Node.js frontend/backend/redirector, PostgreSQL, Docker Compose, five labs |
| 11 — API-First Development & API Management | [API-First](./11.%20API-First%20Development%20and%20API%20Management/README.md) | OpenAPI contracts, registry, mocking, ASP.NET Core |
| 12 — API Versioning & Lifecycle Management | [API Versioning](./12.%20API%20Versioning%20and%20Lifecycle%20Management/README.md) | SemVer, compatibility, OrderPlacement v1/v2, sunset |
| 13 — API Management & Service Mesh | [Service Mesh](./13.%20API%20Management%20and%20Service%20Mesh/README.md) | Travelz, partner APIs, canary, Istio mTLS |
| 14 — Event-Driven Sentiment Analysis | [Event-driven analytics](./14.%20Event-Driven%20Sentiment%20Analysis/README.md) | Kafka, CloudEvents, Globex, PostgreSQL, InfluxDB/Grafana, Knative |
| 15 — CDC Legacy Modernization | [CDC modernization](./15.%20CDC%20Legacy%20Modernization/README.md) | PostgreSQL WAL, Debezium Kafka Connect, search and cashback projections |

**Chapter structure:** Open each module's **README**. For Modules 01–08, the supported Kubernetes 1.37 labs are integrated directly into the lesson and the original explanations remain under a marked *historical reference* section. The old `*-2026.md` URLs are compatibility pointers, not a second curriculum. For Modules 09–15, follow their README and linked labs.

## Lab setup and cross-module dependencies

| Dependency | What you must supply or verify |
|---|---|
| Virtual machines/host network | OS installation, unique hostnames, host IPs, hypervisor/VM capabilities and appropriate firewall |
| Workstation tools | `kubectl`, `helm`, `openssl`, `curl`, `sed`; optionally Minikube, kind, Vagrant, VirtualBox |
| Container registries & Helm charts | Working HTTPS/DNS and the upstream images referenced by the manifests; some historical third-party teaching images may cease to be published |
| NFS storage | A separate NFS server and exports for Modules 04/06; static NFS does **not** appear magically within a kubeadm cluster |
| Ingress | Matching F5 NGINX controller + IngressClass for its rewrite annotations; Traefik is an **alternative** only for the third-controller task |
| Kubernetes node credentials | Valid kubeconfig/current context, permissions to manage lab objects; only disposable labs sign client certificates with kubeadm's CA key |
| NodePorts | Reachable node IP and permitted TCP port, or an alternative local `kubectl port-forward` as documented |
| Quotas/metrics | Metrics Server before CPU HPA; adequate CPU/memory capacity for requested replicas |

These dependencies are **specified** in the relevant module guides. A fully self-contained written procedure does not mean a physical cluster can be conjured without hosts or that an upstream image is guaranteed to stay downloadable indefinitely.

**Resource collisions:** The labs often reuse namespace `homework` and NodePorts **30001, 31000, 32000, 32001 and 32002**. Clean up the previous lab before reserving them again. Use **fresh disposable clusters** for destructive etcd restore/upgrade work and optional alternate-CNI or Ingress configurations. Adapt node IPs and pod/service CIDRs when they overlap the real network.

## Safety and compatibility rules

- **Only one CNI per cluster.** Use Calico 3.33 for the main kubeadm learning track. Do **not** install historic Weave/Antrea/Flannel manifests on top of it. Optional Flannel uses a separate clean cluster.
- **Use supported Kubernetes APIs.** The old `PodSecurityPolicy`, `autoscaling/v2beta2` HPA and `gitRepo` volume driver no longer work on 1.37. Modern alternatives are identified in the relevant guides.
- **Distinguish ports.** NodePort on a Node, Service `port`, Service `targetPort` to a Pod and Ingress HTTPS listener 443 are different things.
- **Respect PV reclaim policy.** On static NFS, `Retain` preserves files when a PVC is deleted and requires manual reclamation of Released PVs. Do not wipe NFS directories while Pods still use them.
- **Keep lab clusters isolated.** The etcd restore and upgrade chapters use separate disposable clusters; a failed control plane is an intentional experiment, not a reason to damage a shared lab.
- **Do not execute raw 2021 author scripts.** Use the integrated 1.37 exercise sections in each module README. Preserve DOCX/ZIP/screenshots as historical examples, including the original multi-cluster exam; modern Exam 2026 uses three **logical namespaces** on one cluster instead.

## Standard lab verification

Before each module:

```bash
kubectl config current-context
kubectl version
kubectl get nodes -o wide
kubectl get pods -A
kubectl get tigerastatus
```

The **full acceptance** for each lab is inside that module's integrated README and covers:
1. **Preflight:** context, compatible versions, service/network/storage prerequisites and unused ports.
2. **Apply:** explicit paths to versioned, modern manifests or commands.
3. **Validate:** `kubectl get/describe`, rollout, status, endpoints, logs, HTTP tests and expected outputs.
4. **Troubleshoot:** distinguish image, CNI, permission, policy, storage and node connectivity faults.
5. **Cleanup:** reset the lab so a following task is not blocked by names, ports or released PVs.

A passing **static document audit** proves the instructions and source references are internally consistent to the extent checked. It does **not** claim a tested runtime success or permanently guarantee external resources.

## Historical exam vs modern simulation

Original `M8-Practice-Exam-Preparation-Simulation-Exam.docx` described three Debian 10 / Kubernetes 1.21.6 clusters; its attached ZIP has only part of the historic setup. The modern exam integrated into [Module 08 README](./08.%20Exam%20Preparation/README.md#kubernetes-137-integrated-labs) provides a current, reproducible **replacement simulation** covering the original skills, not a line-by-line migration or a literal three-cluster reproduction. Historical materials remain intact.

## Original learning material

The [foundations lecture previously stored in the root README](./README-LEGACY-FOUNDATIONS.md), the original module theory, and the DOCX/PPTX/ZIP exercises remain available for historical study. The historical 2021 three-cluster exam is **not** a drop-in Kubernetes 1.37 exercise; the modern Module 08 simulation deliberately uses three logical namespaces on one cluster.

## Source

Official [Kubernetes documentation](https://kubernetes.io/docs/home/), [Calico documentation](https://docs.tigera.io/calico/latest/), [Kustomize](https://kustomize.io/), [Helm](https://helm.sh/docs/) and [Traefik Helm chart](https://github.com/traefik/traefik-helm-chart).
