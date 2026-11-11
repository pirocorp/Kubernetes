# Exam Preparation — Kubernetes 1.37

## Current, self-contained lab (2026)

Follow [EXAM-2026.md](./EXAM-2026.md) for a complete practical exam with prerequisites, **nine tasks**, a complete [setup manifest](./lab-2026/setup.yaml), starter Kustomize files, an independent [solutions guide](./lab-2026/SOLUTIONS.md), pass criteria and cleanup. The test environment uses **three logical namespaces in one disposable Kubernetes 1.37 + Calico cluster** to keep the setup reproducible.

## Historical exam materials (2021)

The original `M8-Practice-Exam-Preparation-Simulation-Exam.docx` assumes **three independent Debian 10 / Kubernetes 1.21.6 clusters** named Mars, Jupiter and Venus with different older CNI controllers (Flannel, Weave Net and Antrea). The historical accompanying ZIP is **not a complete 1.37 setup** and its solutions must not be applied unchanged. Slides and the DOCX remain intact as source/history.

> **NOTE (2026):** The modern exam **replaces** the execution path while preserving the *skills and themes* of the old exam. It is intentionally not a verbatim conversion of all historical tasks. If you specifically need an exact three-cluster historical reenactment, that is a separate undertaking and should not be confused with the supported 1.37 course.
