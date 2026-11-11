# Module 00 — Course resources and blueprint (Kubernetes 1.37 track)

> **NOTE (2026):** Module 00 is **not an executable lab**. It contains the original **M0-Blueprint-Practice-Exam.docx** and introduction slides. The blueprint's subject categories remain useful, but older materials are a historical 2021 snapshot.

## How to use these resources

1. Read the [course-wide 2026 roadmap](../COURSE-2026.md) for cluster prerequisites, module ordering, checks and cleanup.
2. Prepare a Kubernetes **1.37 + containerd 2 + Calico 3.33** cluster from [Module 02 SETUP-2026.md](../02.%20Cluster%20Setup%20and%20Management/SETUP-2026.md). Unlike the original slides, this is the modern documented course environment.
3. Work through Modules 01–07 using each module's **2026** lab guide.
4. Take the modern [Module 08 EXAM-2026.md](../08.%20Exam%20Preparation/EXAM-2026.md) as a practical final assessment.

## Learning objectives

The original blueprint covers: Pods, Services and Deployments; namespaces/labels/annotations; cluster setup, upgrades, troubleshooting and configuration; requests/limits/quotas, NetworkPolicy, auth/RBAC/admission; PV/PVC, StatefulSets, ConfigMaps and Secrets; multi-container Pods, scheduling, HPA, Jobs/CronJobs and Ingress; logs/probes; Kustomize and Helm. Modern modules retain these themes while replacing the unsupported API versions and retired plugins.

**Important exam distinction:** the original Module08 simulation targeted 3 *independent* Kubernetes 1.21.6 clusters. The new 2026 assessment deliberately uses **one** Kubernetes 1.37 Calico cluster and three isolated namespaces. They are **not** the same exam infrastructure. The old DOCX/ZIP is preserved for study, not an executable 1.37 setup.

## Static validation criteria

Every executable 2026 module document supplies: platform prerequisites, exact file paths/commands, target state, verification commands, failure diagnostics, and teardown. No live lab has been run as part of this documentation modernization.
