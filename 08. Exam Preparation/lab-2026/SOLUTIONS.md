# Kubernetes 1.37 practical exam — reference solutions

> **Spoilers.** Read [EXAM-2026.md](../EXAM-2026.md) and attempt all nine tasks first. These commands assume the **repository root**, correct disposable cluster context and completed [setup](./setup.yaml). The solutions are statically checked and **have not been executed** in a live cluster.

## Mars

### T101 — NGINX fanout

File: [solutions/mars-ingress.yaml](./solutions/mars-ingress.yaml). Ingress host `pets.lab`, `nginx` class and Service backends `cat-svc:80`, `dog-svc:80`.

```bash
kubectl apply -f "08. Exam Preparation/lab-2026/solutions/mars-ingress.yaml"
kubectl -n exam-mars describe ingress pets-ingress
kubectl -n exam-mars get svc,endpointslices
kubectl get svc -n nginx-ingress
```

Select the F5 NGINX controller Service **exposing HTTP 80** from `kubectl get svc -n nginx-ingress`. Port-forward it in a separate terminal (the actual service name is chart-dependent):

```bash
kubectl -n nginx-ingress port-forward svc/<NGINX_CONTROLLER_SERVICE_NAME> 8080:80
```

In another terminal:

```bash
curl -fsS -H "Host: pets.lab" http://localhost:8080/cat
curl -fsS -H "Host: pets.lab" http://localhost:8080/dog
```

Expected: `cat-service-ok`, `dog-service-ok`. Stop port-forward with Ctrl+C. The backend Service port is **80**, not the external port-forward 8080.

### T102 — fix the readiness probe

```bash
kubectl -n exam-mars describe deploy misprobe
kubectl -n exam-mars describe pod -l app=misprobe
kubectl -n exam-mars patch deployment/misprobe --type=json \
  -p='[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/path","value":"/"}]'
kubectl -n exam-mars rollout status deployment/misprobe --timeout=180s
kubectl -n exam-mars get pods -l app=misprobe
```

Expected: the broken `/nonexistent` HTTP readiness path is changed to `/`, Pod becomes Ready and deployment becomes Available. The Deployment controller may replace the old unhealthy ReplicaSet.

### T103 — Kustomize blue/green overlays

Starter: [starter/base](./starter/base/). Exact solutions:
[blue](./solutions/blue/) and [green](./solutions/green/).

The new `labels` transformer uses `includeSelectors: true` so variants have matching Service/Pod labels. Both use `patches` and `namePrefix` rather than deprecated fields.

```bash
kubectl kustomize "08. Exam Preparation/lab-2026/solutions/blue"
kubectl kustomize "08. Exam Preparation/lab-2026/solutions/green"
kubectl apply -k "08. Exam Preparation/lab-2026/solutions/blue"
kubectl apply -k "08. Exam Preparation/lab-2026/solutions/green"
kubectl -n exam-mars rollout status deployment/blue-portal --timeout=180s
kubectl -n exam-mars rollout status deployment/green-portal --timeout=180s
kubectl -n exam-mars get deploy,svc,pods
kubectl -n exam-mars get endpointslices
```

Expected: `blue-portal` has **3** Pods, NodePort **31103**; `green-portal` has **1** Pod with a different NGINX image tag, NodePort **32103**. Their Service endpoint selectors match corresponding Pods. Test `http://<reachable-node-ip>:31103` and `http://<reachable-node-ip>:32103` or port-forward their Services independently.

## Jupiter

### T201 — Calico NetworkPolicy

```bash
kubectl -n exam-jupiter run trusted --image=alpine:3.22 --restart=Never --labels=access=trusted -- sleep 1d
kubectl -n exam-jupiter run untrusted --image=alpine:3.22 --restart=Never --labels=access=untrusted -- sleep 1d
kubectl -n exam-jupiter wait pod/trusted pod/untrusted --for=condition=Ready --timeout=180s
# Before policy, both should reach the Service (test if desired).
kubectl apply -f "08. Exam Preparation/lab-2026/solutions/jupiter-networkpolicy.yaml"
kubectl -n exam-jupiter get networkpolicy
# ALLOWED: print "jupiter-api-ok" via wget.
kubectl -n exam-jupiter exec trusted -- wget -qO- -T 5 http://api-svc/
# DENIED: request should time out / exit nonzero, not return the application response.
kubectl -n exam-jupiter exec untrusted -- wget -qO- -T 5 http://api-svc/
```

