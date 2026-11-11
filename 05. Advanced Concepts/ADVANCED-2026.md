# Module 05 — Advanced Concepts and Homework (Kubernetes 1.37)

> **NOTE (2026):** Executable lab path for autoscaling and all three original advanced homework problems (two init containers, TLS fanout Ingress, **another Ingress controller**). The original 2021 DOCX and Contour install snippet remain historical; the 2026 third-controller solution deliberately uses **Traefik**. This avoids relying on unpinned archived manifest URLs. Start on a disposable Kubernetes **1.37 + containerd + Calico 3.33** cluster from [Module 02](../02.%20Cluster%20Setup%20and%20Management/SETUP-2026.md). Run lab applications **sequentially** to avoid NodePort 30001/name conflicts.

## 0. Prerequisites

- Admin `kubectl` configured for the **lab** cluster; worker Nodes Ready, Calico running; `helm` client; image-pull and Helm repository access; openssl and curl on the workstation.
- At least one Node IP reachable from the workstation; TCP NodePorts allowed if testing from outside. Where possible use `kubectl port-forward` to avoid host firewall restrictions.
- All manifest examples below assume your working directory is the **root of the cloned Kubernetes repository**.

```bash
kubectl version
kubectl get nodes -o wide
kubectl config current-context
helm version
kubectl get ingressclass
kubectl get svc -A
```

Expected: 1.37 cluster, Ready nodes, valid Helm installation. The canonical module [README.md](./README.md) has the complete preserved historical theory on static/multi-container Pods, sidecars, scaling, scheduling, Jobs, CronJobs and Ingress.

## 1. Original Homework Problem 1 — two init containers, NGINX app container

Use the executable `Homework/Solution/Problem 1/problem-1.yaml`. The YAML creates a `Pod/pod-init` with **two sequential** Alpine init containers and an NGINX app container sharing an `emptyDir` at `/usr/share/nginx/html`. First init container records begin/end timestamps separated by 10s. Second writes a "launching" timestamp. Their output is the application index page.

```bash
kubectl apply -f "05. Advanced Concepts/Homework/Solution/Problem 1/problem-1.yaml"
kubectl wait pod/pod-init --for=condition=Ready --timeout=180s
kubectl get pod pod-init -o wide
kubectl describe pod pod-init
kubectl logs pod-init -c cont-init-0
kubectl exec pod-init -c cont-main -- cat /usr/share/nginx/html/index.html
kubectl port-forward svc/svc-init 8080:80
# In another terminal: curl http://localhost:8080/
```

**Expected:** index page contains **3 timestamped lines**, with about 10 seconds between the first two; NGINX is Ready after both init containers exit successfully; HTTP response is the generated page. Press Ctrl+C to stop port-forward.

```bash
kubectl delete -f "05. Advanced Concepts/Homework/Solution/Problem 1/problem-1.yaml" --ignore-not-found
```

## 2. Original Homework Problem 2 — HTTPS fanout with F5 NGINX Ingress

### 2.1 Install the correct NGINX Ingress controller

