# Module 07 — Templating Tools and Package Management

> **Learning edition (Kubernetes 1.37).** The original explanations of variable substitution, template-free overlays and Helm chart packaging lead directly into the three current exercises. Historical unpinned installer commands and old tutorial deployments have been replaced by **versioned repository manifests, modern Kustomize and working Helm checks**. The original DOCX/ZIP remain for archival comparison.

## Learning path and objectives

Learn the trade-offs of **sed** substitution, declarative Kustomize overlays and parameterized Helm packages. Practice rendering before applying and verify the result against real Service endpoints; clean up between tasks. The cluster prerequisites are in the [course README](../README.md).

## Kubernetes 1.37 integrated labs


<!-- MODERN_LAB_BEGIN LAB-2026.md 0 -->
## Module 07 — Templating and Helm homework (Kubernetes 1.37)

> **NOTE (2026):** This document is the executable path for **all three** original Module 07 homework tasks. It uses supported `kubectl kustomize`, `labels`/ `patches`, the updated version-pinned NGINX Helm chart and real repository paths. Original 2021 DOCX/ZIP/old screenshots are preserved as historical course material.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN LAB-2026.md 1 -->
### Prerequisites

- Kubernetes **1.37** cluster from [Module 02 SETUP-2026.md](../02.%20Cluster%20Setup%20and%20Management/SETUP-2026.md), Calico, Ready nodes and admin `kubectl`.
- Helm client (see [main Module 07 README Helm Installation](./README.md#helm-installation)); `sed` command on Linux/macOS or in a suitable UNIX shell on Windows for Task 1.
- Internet access for the `shekeriev/k8s-oracle` training image (Tasks 1–2) and pinned `nginx:1.30.6-alpine-slim` (Task 3).
- From workstation: a Node IP reachable on the requested NodePort, **or** use `kubectl port-forward`. Run **one task at a time**; NodePorts must be free.
- The commands below assume the current directory is the **repository root**.

```bash
kubectl config current-context
kubectl version
kubectl get nodes
helm version
kubectl get svc -A
```
<!-- MODERN_LAB_END -->


<!-- PRESERVED_THEORY_BEGIN -->
## Manual Approach (using [sed](https://www.gnu.org/software/sed/manual/sed.html))

![image](https://user-images.githubusercontent.com/34960418/148054368-3da900a8-c995-4555-857a-581fc09e112a.png)


Manifest with placeholders prepared for ```sed```.

- The replicas value is parameterized
- The image and tag are parameterized
- The ```APPROACH``` environment variable is parameterized
- The NodePort (the port on which service is listening) is parameterized
<!-- PRESERVED_THEORY_END -->


<!-- MODERN_LAB_BEGIN LAB-2026.md 2 -->
### Task 1 — simple `sed` template

Source: `Homework/Solution/Problem 1/homework.yaml`, with placeholders `%replicas%` and `%nodeport%`. Unlike a valid Kubernetes resource, this is a **template**; render it before applying.

```bash
cd "07. Templating Tools and Package Management/Homework/Solution/Problem 1"
sed 's/%replicas%/3/g; s/%nodeport%/30001/g' homework.yaml > result.yaml
grep -E 'replicas:|nodePort:' result.yaml
kubectl apply -f result.yaml
kubectl -n homework rollout status deployment/homework --timeout=180s
kubectl -n homework get deploy,pods,svc
kubectl -n homework get svc homework-svc
```

**Expected:** Namespace `homework`, 3 Pods serving `shekeriev/k8s-oracle`, Service port **5000** to Pod port **5000**, NodePort **30001**. Verify `http://<reachable-node-ip>:30001`; use a different reachable port if it conflicts with another task.

```bash
kubectl delete namespace homework --ignore-not-found
rm -f result.yaml
cd ../../../../
```

**Shell note:** from `07. Templating Tools and Package Management/Homework/Solution/Problem 1`, `cd ../../../../` returns to the **repository root** (four parent levels). The next task's paths assume that root working directory.
<!-- MODERN_LAB_END -->


<!-- PRESERVED_THEORY_BEGIN -->
## [Kustomize](https://kustomize.io/)

- Native Kubernetes configuration management
- Template-free way to customize application configuration
- Simplifies the use of off-the-shelf applications
- Built into **kubectl** as **apply -k**

![image](https://user-images.githubusercontent.com/34960418/148058002-cf97fa5c-7c09-4989-a322-d1fa52c03dc2.png)
<!-- PRESERVED_THEORY_END -->


<!-- PRESERVED_THEORY_BEGIN -->
### Using Kustomize

> **NOTE (2026):** The examples below use the supported Kustomize `labels` and `patches` fields instead of deprecated `commonLabels` and `patchesStrategicMerge`. We set `includeSelectors: true` to retain the original behavior: labels are added to selectors and Pod templates as well as resource metadata. `commonAnnotations` remains supported.

![image](https://user-images.githubusercontent.com/34960418/147357972-a133c2f2-4542-4d50-be8a-d6a2f9c9f2f1.png)
<!-- PRESERVED_THEORY_END -->

### Base versus overlays — why the abstraction matters

The original lecture distinguishes a **base** (shared resources) from environment **overlays** (targeted changes). The supported Task 2 below provides the exact checked-in manifests, selector-safe labels and current patch syntax, rather than replaying the historical `commonLabels` / `patchesStrategicMerge` exercise.


<!-- MODERN_LAB_BEGIN LAB-2026.md 3 -->
### Task 2 — Kustomize production and test overlays

The executable source is `Homework/Solution/Problem 2/`. The base contains **Deployment + Service**, but **does not include a Namespace object**. This is intentional: `namePrefix: production-` / `test-` would rename a Namespace object, breaking the intended shared `homework` namespace. Create the namespace separately.

```bash
# From the repository root:
kubectl create namespace homework --dry-run=client -o yaml | kubectl apply -f -
kubectl kustomize "07. Templating Tools and Package Management/Homework/Solution/Problem 2/overlays/production"
kubectl kustomize "07. Templating Tools and Package Management/Homework/Solution/Problem 2/overlays/test"
kubectl apply -k "07. Templating Tools and Package Management/Homework/Solution/Problem 2/overlays/production"
kubectl apply -k "07. Templating Tools and Package Management/Homework/Solution/Problem 2/overlays/test"
kubectl -n homework get deployments,pods,services
kubectl -n homework get endpointslices
```

**Expected:** `production-homework` has **3 replicas**, `test-homework` has **1 replica**; both workloads run in `namespace/homework` with matching selectors, with NodePorts **32001** and **32002**. The overlays use `labels: [{pairs, includeSelectors: true}]` and `patches`, not deprecated `commonLabels` / `patchesStrategicMerge`. Open the two URLs `http://<node-ip>:32001` and `http://<node-ip>:32002`.

```bash
kubectl delete namespace homework --ignore-not-found
```
<!-- MODERN_LAB_END -->


<!-- PRESERVED_THEORY_BEGIN -->
## [Helm](https://helm.sh/)

- It is a **package manager** for Kubernetes.
- Its packages are called **charts**.
- Charts help us define, install, and upgrade complex applications.
- They are easy to create, version, share, and publish.
- Charts are **organized in repositories**.
- Repositories may be accessed either **directly** or via a **hub**.
- One such hub is the **ArtifactHUB** (https://artifacthub.io/).

[Architecture](https://helm.sh/docs/topics/architecture/) - Two parts in one executable – client and library

![image](https://user-images.githubusercontent.com/34960418/148059263-b2c0a6f3-15d0-40af-9dd3-21001aad6a31.png)

[Charts](https://helm.sh/docs/topics/charts/)

- Collection of files that describe a related set of Kubernetes resources
- A single chart might be used to deploy something simple like a single pod with nginx, redis, etc.
- Or a set of different resources. For example, a full web app stack with HTTP servers, databases, caches, and so on
- They are created as a set of files with particular names and structure and then packaged into versioned archives
- Chart is organized as a collection of files inside of a directory
- The directory name is the name of the chart without versioning information

### Chart Directory Structure

![image](https://user-images.githubusercontent.com/34960418/148059973-46ab0129-cb43-466d-aef2-e568d874d9ff.png)
<!-- PRESERVED_THEORY_END -->


### Helm Installation

Install a supported Helm 3 client using the [official Helm installation instructions](https://helm.sh/docs/intro/install/). Verify the client with `helm version` before starting the chart lab. The old unpinned installer steps have been removed from the execution path.

<!-- MODERN_LAB_BEGIN LAB-2026.md 4 -->
### Task 3 — Helm chart of NGINX with ConfigMap-hosted HTML and picture

The executable directory is `Homework/Solution/Problem 3/webchart/`. The chart has explicit image tag **nginx:1.30.6-alpine-slim**, 3 replicas by default, ConfigMap-hosted `index.html` and `logo.svg`, and Service NodePort **31000**. Parameters are `replicasCount`, `greetingMessage`, and `nodePort`.

```bash
# From repository root:
helm lint "07. Templating Tools and Package Management/Homework/Solution/Problem 3/webchart"
helm template demo "07. Templating Tools and Package Management/Homework/Solution/Problem 3/webchart"
helm upgrade --install demo "07. Templating Tools and Package Management/Homework/Solution/Problem 3/webchart"
kubectl rollout status deployment/demo-deployment --timeout=180s
kubectl get deployments,pods,services,configmaps
kubectl port-forward svc/demo-svc 8080:80
# In second terminal:
# curl -fsS http://localhost:8080/
# curl -fsS http://localhost:8080/logo.svg
```

**Expected:** 3 Ready NGINX Pods and a working web page with greeting and a local embedded SVG picture. The HTTP body shows `Hello from NGINX chart :)`; the `logo.svg` request returns SVG source. Stop port-forward with Ctrl+C.

Example of **parametrization** without changing the chart:

```bash
helm upgrade demo "07. Templating Tools and Package Management/Homework/Solution/Problem 3/webchart" \
  --set replicasCount=2 --set nodePort=31000 \
  --set-string greetingMessage='Hello from a customized Helm lab'
kubectl rollout status deployment/demo-deployment --timeout=180s
helm status demo
helm uninstall demo
```

**Expected:** 2 replicas after upgrade; updated greeting; Service still uses NodePort 31000. Do not run another lab using this NodePort simultaneously.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN LAB-2026.md 5 -->
### Static acceptance checklist

- [ ] Correct K8s context; Ready Nodes; no duplicate NodePorts
- [ ] Task 1 templates expanded (no `%replicas%` / `%nodeport%` left) before applying
- [ ] Task 2 shared Namespace created separately; 3/1 replicas; both Services have endpoints
- [ ] Task 3 passes `helm lint`, `helm template`, and the expected HTML/SVG behavior
- [ ] Check each task's desired state, then clean up before starting another one

See [Author Solution README](./Homework/Solution/Author%20Solution/README.md) for step-by-step historical and synchronized examples. The executable source files are authoritative if old screenshots differ.
<!-- MODERN_LAB_END -->

