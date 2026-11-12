# Kubernetes course — self-contained Kubernetes 1.37 execution track

> **Scope:** course modules **00–08**. Module **09 OpenShift** is intentionally excluded.
>
> **Status (11 November 2026):** The executable 2026 path has been **statically audited**: prerequisites, source-file links, versioned API usage, command paths, object names, intended port mappings, expected results and cleanup are documented. **No live multi-module cluster execution has been carried out.** Real success also depends on your node environment, connectivity, installed tools and the availability of upstream container images or charts.
>
> The original DOCX/PPTX/ZIP and historical lecture notes document the **2021 course** and are preserved for study. **Modules 01–08 now contain their complete Kubernetes 1.37 labs directly in their original README files**, followed by the untouched historical lecture content. The separate `*-2026.md` files remain as compatibility pointers to those integrated lessons.

## Start here — choose your lab

**Supported default:** Kubernetes **1.37**, **containerd 2.x**, **Calico 3.33 / VXLAN / BGP disabled**, Ubuntu Server 24.04 LTS on one control-plane and two worker VMs. All node IPs and pod/service subnet examples must be adapted if they overlap your network.

1. Start with **[Module 02 README](./02.%20Cluster%20Setup%20and%20Management/README.md#kubernetes-137-integrated-labs)**, sections **0–8**, to build the default cluster. This is the foundation for Modules 01, 03–08.
2. Verify all three Nodes Ready, Calico healthy and client kubeconfig working.
3. Follow the **module guides below**, completing one lab at a time with the prescribed preflight, validation and cleanup. Use fresh clusters for destructive etcd-restore/upgrade and optional alternate-CNI/Ingress labs.
4. Use **[Module 08 integrated exam](./08.%20Exam%20Preparation/README.md#kubernetes-137-integrated-labs)** to assess your skills after the previous modules.

### Module and exercise navigation

The **README in each module is now the canonical course chapter**, combining the supported 1.37 lab with all the original notes. The former `*-2026.md` paths lead to compatibility pointers, not a second divergent version of the course.

| Module | Executable 2026 guide | Coverage / expected result |
|---|---|---|
| **00 — Resources** | [Module 00 README](./00.%20Resources/README.md) | Exam blueprint and course prerequisites; not a runnable lab |
| **01 — Core Concepts** | [Integrated Module 01 README](./01.%20Core%20Concepts/Readme.md) | Four tasks: Namespaces, labels, Pods, NodePort Service, declarative files and optional kind |
| **02 — Cluster Setup & Management** | [Integrated Module 02 README](./02.%20Cluster%20Setup%20and%20Management/README.md) | Basic/HA kubeadm clusters, etcd, upgrades, Calico; Minikube/kind/Vagrant homework |
| **03 — Security & Policies** | [Integrated Module 03 README](./03.%20Security%20and%20Policies/README.md) | X.509 users, RBAC, quota/LimitRange, Calico NetworkPolicy allow/deny tests |
| **04 — Storage & Persistence** | [Integrated Module 04 README](./04.%20Storage%20and%20Persistence/README.md) | NFS, ConfigMaps/Secrets, three PVC/PV StatefulSet, Retain, supported Git init-container alternative |
| **05 — Advanced Concepts** | [Integrated Module 05 README](./05.%20Advanced%20Concepts/README.md) | Init containers, HTTP page, F5 NGINX HTTPS fanout, Traefik and modern HPA |
| **06 — Observability & Troubleshooting** | [Integrated Module 06 README](./06.%20Observability%20and%20Troubleshooting/README.md) | Broken scenarios and corrected manifests, NFS StatefulSet, logging/probes/debug |
| **07 — Templating & Helm** | [Integrated Module 07 README](./07.%20Templating%20Tools%20and%20Package%20Management/README.md) | sed, Kustomize overlays, Helm chart and ConfigMap HTML/SVG |
| **08 — Exam Preparation** | [Integrated Module 08 README](./08.%20Exam%20Preparation/README.md) | Nine-task/36-point, three-namespace practice exam with setup and separate solutions |

**Recommended practical order:** 02 setup → 01 → 02 homework/extensions → 03 → 04 → 05 → 06 → 07 → 08 exam. Do not run every lab simultaneously. Modules often re-use namespace `homework`, NodePort **30001**, **31000**, **32000**, **32001** or **32002**. Destroy/clean up the earlier lab before reserving the same ports for the next.


## Further modules — sequential OpenShift and application tracks

The Kubernetes **1.37 static audit above covers Modules 00–08 only**. Continue with **Module 09**, followed by **Module 10**, then the API and event-driven modernization modules. Each has standalone prerequisites; **none changes** the default kubeadm/Calico lab baseline.

| Module | Standalone lesson and practical goal |
|---|---|
| **09 — OpenShift** | [OpenShift](./09.%20OpenShift/README.md) — Projects, Builds, Routes, security, storage and virtualization |
| **10 — Full-stack JavaScript on OpenShift** | [URL Shortener](./10.%20Full-Stack%20JavaScript%20on%20OpenShift/README.md) — Node.js frontend/backend/redirector, PostgreSQL, Docker Compose, five labs |
| **11 — API-First Development & API Management** | [API-First](./11.%20API-First%20Development%20and%20API%20Management/README.md) — OpenAPI contracts, registry, mocking, ASP.NET Core |
| **12 — API Versioning & Lifecycle Management** | [API Versioning](./12.%20API%20Versioning%20and%20Lifecycle%20Management/README.md) — SemVer, compatibility, OrderPlacement v1/v2, sunset |
| **13 — API Management & Service Mesh** | [Service Mesh](./13.%20API%20Management%20and%20Service%20Mesh/README.md) — Travelz, partner APIs, canary, Istio mTLS |
| **14 — Event-Driven Sentiment Analysis** | [Event-driven analytics](./14.%20Event-Driven%20Sentiment%20Analysis/README.md) — Kafka, CloudEvents, Globex, PostgreSQL, InfluxDB/Grafana, Knative |
| **15 — CDC Legacy Modernization** | [CDC modernization](./15.%20CDC%20Legacy%20Modernization/README.md) — PostgreSQL WAL, Debezium Kafka Connect, search and cashback projections |

**Verification boundary:** Module 10 CI exercises actual PostgreSQL and Node services, whereas live OpenShift acceptance requires a separate authorized cluster and is **not** claimed here.

## External dependencies that cannot be packaged as static documents

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

## Rules preventing the historical problems

- **Only one CNI per cluster.** Use Calico 3.33 for the main kubeadm learning track. Do **not** install historic Weave/Antrea/Flannel manifests on top of it. Optional Flannel uses a separate clean cluster.
- **Use supported Kubernetes APIs.** The old `PodSecurityPolicy`, `autoscaling/v2beta2` HPA and `gitRepo` volume driver no longer work on 1.37. Modern alternatives are identified in the relevant guides.
- **Distinguish ports.** NodePort on a Node, Service `port`, Service `targetPort` to a Pod and Ingress HTTPS listener 443 are different things.
- **Respect PV reclaim policy.** On static NFS, `Retain` preserves files when a PVC is deleted and requires manual reclamation of Released PVs. Do not wipe NFS directories while Pods still use them.
- **Keep lab clusters isolated.** The etcd restore and upgrade chapters use separate disposable clusters; a failed control plane is an intentional experiment, not a reason to damage a shared lab.
- **Do not execute raw 2021 author scripts.** Use the integrated 1.37 exercise sections in each module README. Preserve DOCX/ZIP/screenshots as historical examples, including the original multi-cluster exam; modern Exam 2026 uses three **logical namespaces** on one cluster instead.

## Verification recipe

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

## Source

Official [Kubernetes documentation](https://kubernetes.io/docs/home/), [Calico documentation](https://docs.tigera.io/calico/latest/), [Kustomize](https://kustomize.io/), [Helm](https://helm.sh/docs/) and [Traefik Helm chart](https://github.com/traefik/traefik-helm-chart).