The rule uses **5678**, the actual Pod destination port behind `Service/api-svc` port 80. Ingress NetworkPolicy controls target Pod traffic and does not require separate egress rules for this lab. If both requests succeed, verify Calico enforcement, `kubectl -n exam-jupiter get pod --show-labels`, Service endpoints and any pre-existing policies.

### T202 — read-only ServiceAccount

```bash
kubectl apply -f "08. Exam Preparation/lab-2026/solutions/jupiter-rbac.yaml"
kubectl -n exam-jupiter get sa,role,rolebinding
kubectl auth can-i list pods --as=system:serviceaccount:exam-jupiter:exam-reader -n exam-jupiter
kubectl auth can-i delete pods --as=system:serviceaccount:exam-jupiter:exam-reader -n exam-jupiter
```

Expected: **yes** for list and **no** for delete.

### T203 — ConfigMap + Secret environment

```bash
kubectl apply -f "08. Exam Preparation/lab-2026/solutions/jupiter-env.yaml"
kubectl -n exam-jupiter wait pod/env-check --for=condition=Ready --timeout=180s
kubectl -n exam-jupiter logs env-check
kubectl -n exam-jupiter get cm,secret,pod
```

Expected log `configuration-ok`, confirming both variables without displaying the dummy secret value. The manifest contains training-only plaintext and must **not** be reused for production.

## Venus

### T301 — recover missing ConfigMap

```bash
kubectl -n exam-venus describe pod -l app=venus-web
kubectl apply -f "08. Exam Preparation/lab-2026/solutions/venus-index.yaml"
kubectl -n exam-venus rollout status deployment/venus-web --timeout=180s
kubectl -n exam-venus get deploy,svc,pods,cm
kubectl -n exam-venus port-forward svc/venus-web 8887:80
# In another terminal: curl -fsS http://localhost:8887/
```

Expected: `Venus recovered!` appears and Deployment becomes Available. Stop port-forward with Ctrl+C.

### T302 — CronJob

```bash
kubectl apply -f "08. Exam Preparation/lab-2026/solutions/venus-cronjob.yaml"
kubectl -n exam-venus get cronjobs
kubectl -n exam-venus create job pulse-now --from=cronjob/pulse
kubectl -n exam-venus wait job/pulse-now --for=condition=complete --timeout=180s
kubectl -n exam-venus logs job/pulse-now
```

Expected: `exam-venus-pulse` and a UTC timestamp. A schedule of `*/2 * * * *` is defined; no need to wait two minutes because the explicit Job demonstrates the same template.

### T303 — Helm chart from Module 07

```bash
helm lint "07. Templating Tools and Package Management/Homework/Solution/Problem 3/webchart"
helm template examweb "07. Templating Tools and Package Management/Homework/Solution/Problem 3/webchart" \
  --set replicasCount=2 --set nodePort=31000 --set-string greetingMessage='Exam Venus complete'
helm upgrade --install examweb "07. Templating Tools and Package Management/Homework/Solution/Problem 3/webchart" \
  --namespace exam-venus --set replicasCount=2 --set nodePort=31000 \
  --set-string greetingMessage='Exam Venus complete'
kubectl -n exam-venus rollout status deployment/examweb-deployment --timeout=180s
kubectl -n exam-venus get deploy,pods,svc,cm
helm status examweb -n exam-venus
kubectl -n exam-venus port-forward svc/examweb-svc 8889:80
# In a second terminal:
# curl -fsS http://localhost:8889/        → Exam Venus complete
# curl -fsS http://localhost:8889/logo.svg → inline SVG illustration
```

Expected: **2** Ready NGINX Pods, Service NodePort **31000**, rendered greeting and SVG image served by ConfigMap. Stop port-forward, then remove only this Helm release:

```bash
helm uninstall examweb -n exam-venus
```

## Optional extensions and final cleanup

Read the optional HPA and NFS advanced exercises in [EXAM-2026.md](../EXAM-2026.md#3-optional-advanced-extensions-not-in-the-36-points). Full exam cleanup:

```bash
kubectl delete namespace exam-mars exam-jupiter exam-venus --ignore-not-found
# Optional only when the exam exclusively installed this controller:
helm uninstall nginx-ingress -n nginx-ingress
kubectl delete namespace nginx-ingress --ignore-not-found
```

This simulation deliberately uses **one Kubernetes 1.37 cluster**. It covers the original exam blueprint categories but is not a byte-for-byte reconstruction of the historical 3-cluster challenge.
