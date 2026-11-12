# Module 07 — Templating Tools and Package Management

> **Integrated edition · Kubernetes 1.37 (2026).** The modern exercises are now inside the original module's README, with the original lesson retained **verbatim** after the labs. Keep historical documentation for concepts and comparisons; use the modern text for actual commands, versions and validations.

## Recommended learning path

1. Start from the [2026 course roadmap](../COURSE-2026.md) and check your disposable cluster's prerequisites.
2. Work through the [integrated modern lab](#kubernetes-137-integrated-labs) in this README, following expected results, failure diagnosis and cleanup.
3. Return to the [preserved original lecture](#preserved-original-lecture--historical-reference), compare approaches, and reinforce your understanding. Historical artifacts are not a substitute for the 1.37 runbook.

| Concepts and teaching value preserved | Kubernetes 1.37 integration |
|---|---|
| Manual sed-based substitution | Render, inspect, apply and clean up current manifests |
| Kustomize base and environment overlays | Modern patches/labels and production vs test |
| Helm charts, templates, releases | Pinned working NGINX chart, ConfigMap HTML/SVG, lint/test |

## Kubernetes 1.37 integrated labs

> **Execution boundary:** the lab below is the documented modern path, not a verified live-cluster run. Keep the practice questions and their solutions separate where the original exercise requires independent work.

## Module 07 — Templating and Helm homework (Kubernetes 1.37)

> **NOTE (2026):** This document is the executable path for **all three** original Module 07 homework tasks. It uses supported `kubectl kustomize`, `labels`/ `patches`, the updated version-pinned NGINX Helm chart and real repository paths. Original 2021 DOCX/ZIP/old screenshots are preserved as historical course material.

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

### Static acceptance checklist

- [ ] Correct K8s context; Ready Nodes; no duplicate NodePorts
- [ ] Task 1 templates expanded (no `%replicas%` / `%nodeport%` left) before applying
- [ ] Task 2 shared Namespace created separately; 3/1 replicas; both Services have endpoints
- [ ] Task 3 passes `helm lint`, `helm template`, and the expected HTML/SVG behavior
- [ ] Check each task's desired state, then clean up before starting another one

See [Author Solution README](./Homework/Solution/Author%20Solution/README.md) for step-by-step historical and synchronized examples. The executable source files are authoritative if old screenshots differ.

---

## Preserved original lecture — historical reference

> **2021 lecture / exam notes.** The content below is preserved byte-for-byte for educational comparison. Follow the integrated 1.37 lab above instead of reusing retired APIs, network plugins, URLs, or old examination environment assumptions.

<!-- ORIGINAL_MODULE_README_PRESERVED_START -->
> **Kubernetes 1.37 lab (2026):** [LAB-2026.md](./LAB-2026.md) provides the complete, self-contained runbook for the three Module 07 homework tasks (sed, Kustomize and Helm), current manifests, expected results, verification and cleanup. Older examples below are retained as original course explanations.

# Manual Approach (using [sed](https://www.gnu.org/software/sed/manual/sed.html))

![image](https://user-images.githubusercontent.com/34960418/148054368-3da900a8-c995-4555-857a-581fc09e112a.png)


Manifest with placeholders prepared for ```sed```.

- The replicas value is parameterized
- The image and tag are parameterized
- The ```APPROACH``` environment variable is parameterized
- The NodePort (the port on which service is listening) is parameterized

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: appa
spec:
  replicas: %replicas%
  selector:
    matchLabels: 
      app: appa
  template:
    metadata:
      labels:
        app: appa
    spec:
      containers:
      - name: main
        image: %image%:%tag%
        env:
        - name: APPROACH
          value: "%approach%"
        - name: FOCUSON
          value: "APPROACH"
---
apiVersion: v1
kind: Service
metadata:
  name: appa
spec:
  type: NodePort
  ports:
  - port: 80
    nodePort: %nodeport%
    protocol: TCP
  selector:
    app: appa
```

If send it as it is to the cluster, will see that it will result in error as it is not valid. But having it prepared in this way, can change or adjust it on the fly. Can execute this command to change, for example the number of replicas

```bash
sed s/%replicas%/3/ appa.yaml
```


This way, we set just one placeholder and saw the new version of the manifest. In order to set all of them, must either execute a sequence of commands (skip this)

```bash
sed s/%replicas%/3/ 2-appa.yaml | sed s@%image%@shekeriev/k8s-environ@ | sed s/%tag%/latest/ | sed s/%approach%/MANUAL/ | sed s/%nodeport%/30001/
```

Or execute an extended (this is one of the possible ways) command (use this)

```bash
sed 's/%replicas%/3/ ; s@%image%@shekeriev/k8s-environ@ ; s/%tag%/latest/ ; s/%approach%/MANUAL/ ; s/%nodeport%/30001/' appa.yaml
```

Here (in either of two versions), there two things to notice. 

First, we are replacing **the first occurrence** of a placeholder. Should we want to replace all, we must change the rules. For example, instead of this ```s/%nodeport%/30001/``` we should have this ```s/%nodeport%/30001/g```.

Second, notice how is changed the separator in one of the rules. Was done because have the same character as part of the value that is using.


We can either use the above command (either of its versions) to store the new version of the manifest (skip this for now)

```bash
sed 's/%replicas%/3/ ; s@%image%@shekeriev/k8s-environ@ ; s/%tag%/latest/ ; s/%approach%/MANUAL/ ; s/%nodeport%/30001/' appa.yaml > new-appa.yaml
```

Or just send it to the cluster (use this approach)

```bash
sed 's/%replicas%/3/ ; s@%image%@shekeriev/k8s-environ@ ; s/%tag%/latest/ ; s/%approach%/MANUAL/ ; s/%nodeport%/30001/' appa.yaml | kubectl apply -f -
```

Open a browser tab and navigate to the following address ```http://<control-plane-ip>:30001```. It is working. 

Now, let’s change the values of the placeholders with the following command.

```bash
sed 's/%replicas%/3/ ; s@%image%@shekeriev/k8s-environ@ ; s/%tag%/green/ ; s/%approach%/MANUAL/ ; s/%nodeport%/30001/' appa.yaml | kubectl apply -f -
```

Return to the browser tab and refresh. It is still working but looking a little bit different. So, this appears to be a valid approach of templating. There is one drawback though, we must submit values for all placeholders before we can use the manifest even if we want to change just one. 

Clean Up 

```bash
kubectl delete deployment appa
kubectl delete service appa
```


# [Kustomize](https://kustomize.io/)

- Native Kubernetes configuration management
- Template-free way to customize application configuration
- Simplifies the use of off-the-shelf applications
- Built into **kubectl** as **apply -k**

![image](https://user-images.githubusercontent.com/34960418/148058002-cf97fa5c-7c09-4989-a322-d1fa52c03dc2.png)



## Installing Kustomize

Under any **Linux** distribution, we can download it (the latest version) with

```bash
curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
```

For other versions or operating systems, should check [here](https://github.com/kubernetes-sigs/kustomize/releases).


Once downloaded, we must make it executable and move it to a folder that is part of our executable path. We can check if the process went as expected by executing.

```bash
kustomize version
```

## Using Kustomize

> **NOTE (2026):** The examples below use the supported Kustomize `labels` and `patches` fields instead of deprecated `commonLabels` and `patchesStrategicMerge`. We set `includeSelectors: true` to retain the original behavior: labels are added to selectors and Pod templates as well as resource metadata. `commonAnnotations` remains supported.

![image](https://user-images.githubusercontent.com/34960418/147357972-a133c2f2-4542-4d50-be8a-d6a2f9c9f2f1.png)


### Base Variant Kustomization

Kustomization contains the base structure of our customizable application. Let’s create the base customization file (**base/kustomization.yaml**).

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: arbitrary

# Example configuration for the webserver
# at https://github.com/monopole/hello
labels:
- pairs:
    app: hello
  includeSelectors: true

resources:
- deployment.yaml
- service.yaml
- configMap.yaml
```

Base(original) Resources

Config Map (configMap.yaml)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: the-map
data:
  altGreeting: "Good Morning!"
  enableRisky: "false"
```

Deployment (deployment.yaml)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: the-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      deployment: hello
  template:
    metadata:
      labels:
        deployment: hello
    spec:
      containers:
      - name: the-container
        image: monopole/hello:1
        command: ["/hello",
                  "--port=8080",
                  "--enableRiskyFeature=$(ENABLE_RISKY)"]
        ports:
        - containerPort: 8080
        env:
        - name: ALT_GREETING
          valueFrom:
            configMapKeyRef:
              name: the-map
              key: altGreeting
        - name: ENABLE_RISKY
          valueFrom:
            configMapKeyRef:
              name: the-map
              key: enableRisky
```

Service (service.yaml)

```yaml
kind: Service
apiVersion: v1
metadata:
  name: the-service
spec:
  selector:
    deployment: hello
  type: LoadBalancer
  ports:
  - protocol: TCP
    port: 8666
    targetPort: 8080
```

```$BASE``` must point to kustomization location

This will display base configuration in yaml on console

```bash
kustomize build $BASE
```

To send configuration to cluster

```bash
kustomize build $BASE | kubectl apply -f -
```

To delete it from cluster

```bash
kustomize build $BASE | kubectl delete -f -
```

### Staging overlay

Kustomization

```yaml
namePrefix: staging-
labels:
- pairs:
    variant: staging
    org: acmeCorporation
  includeSelectors: true
commonAnnotations:
  note: Hello, I am staging!
# Location of base variant
resources:
- ../../base
# Patch files
patches:
- path: map.yaml
```

ConfigMap patch (map.yaml)

```yaml
apiVersion: v1
# Kind and metadata describe patched resources.
kind: ConfigMap
metadata:
  name: the-map
data:
  altGreeting: "Have a pineapple!"
  enableRisky: "true"
```

Build staging variant

```bash
kustomize build $OVERLAYS/staging
```

Apply staging variant

```bash
kustomize build $OVERLAYS/staging | kubectl apply -f -
```

or

```bash
kubectl apply -k $OVERLAYS/staging
```

Delete staging variant

```bash
kustomize build $OVERLAYS/staging | kubectl delete -f -
```

or

```bash
kubectl delete -k $OVERLAYS/staging
```

### Production overlay

Kustomization

```yaml
namePrefix: production-
labels:
- pairs:
    variant: production
    org: acmeCorporation
  includeSelectors: true
commonAnnotations:
  note: Hello, I am production!
resources:
- ../../base
patches:
- path: deployment.yaml
```

Deployment (deployment.yaml)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: the-deployment
spec:
  replicas: 5
```

Build production variant

```bash
kustomize build $OVERLAYS/production
```

Apply production variant

```bash
kubectl apply -k $OVERLAYS/production
```

Delete production variant

```bash
kubectl delete -k $OVERLAYS/production
```

# [Helm](https://helm.sh/)

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

## Chart Directory Structure

![image](https://user-images.githubusercontent.com/34960418/148059973-46ab0129-cb43-466d-aef2-e568d874d9ff.png)

## Helm Installation

There are multiple ways to install Helm and perhaps the easiest one is by downloading the binary file. For any **64-bit** **Linux** distribution this can be done in the following way.

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

Latest version for other OSes can be downloaded from [here](https://github.com/helm/helm/releases/latest).
Other options and further instructions can be found [here](https://v3.helm.sh/docs/intro/install/).

Once, we have it installed, we can test if it is working by executing

```bash
helm version
```

## Register Repository

Before can start working with charts, must register one or more repositories.

The easiest way to find some, is to use the [ArtifactHub](https://artifacthub.io/).

Enter **nginx** in the search box and press Enter. A list of **nginx** related charts will appear. The first one should be a one provided by **Bitnami**. Click on it (or visit this URL: https://artifacthub.io/packages/helm/bitnami/nginx). There, in the beginning, are the instructions on how to add the repository.

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
```

Now, can list all locally registered repositories (it should be just this one)

```bash
helm repo list
```

To see where the information about the repository has been stored use

```bash
helm env
```

Let’s check what is behind the **HELM_REPOSITORY_CACHE** and **HELM_REPOSITORY_CONFIG** variables

The first one (**HELM_REPOSITORY_CACHE**) points to a folder, where information (the packages they provide) about the registered repositories will be stored including the charts that we use

The second one (**HELM_REPOSITORY_CONFIG**) points to a file which contains information about the registered repositories.


## Install Chart From Repository


Now, let’s install the chart that we wanted

```bash
helm install my-nginx-1 bitnami/nginx
```

We can notice two sets of information. The first one, right after our command, is a short information on what we deployed. The second one, contains detailed instructions on how to interact with what we deployed.


Let’s see what we have so far. Our only chart (in fact a **release**, as it is deployed in the cluster) is shown

```bash
helm list
```

Get detailed information about the release with. Have seen this information already

```bash
helm status my-nginx-1
```

Let’s use the **kubectl** to check what we have

```bash
kubectl get pods,svc
```

One pod and a service which appears to be of type **LoadBalancer** by default. Is this all? We can check with

```bash
helm get manifest my-nginx-1
```

There is one more object – a **ConfigMap**. It is used to store some additional configuration for nginx. Let’s try this command. Way more than we saw earlier. Which of the options (**all**, **hooks**, **manifest**, **notes** or **values**) to use, depends on what we are looking for.

```bash
helm get all my-nginx-1
```

Let’s try to access the default web page of the **nginx** instance. Ask for the service first.

```bash
kubectl get service my-nginx-1
```

Open a browser tab and navigate to ```http://<control-plane-ip:port> ```. Okay, it is the default page.


## Configure Chart From Repository

Go to the chart’s [page](https://artifacthub.io/packages/helm/bitnami/nginx). Explore the **Parameters** section. Go to the **custom NGINX application parameters** sub-section. And more specially in the **staticSiteConfigmap**. We can use it to pass a custom index page to the nginx chart. Create a second nginx release but this time with a custom index page.

First, create the configuration map with

```bash
kubectl create configmap my-nginx-2-index --from-literal=index.html='<h1>Hello from NGINX chart :)</h1>'
```

Check that it is there, and the content is as expected

```bash
kubectl get cm
kubectl get cm my-nginx-2-index -o yaml
```

Sure, everything is just fine. Now, install the chart but this time execute this

```bash
helm install my-nginx-2 bitnami/nginx --set staticSiteConfigmap=my-nginx-2-index --dry-run
```

This will do as stated – a dry run and show to us what will be the outcome. It seems that everything is fine, so let’s re-execute the command but without the **--dry-run** option.

```bash
helm install my-nginx-2 bitnami/nginx --set staticSiteConfigmap=my-nginx-2-index
```

Check what we have by now with

```bash
helm list
kubectl get pods,svc
```

Copy the service port and open a browser tab and navigate to ```http://<control-plane-ip:port>```. Our custom index page is there.

## Clean Up Chart

Remove the releases by executing

```bash
helm uninstall my-nginx-1 my-nginx-2
```

We can then check with

```bash
kubectl get pods,svc,cm
```

Most of the resources are gone, but configuration map is not. Because it was created separately and not as part of the chart. Remove it

```bash
kubectl delete cm my-nginx-2-index
```

## Create Chart from Manifest

> **NOTE (2026):** The following generic `appchart` walkthrough is retained from the course. Its third-party `shekeriev/k8s-environ:latest` image is **not version-pinned**; before deploying in a long-lived environment, choose and verify an immutable image tag or digest. The separate [homework NGINX chart](./Homework/Solution/Problem%203/webchart/) now defaults to an explicitly versioned image.


Original manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: appa
spec:
  replicas: 1
  selector:
    matchLabels: 
      app: appa
  template:
    metadata:
      labels:
        app: appa
    spec:
      containers:
      - name: main
        image: shekeriev/k8s-environ:latest
        env:
        - name: APPROACH
          value: "STATIC"
        - name: FOCUSON
          value: "APPROACH"
---
apiVersion: v1
kind: Service
metadata:
  name: appa
spec:
  type: NodePort
  ports:
  - port: 80
    nodePort: 30001
    protocol: TCP
  selector:
    app: appa
```

### Create helm chart

Chart directory structure

![image](https://user-images.githubusercontent.com/34960418/147486012-5b3d7e10-9ab5-489c-b687-df609f99c73e.png)


Chart.yaml

```yaml
apiVersion: v2
name: appchart
description: A simple Helm chart for Kubernetes based on an existing application

# Chart type. A chart can be either an 'application' or a 'library' chart
type: application

# Version of the chart
version: 0.1.0

# Version of the application. In our case this can be a custom version as it is our application
appVersion: "1.0.0"
```

deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-deployment
spec:
  replicas: {{ .Values.replicasCount }}
  selector:
    matchLabels:
      app: {{ .Release.Name }}
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}
    spec:
      containers:
      - name: main
        image: shekeriev/k8s-environ:latest
        env:
        - name: APPROACH
          value: {{ .Values.approachVar | quote }}
        - name: FOCUSON
          value: {{ .Values.focusOnVar | quote }}
```

service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}-service
spec:
  type: NodePort
  ports:
  - port: 80
    nodePort: {{ .Values.nodePort }}
    protocol: TCP
  selector:
    app: {{ .Release.Name }}
```

values.yaml

```yaml
replicasCount: 1
approachVar: "Helm Charts! :)"
focusOnVar: "APPROACH"
nodePort: 30001
```

Let’s test our newly created chart

```bash
helm show all ./appchart
helm lint ./appchart
helm template demo ./appchart
```

Install chart from the directory containing `appchart/`. Use a lowercase release name and an explicit `./` for the local chart path:

```bash
helm install demo ./appchart
```

Install chart with custom parameters.

```bash
helm install demo-custom ./appchart --set nodePort=30002 --set replicasCount=3
```