Follow the **current section** [Installing Ingress Controllers — Kubernetes 1.37 lab (2026)](./README.md#installing-ingress-controllers--kubernetes-137-lab-2026). It pins **F5 NGINX Ingress Controller v5.7.1, Helm chart 2.8.1**, uses class `nginx` and Service type NodePort. The NGINX-specific `nginx.org/rewrites` annotation in the homework requires this **F5 NGINX** implementation, not the similarly named community ingress-nginx or Traefik.

Verify:

```bash
kubectl get ingressclass nginx -o yaml
helm status nginx-ingress -n nginx-ingress
kubectl get pods,svc -n nginx-ingress
```

### 2.2 TLS Secret and fanout manifest

In a terminal at the **repository root**, create a fresh self-signed certificate with SAN `demo.lab` instead of using the 2021 demo secret:

```bash
TLS_DIR="$(mktemp -d)"
openssl req -x509 -nodes -days 30 -newkey rsa:2048 \
  -keyout "$TLS_DIR/tls.key" -out "$TLS_DIR/tls.crt" \
  -subj "/CN=demo.lab" -addext "subjectAltName=DNS:demo.lab"
kubectl create secret tls demo-lab-secret \
  --cert="$TLS_DIR/tls.crt" --key="$TLS_DIR/tls.key" \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f "05. Advanced Concepts/Homework/Solution/Problem 2/solution.yaml"
kubectl wait --for=condition=Ready pod/pod1 pod/pod2 pod/podd --timeout=180s
kubectl get ingress ingress-ctrl -o yaml
kubectl get pods,svc,ingress
kubectl get endpointslices
```

**Expected:** three backend Pods Ready and Ingress class `nginx` with HTTPS host `demo.lab`; the three Ingress backends reference **Service port 80**, whereas client HTTPS uses listener **443** via its **mapped NodePort**. The Ingress default backend routes `/` to `serviced`.

### 2.3 Validate the HTTPS paths

```bash
kubectl get svc -n nginx-ingress
# In the Service ports mapping, locate the NodePort assigned to 443/TCP.
# Replace BOTH values below; never use documentation example addresses unchanged.
NODE_IP=192.0.2.10           # REPLACE with your reachable cluster node IP
HTTPS_NODEPORT=30443        # REPLACE with the assigned HTTPS NodePort
curl -ksS --resolve "demo.lab:${HTTPS_NODEPORT}:${NODE_IP}" "https://demo.lab:${HTTPS_NODEPORT}/service1"
curl -ksS --resolve "demo.lab:${HTTPS_NODEPORT}:${NODE_IP}" "https://demo.lab:${HTTPS_NODEPORT}/service2"
curl -ksS --resolve "demo.lab:${HTTPS_NODEPORT}:${NODE_IP}" "https://demo.lab:${HTTPS_NODEPORT}/"
```

Expected body text from the historical example: `POD1 -> SERVICE1`, `POD2 -> SERVICE2`, and `PODd -> SERVICEd (default backend)`. `-k` skips trust validation of the self-signed lab certificate **only for this lab**, never production.

If a path fails, inspect `kubectl describe ingress ingress-ctrl`, class/annotations, NGINX controller logs, Pod readiness, `kubectl get endpointslices`, and node firewall. Ingress Controller may take a few moments to reconcile after applying the objects.

```bash
kubectl delete -f "05. Advanced Concepts/Homework/Solution/Problem 2/solution.yaml" --ignore-not-found
kubectl delete secret demo-lab-secret --ignore-not-found
rm -rf "$TLS_DIR"
# Only if this dedicated lab has no other nginx-ingress uses:
helm uninstall nginx-ingress -n nginx-ingress
kubectl delete namespace nginx-ingress
```

## 3. Original Homework Problem 3 — another controller (Traefik, not NGINX/HAProxy)

The archived author solution used Contour with a moving `quickstart` URL and manual changes by approximate file line numbers. Instead, the new executable solution uses **Traefik chart 42.3.0** (chart requires Kubernetes >= 1.30) and standard `networking.k8s.io/v1` Ingress on **a separate clean lab**.

This is a standalone demonstration with two HTTP echo Deployments, so it does **not** need NGINX-specific URL rewrite annotations. Two URLs route to two Services; backend Service ports are 80.

```bash
helm repo add traefik https://traefik.github.io/charts
helm repo update
helm upgrade --install traefik traefik/traefik \
  --version 42.3.0 --namespace traefik-lab --create-namespace \
  --set service.type=ClusterIP \
  --set ingressClass.name=traefik \
  --set ingressClass.isDefaultClass=false \
  --set providers.kubernetesIngress.enabled=true \
  --set providers.kubernetesIngress.ingressClass=traefik \
  --wait --timeout 180s

kubectl get ingressclass traefik
kubectl get svc,pods -n traefik-lab
kubectl apply -f "05. Advanced Concepts/Homework/Solution/Problem 3 - Traefik/traefik-fanout.yaml"
kubectl -n m05-alt rollout status deploy/service1 --timeout=180s
kubectl -n m05-alt rollout status deploy/service2 --timeout=180s
kubectl -n m05-alt get svc,pods,ingress
kubectl -n traefik-lab port-forward svc/traefik 8888:80
# On another terminal:
# curl -fsS http://localhost:8888/service1
# curl -fsS http://localhost:8888/service2
```

**Expected:** HTTP response **`service1 via Traefik`** at `/service1` and **`service2 via Traefik`** at `/service2`. The host-local `8888` is a port-forward to the Traefik HTTP entrypoint; no DNS or NodePort is required. Ensure local 8888 is free.

```bash
# Stop kubectl port-forward with Ctrl+C first.
kubectl delete -f "05. Advanced Concepts/Homework/Solution/Problem 3 - Traefik/traefik-fanout.yaml" --ignore-not-found
helm uninstall traefik -n traefik-lab
kubectl delete namespace traefik-lab
```

**Important:** The historical Contour-based solution is **archived for comparison**. It is not the recommended execution path for Kubernetes 1.37. Original requirement was simply "another Ingress Controller, not NGINX or HAProxy"; Traefik satisfies it. For this course, prefer standard Ingress for the task; Kubernetes Gateway API is a separate topic.

## 4. Horizontal Pod Autoscaler (HPA) practical lab

The module's [modern HPA section](./README.md#horizontal-pod-autoscaler-example) provides the full commands; the checked-in [autoscaling/v2 manifest](./labs/auto-scale-hpa-2026.yaml) includes Deployment, NodePort Service, CPU requests and HPA min1/max5. Install **Metrics Server 0.9.1** compatible with Kubernetes 1.37, verify `kubectl top`, and apply this manifest.

Do not blindly add `--kubelet-insecure-tls`: only consider the lab-only flag when kubelet serving certificate verification fails, and prefer real trust configuration for non-lab clusters.

**Expected:** CPU metrics available, HPA has non-unknown targets, workload generates CPU demand and causes scaling within bounds. HPA behavior depends on actual measured utilization.

## 5. Additional module topics

Read the existing sections in [README.md](./README.md) and practice them **sequentially**: static Pods, init/sidecar/adapter containers, taints/tolerations and node selectors, DaemonSets, Jobs, CronJobs and HPA. Their original embedded commands and DOCX/ZIP screenshots may show 2021-era images and cluster versions; use the validated K8s 1.37 baseline and inspect current API versions with `kubectl api-resources` and `kubectl explain`.

Troubleshooting order: `kubectl get` / `describe` / `get events` / `logs` / `rollout status` / `get endpointslices`. Never apply an `Ingress` alone and expect traffic to route without an active matching controller.

## Acceptance checklist

- [ ] All app Pods and Services reach Ready/available
- [ ] Problem 1 produces 3 timestamped lines with about a 10-second pause
- [ ] Problem 2 has fresh TLS Secret and responds correctly for all three HTTPS paths
- [ ] Problem 3 responds through the Traefik Ingress at two independent paths
- [ ] HPA uses **autoscaling/v2** and real Metrics Server CPU data
- [ ] NodePort assignments do not conflict and all lab-created objects are cleaned up
