# Module 08 — Exam Preparation

> **Integrated edition · Kubernetes 1.37 (2026).** The modern exercises are now inside the original module's README, with the original lesson retained **verbatim** after the labs. Keep historical documentation for concepts and comparisons; use the modern text for actual commands, versions and validations.

## Recommended learning path

1. Start from the [2026 course roadmap](../README.md) and check your disposable cluster's prerequisites.
2. Work through the [integrated modern lab](#kubernetes-137-integrated-labs) in this README, following expected results, failure diagnosis and cleanup.
3. Return to the [preserved original lecture](#preserved-original-lecture--historical-reference), compare approaches, and reinforce your understanding. Historical artifacts are not a substitute for the 1.37 runbook.

| Concepts and teaching value preserved | Kubernetes 1.37 integration |
|---|---|
| Historical exam blueprint and topics | Original slides/DOCX remain available and unchanged |
| Current Kubernetes 1.37 practice exam | Nine tasks, 36 points, three logical namespaces |
| Reproducibility and grading | Lab setup YAML, validation matrix, separate reference solutions |
| Different underlying 2021 topology | No claim of reconstructing the historical three-cluster exam |

## Kubernetes 1.37 integrated labs

> **Execution boundary:** the lab below is the documented modern path, not a verified live-cluster run. Keep the practice questions and their solutions separate where the original exercise requires independent work.

## Kubernetes 1.37 — practical simulation exam (2026)

> **Version:** 11 November 2026 · **Static-review status:** full task, setup, reference manifests, validation and cleanup documented; **not live-tested**.
>
> **IMPORTANT:** The original `M8-Practice-Exam-Preparation-Simulation-Exam.docx` is a **2021 historical three-cluster exam** (Kubernetes 1.21.6, Debian 10, Flannel/Weave/Antrea). The attached `(files).zip` contains only part of that old exam's setup and solutions; it cannot be honestly presented as a complete 1.37 deployment. The modern, fully described **equivalent practice exam** below instead divides **one disposable 1.37 Calico cluster** into three namespaces named **exam-mars**, **exam-jupiter**, and **exam-venus**. These are logical areas, **not three independent clusters**. The original PDF/DOCX/ZIP are retained for study, not for executing unchanged against 1.37.

### Skills tested and score

| Area | Tasks | Points |
|---|---|---:|
| Mars — application routing / troubleshooting / Kustomize | T101, T102, T103 | 12 |
| Jupiter — NetworkPolicy / RBAC / ConfigMap+Secret | T201, T202, T203 | 12 |
| Venus — recovery / CronJob / Helm | T301, T302, T303 | 12 |
| **Total** | **9 tasks** | **36** |

Solutions are deliberately separate in [lab-2026/SOLUTIONS.md](./lab-2026/SOLUTIONS.md). Attempt the tasks without reading them first. Optional extensions add HPA and NFS (from Modules 05/04/06). These are not required for the 36-point exam.

### 0. Preflight and initial provisioning

Requirements: **one new disposable Kubernetes 1.37 cluster** from [Module 02 SETUP-2026.md](../02.%20Cluster%20Setup%20and%20Management/SETUP-2026.md), with Calico 3.33 providing NetworkPolicy enforcement; `kubectl`, Helm v3, internet for pulling pinned images/Helm chart; local `curl`; enough CPU/RAM for several small Pods. Use a context with permission to create all resources in these three dedicated namespaces. Do not reuse another lab's NodePorts or namespaces. Commands below assume the **repository root**.

```bash
kubectl config current-context
kubectl version
kubectl get nodes
kubectl get tigerastatus
helm version
```

**Expected:** control plane + workers Ready; Calico healthy. There must be no pre-existing `exam-mars`, `exam-jupiter`, `exam-venus` namespaces. **Do not run the cleanup commands on any real environment.**

Install the correct F5 NGINX controller for the Mars ingress exercise; this can be omitted only if the current lab already has this exact controller with `IngressClass/nginx`:

```bash
helm upgrade --install nginx-ingress oci://ghcr.io/nginx/charts/nginx-ingress \
  --version 2.8.1 --namespace nginx-ingress --create-namespace \
  --set controller.service.type=NodePort \
  --set controller.ingressClass.name=nginx
kubectl get ingressclass nginx
kubectl get pods,svc -n nginx-ingress
```

The source setup file [lab-2026/setup.yaml](./lab-2026/setup.yaml) creates: two HTTP echo apps and a **deliberately broken readiness probe** in Mars; a test API and ServiceAccount in Jupiter; and a **deliberately missing ConfigMap dependency** in Venus. The "broken" workloads are supposed to be diagnosed as tasks.

```bash
# Create namespaces first, so their scoped resources never race them.
for n in exam-mars exam-jupiter exam-venus; do
  kubectl create namespace "$n" --dry-run=client -o yaml | kubectl apply -f -
done
kubectl apply -f "08. Exam Preparation/lab-2026/setup.yaml"
kubectl get deploy,pods,svc -n exam-mars
kubectl get deploy,pods,svc,sa -n exam-jupiter
kubectl get deploy,pods,svc -n exam-venus
```

**Expected initially:** cat, dog, jupiter-api available. `misprobe` Deployment exists but its Pod is **not Ready** due to wrong readiness path; venus-web cannot become Ready until `ConfigMap/venus-index` exists. Do not "fix" those two until their tasks.

### 1. Exam tasks — solve before viewing the key

#### Mars — 12 points

**T101 / 4 pts — Ingress fanout.** Create `Ingress/pets-ingress` in `exam-mars`, class **nginx**, host **pets.lab**, using `networking.k8s.io/v1`. Route `/cat` to `cat-svc:80` and `/dog` to `dog-svc:80` via `Prefix` matches. Save the manifest and apply it. Verify actual HTTP replies `cat-service-ok` and `dog-service-ok`. The F5 NGINX controller must already be Ready; do **not** install another Ingress controller.

**T102 / 4 pts — probe troubleshooting.** `Deployment/misprobe` is unavailable despite a working NGINX container. Diagnose its readiness failure using Pod events and fix it **without deleting the entire Deployment**. Its HTTP endpoint on port 80 should respond at `/`. Verify Deployment becomes Available.

**T103 / 4 pts — Kustomize blue/green.** Start from [lab-2026/starter/base](./lab-2026/starter/base/), containing a Deployment and a NodePort Service. Produce two overlays with names **blue-portal** / **green-portal** and Services **blue-portal-svc** / **green-portal-svc**, in `exam-mars`. Blue: **3 replicas**, nodePort **31103**; Green: **1 replica**, a **different NGINX image tag**, nodePort **32103**. Preserve label selectors/Pod labels so the respective Services get endpoints. Use modern `labels` with `includeSelectors: true` and `patches`. Render and apply **both overlays**, never the unmodified base.

#### Jupiter — 12 points

**T201 / 4 pts — Calico NetworkPolicy.** `Deployment/jupiter-api` and `Service/api-svc` already run on TCP **Service 80 → Pod 5678**. Create a policy selecting `app=jupiter-api` that allows ingress **only from same-namespace Pods labelled `access=trusted`** on **Pod TCP 5678**. Create a trusted and an untrusted test Pod and demonstrate a successful HTTP response only from the trusted one.

**T202 / 4 pts — RBAC.** `ServiceAccount/exam-reader` already exists. Give it **get/list/watch** on Pods in `exam-jupiter`, and **no write permissions**. Check `kubectl auth can-i` with impersonation for list vs delete.

**T203 / 4 pts — configuration/secrets.** Create `ConfigMap/app-settings` with key `MODE=exam`, a disposable `Secret/api-credentials` with key `PASSWORD=demo-only`, and a Pod `env-check` which consumes both as environment variables and demonstrates they were loaded (without printing the password). This credential is **dummy training text only**.

#### Venus — 12 points

**T301 / 4 pts — ConfigMap volume recovery.** `Deployment/venus-web` exists but fails to start because it references absent `ConfigMap/venus-index`. Repair it by creating the expected ConfigMap with an `index.html` page containing **Venus recovered!**. Verify Deployment Ready and HTTP response from the Service.

**T302 / 4 pts — scheduled jobs.** Create `CronJob/pulse` in `exam-venus` using `batch/v1`, running every **2 minutes**, printing `exam-venus-pulse` and UTC time. Demonstrate immediately by creating one Job from that CronJob instead of waiting 2 minutes; inspect the Job's logs. Avoid overlapping runs.

**T303 / 4 pts — Helm templating.** Reuse the self-contained Helm chart from Module 07, [`webchart`](../07.%20Templating%20Tools%20and%20Package%20Management/Homework/Solution/Problem%203/webchart/). Validate it with `helm lint` and `helm template`, then install as release **examweb** into `exam-venus`, with **2 replicas**, `NodePort 31000` and greeting **Exam Venus complete**. Confirm page text, local SVG image and generated Kubernetes resources. Cleanup only the Helm release, not the whole namespace yet.

### 2. Validation matrix

| Task | Pass evidence |
|---|---|
| T101 | Ingress class nginx; `pets.lab/cat` and `pets.lab/dog` return correct distinct text |
| T102 | `misprobe` Pod Ready and Deployment Available after probe fix |
| T103 | Both blue/green Deployments Available, replicas 3/1; Services have correct endpoints and NodePorts 31103/32103 |
| T201 | Trusted Pod reaches Jupiter API; untrusted request times out when policy active |
| T202 | ServiceAccount list Pods = **yes**; delete Pods = **no** |
| T203 | Pod `env-check` logs `configuration-ok`, not the password |
| T301 | `venus-web` reaches Available; `index.html` serves expected text |
| T302 | On-demand Job Complete and logs show `exam-venus-pulse` |
| T303 | Helm chart passes lint/template, 2 replicas available, Service NodePort 31000 and HTML+SVG served |

Use `kubectl describe`, `kubectl get endpointslices`, `kubectl logs`, `kubectl rollout status`, and `helm status` to diagnose unexpected output. A live API, image registry, NFS server or external endpoint can still fail; the documentation is **statically** reviewed, not an execution guarantee.

### 3. Optional advanced extensions (not in the 36 points)

- **HPA:** install Metrics Server **v0.9.1** and run the supported `autoscaling/v2` test from [Module 05 ADVANCED-2026.md](../05.%20Advanced%20Concepts/ADVANCED-2026.md#4-horizontal-pod-autoscaler-hpa-practical-lab).
- **NFS/StatefulSets:** run [Module 04 STORAGE-2026.md](../04.%20Storage%20and%20Persistence/STORAGE-2026.md) or [Module 06 LAB-2026.md](../06.%20Observability%20and%20Troubleshooting/LAB-2026.md). These need a separate NFS machine and should be executed in a **fresh lab** because they use NodePort 30001.

### 4. Cleanup

**Destructive on a dedicated disposable exam lab only**: removes all objects in three exam namespaces, even if you added extra objects.

```bash
kubectl delete namespace exam-mars exam-jupiter exam-venus --ignore-not-found
# Only if it was installed solely for this exam and no other workload uses it:
helm uninstall nginx-ingress -n nginx-ingress
kubectl delete namespace nginx-ingress --ignore-not-found
kubectl get namespace
```

Check that all three exam namespaces are gone. The original historical 2021 simulation and its answer material remain unchanged in the repository.

### Links

- [Solutions, with exact commands and files](./lab-2026/SOLUTIONS.md)
- [Starter setup](./lab-2026/setup.yaml)
- [2021 exam blueprint](../00.%20Resources/M0-Blueprint-Practice-Exam.docx)
- [Upstream Kubernetes concepts](https://kubernetes.io/docs/home/)

---

## Preserved original lecture — historical reference

> **2021 lecture / exam notes.** The content below is preserved byte-for-byte for educational comparison. Follow the integrated 1.37 lab above instead of reusing retired APIs, network plugins, URLs, or old examination environment assumptions.

<!-- ORIGINAL_MODULE_README_PRESERVED_START -->
# Exam Preparation — Kubernetes 1.37

## Current, self-contained lab (2026)

Follow [EXAM-2026.md](./EXAM-2026.md) for a complete practical exam with prerequisites, **nine tasks**, a complete [setup manifest](./lab-2026/setup.yaml), starter Kustomize files, an independent [solutions guide](./lab-2026/SOLUTIONS.md), pass criteria and cleanup. The test environment uses **three logical namespaces in one disposable Kubernetes 1.37 + Calico cluster** to keep the setup reproducible.

## Historical exam materials (2021)

The original `M8-Practice-Exam-Preparation-Simulation-Exam.docx` assumes **three independent Debian 10 / Kubernetes 1.21.6 clusters** named Mars, Jupiter and Venus with different older CNI controllers (Flannel, Weave Net and Antrea). The historical accompanying ZIP is **not a complete 1.37 setup** and its solutions must not be applied unchanged. Slides and the DOCX remain intact as source/history.

> **NOTE (2026):** The modern exam **replaces** the execution path while preserving the *skills and themes* of the old exam. It is intentionally not a verbatim conversion of all historical tasks. If you specifically need an exact three-cluster historical reenactment, that is a separate undertaking and should not be confused with the supported 1.37 course.
