# Module 00 — Course resources and blueprint (Kubernetes 1.37 track)

> **NOTE (2026):** Module 00 is **not an executable lab**. It contains the original **M0-Blueprint-Practice-Exam.docx** and introduction slides. The blueprint's subject categories remain useful, but older materials are a historical 2021 snapshot.

## How to use these resources

1. Read the [course-wide 2026 roadmap](../COURSE-2026.md) for cluster prerequisites, module ordering, checks and cleanup.
2. Prepare a Kubernetes **1.37 + containerd 2 + Calico 3.33** cluster from [Module 02 integrated README](../02.%20Cluster%20Setup%20and%20Management/README.md#kubernetes-137-integrated-labs). Unlike the original slides, this is the modern documented course environment.
3. Work through Modules 01–07 using the **integrated 1.37 lab in each module README**, then compare with the preserved original lecture in that same file.
4. Take the modern [Module 08 integrated exam](../08.%20Exam%20Preparation/README.md#kubernetes-137-integrated-labs) as a practical final assessment.

## Learning objectives

The original blueprint covers: Pods, Services and Deployments; namespaces/labels/annotations; cluster setup, upgrades, troubleshooting and configuration; requests/limits/quotas, NetworkPolicy, auth/RBAC/admission; PV/PVC, StatefulSets, ConfigMaps and Secrets; multi-container Pods, scheduling, HPA, Jobs/CronJobs and Ingress; logs/probes; Kustomize and Helm. Modern modules retain these themes while replacing the unsupported API versions and retired plugins.

**Important exam distinction:** the original Module08 simulation targeted 3 *independent* Kubernetes 1.21.6 clusters. The new 2026 assessment deliberately uses **one** Kubernetes 1.37 Calico cluster and three isolated namespaces. They are **not** the same exam infrastructure. The old DOCX/ZIP is preserved for study, not an executable 1.37 setup.

## Static validation criteria

Every integrated module README supplies: platform prerequisites, exact file paths/commands, target state, verification commands, failure diagnostics, and teardown. No live lab has been run as part of this documentation modernization.


## Learning bridge: original blueprint to the current course

| Original skill area | Modern chapter and validation focus |
|---|---|
| Kubernetes objects, Pods, Services and controllers | [01 — Core Concepts](../01.%20Core%20Concepts/Readme.md): desired state, matching selectors, deployed applications and reachable endpoints |
| Cluster components, maintenance and resilience | [02 — Cluster Setup](../02.%20Cluster%20Setup%20and%20Management/README.md): kubeadm, containerd, Calico, etcd backup/recovery and HA |
| Authentication, policy and resource governance | [03 — Security](../03.%20Security%20and%20Policies/README.md): certificate identities, RBAC, quotas and tested NetworkPolicies |
| Persistence, configuration and StatefulSets | [04 — Storage](../04.%20Storage%20and%20Persistence/README.md): static NFS PV/PVC, reclaim behavior and configuration injection |
| Pod patterns, scheduling, ingress and scaling | [05 — Advanced](../05.%20Advanced%20Concepts/README.md): init containers, HTTPS fanout, ingress variants and autoscaling |
| Application health and systematic debugging | [06 — Observability](../06.%20Observability%20and%20Troubleshooting/README.md): diagnose broken probes, Services and NFS |
| Reusable resource templates and packaging | [07 — Templating](../07.%20Templating%20Tools%20and%20Package%20Management/README.md): sed, Kustomize and Helm |
| Timed applied assessment | [08 — Exam](../08.%20Exam%20Preparation/README.md): nine practical tasks and separate grading key |

The original blueprint and introduction slides remain unchanged. This bridge maps their learning objectives to the supported labs; it does not claim that the old exam infrastructure is supported.
