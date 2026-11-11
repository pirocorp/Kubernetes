# Kubernetes course — self-contained Kubernetes 1.37 execution track

> **Scope:** course modules **00–08**. Module **09 OpenShift** is intentionally excluded.
>
> **Status (11 November 2026):** The executable 2026 path has been **statically audited**: prerequisites, source-file links, versioned API usage, command paths, object names, intended port mappings, expected results and cleanup are documented. **No live multi-module cluster execution has been carried out.** Real success also depends on your node environment, connectivity, installed tools and the availability of upstream container images or charts.
>
> The original DOCX/PPTX/ZIP and historical README commands document the **2021 course** and are retained for study. This index deliberately distinguishes them from the modern executable `*-2026.md` guides.

## Start here — choose your lab

**Supported default:** Kubernetes **1.37**, **containerd 2.x**, **Calico 3.33 / VXLAN / BGP disabled**, Ubuntu Server 24.04 LTS on one control-plane and two worker VMs. All node IPs and pod/service subnet examples must be adapted if they overlap your network.

1. Start with **[Module 02 SETUP-2026.md](./02.%20Cluster%20Setup%20and%20Management/SETUP-2026.md)**, sections **0–8**, to build the default cluster. This is the foundation for Modules 01, 03–08.
2. Verify all three Nodes Ready, Calico healthy and client kubeconfig working.
3. Follow the **module guides below**, completing one lab at a time with the prescribed preflight, validation and cleanup. Use fresh clusters for destructive etcd-restore/upgrade and optional alternate-CNI/Ingress labs.
4. Use **[Module 08 EXAM-2026.md](./08.%20Exam%20Preparation/EXAM-2026.md)** to assess your skills after the previous modules.

### Module and exercise navigation

| Module | Executable 2026 guide | Coverage / expected result |
|---|---|---|
| **00 — Resources** | [Module 00 README](./00.%20Resources/README.md) | Exam blueprint and course prerequisites; not a runnable lab |
| **01 — Core Concepts** | [CORE-2026.md](./01.%20Core%20Concepts/CORE-2026.md) | Four tasks: Namespaces, labels, Pods, NodePort Service, declarative files and optional kind |
| **02 — Cluster Setup & Management** | [SETUP-2026.md](./02.%20Cluster%20Setup%20and%20Management/SETUP-2026.md) + [HOMEWORK-2026.md](./02.%20Cluster%20Setup%20and%20Management/HOMEWORK-2026.md) | Basic/HA kubeadm clusters, etcd, upgrades, Calico; optional Minikube/kind/Vagrant homework |
| **03 — Security & Policies** | [SECURITY-2026.md](./03.%20Security%20and%20Policies/SECURITY-2026.md) | X.509 users, RBAC, quota/LimitRange, Calico NetworkPolicy allow/deny tests |
| **04 — Storage & Persistence** | [STORAGE-2026.md](./04.%20Storage%20and%20Persistence/STORAGE-2026.md) | NFS setup, ConfigMaps/Secrets, three PVC/PV StatefulSet, `Retain`, supported Git init-container alternative |
| **05 — Advanced Concepts** | [ADVANCED-2026.md](./05.%20Advanced%20Concepts/ADVANCED-2026.md) | Init containers, HTTP page, F5 NGINX HTTPS fanout, alternative Traefik controller, modern HPA |
| **06 — Observability & Troubleshooting** | [LAB-2026.md](./06.%20Observability%20and%20Troubleshooting/LAB-2026.md) | Intentionally broken scenario 2 & 3, corrected solutions, four NFS StatefulSet PVs, logging/probes/debug checks |
| **07 — Templating & Helm** | [LAB-2026.md](./07.%20Templating%20Tools%20and%20Package%20Management/LAB-2026.md) | All three tasks: sed, modern Kustomize overlays, version-pinned Helm chart + ConfigMap HTML/SVG |
| **08 — Exam Preparation** | [EXAM-2026.md](./08.%20Exam%20Preparation/EXAM-2026.md) | Modern 9-task/36-point, three-namespace practice exam with reproducible setup and separate solutions |

**Recommended practical order:** 02 setup → 01 → 02 homework/extensions → 03 → 04 → 05 → 06 → 07 → 08 exam. Do not run every lab simultaneously. Modules often re-use namespace `homework`, NodePort **30001**, **31000**, **32000**, **32001** or **32002**. Destroy/clean up the earlier lab before reserving the same ports for the next.

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
- **Do not execute raw 2021 author scripts.** Use the modern `*-2026.md` entry points. Preserve DOCX/ZIP/screenshots as historical examples, including the original multi-cluster exam; modern Exam 2026 uses three **logical namespaces** on one cluster instead.

## Verification recipe

Before each module:

```bash
kubectl config current-context
kubectl version
kubectl get nodes -o wide
kubectl get pods -A
kubectl get tigerastatus
```

The **full acceptance** for each lab is in that module's 2026 guide and covers:
1. **Preflight:** context, compatible versions, service/network/storage prerequisites and unused ports.
2. **Apply:** explicit paths to versioned, modern manifests or commands.
3. **Validate:** `kubectl get/describe`, rollout, status, endpoints, logs, HTTP tests and expected outputs.
4. **Troubleshoot:** distinguish image, CNI, permission, policy, storage and node connectivity faults.
5. **Cleanup:** reset the lab so a following task is not blocked by names, ports or released PVs.

A passing **static document audit** proves the instructions and source references are internally consistent to the extent checked. It does **not** claim a tested runtime success or permanently guarantee external resources.

## Historical exam vs modern simulation

Original `M8-Practice-Exam-Preparation-Simulation-Exam.docx` described three Debian 10 / Kubernetes 1.21.6 clusters; its attached ZIP has only part of the historic setup. The new [EXAM-2026.md](./08.%20Exam%20Preparation/EXAM-2026.md) provides a current, reproducible **replacement simulation** covering the original skills, not a line-by-line migration or a literal three-cluster reproduction. Historical materials remain intact.

## Source

Official [Kubernetes documentation](https://kubernetes.io/docs/home/), [Calico documentation](https://docs.tigera.io/calico/latest/), [Kustomize](https://kustomize.io/), [Helm](https://helm.sh/docs/) and [Traefik Helm chart](https://github.com/traefik/traefik-helm-chart).
