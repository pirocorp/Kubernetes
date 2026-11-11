# Module 03 — Security and NetworkPolicy homework (Kubernetes 1.37)

> **NOTE (2026):** Self-contained execution path for the seven original homework tasks. Use the **Calico 3.33 / VXLAN / BGP disabled** cluster prepared via [SETUP-2026.md](../02.%20Cluster%20Setup%20and%20Management/SETUP-2026.md); **do not** install an additional CNI. Original 2021 DOCX/author-solution certificates and old API addresses are **not reusable**.

## Before you begin

- One working **disposable** Kubernetes **1.37** lab from Module 02, with Calico NetworkPolicy enforcement enabled and DNS/HTTPS package/image pulls working.
- SSH/admin access to kubeadm **cp1** (not a managed cloud cluster): this exercise signs temporary client credentials with `/etc/kubernetes/pki/ca.key`. **Never expose or commit that CA private key**. Avoid on production clusters; use CSR approval or your organization's normal identity provider instead.
- All commands in this guide run on cp1 in an **admin root shell**, with a fresh checkout of `pirocorp/Kubernetes`. Certificate/key files remain local under `/root/m03-lab`, mode 600.
- Two Deployments will create **six Pods**; plus up to three test Pods fit the provided **10 Pod** quota. NodePort **30001** must be available for `Service/consumer`.

```bash
sudo -i
export KUBECONFIG=/etc/kubernetes/admin.conf
kubectl version
kubectl get nodes
kubectl get tigerastatus
kubectl config current-context
git clone https://github.com/pirocorp/Kubernetes.git /root/Kubernetes
cd /root/Kubernetes
```

**Expected:** 1.37 cluster Ready, Calico status healthy, correct admin context. If cloned previously, update it with `git -C /root/Kubernetes pull --ff-only` on the main branch.

## Task 1 — X.509 users Ivan and Mariana in `gurus`

Kubernetes does **not** have a built-in User API object: users here are authenticated by **client certificates** where `CN` gives username and `O` gives group. Group names are case-sensitive: **`gurus`** ≠ `Gurus`.

```bash
mkdir -p /root/m03-lab
chmod 700 /root/m03-lab
kubectl create namespace projectx

API_SERVER="$(kubectl config view --raw -o jsonpath='{.clusters[0].cluster.server}')"
test -n "$API_SERVER" || { echo "Missing API server endpoint"; exit 1; }

for u in ivan mariana; do
  openssl genrsa -out "/root/m03-lab/$u.key" 2048
  openssl req -new -key "/root/m03-lab/$u.key" -out "/root/m03-lab/$u.csr" \
    -subj "/CN=$u/O=gurus"
  openssl x509 -req -in "/root/m03-lab/$u.csr" \
    -CA /etc/kubernetes/pki/ca.crt -CAkey /etc/kubernetes/pki/ca.key \
    -CAcreateserial -out "/root/m03-lab/$u.crt" -days 30 -sha256

  F="/root/m03-lab/$u.kubeconfig"
  kubectl config --kubeconfig="$F" set-cluster k8s-lab \
    --server="$API_SERVER" --certificate-authority=/etc/kubernetes/pki/ca.crt --embed-certs=true
  kubectl config --kubeconfig="$F" set-credentials "$u" \
    --client-certificate="/root/m03-lab/$u.crt" --client-key="/root/m03-lab/$u.key" --embed-certs=true
  kubectl config --kubeconfig="$F" set-context "$u" --cluster=k8s-lab --user="$u" --namespace=projectx
  kubectl config --kubeconfig="$F" use-context "$u"
  chmod 600 "$F" "/root/m03-lab/$u.key"
done

kubectl --kubeconfig=/root/m03-lab/ivan.kubeconfig auth whoami
kubectl --kubeconfig=/root/m03-lab/mariana.kubeconfig auth whoami
```

**Expected:** `ivan` and `mariana` with group `gurus`. Authentication works, but authorization should initially **deny** non-granted projectx actions.

## Tasks 2–4 — Namespace, LimitRange, ResourceQuota

The checked-in files are real working manifests; unlike the author README's illustrative names (`limits.yaml`, `quotas.yaml`), these are the actual paths:

```bash
kubectl apply -f "03. Security and Policies/Exercise/Solution/Problem 3/limit-range.yml"
kubectl apply -f "03. Security and Policies/Exercise/Solution/Problem 4/resource-quota.yaml"
kubectl get limitrange,resourcequota -n projectx
kubectl describe limitrange -n projectx
kubectl describe resourcequota -n projectx
```

**Expected:** LimitRange supplies CPU/memory defaults/min/max; quota limits Requests/Limits, Pods, Services, Deployments and ReplicaSets. Note `count/replicasets.apps: 2`: do not trigger unnecessary Deployment rollouts during this constrained lab, since a rolling update may temporarily create another ReplicaSet and hit the quota. Tune the quota for additional troubleshooting Pods if needed.

## Task 5 — devguru Role and RBAC group binding

`Problem 5/devguru-role.yaml` contains the Role and RoleBinding for **`gurus`** (corrected in 2026 from incorrect `Gurus`). Permissions cover Pods, Services, Deployments and ReplicaSets in namespace `projectx`, **not** NetworkPolicies.

```bash
kubectl apply -f "03. Security and Policies/Exercise/Solution/Problem 5/devguru-role.yaml"
kubectl get role,rolebinding -n projectx
kubectl --kubeconfig=/root/m03-lab/ivan.kubeconfig auth can-i create deployments -n projectx
kubectl --kubeconfig=/root/m03-lab/mariana.kubeconfig auth can-i create pods -n projectx
kubectl --kubeconfig=/root/m03-lab/ivan.kubeconfig auth can-i create networkpolicies -n projectx
```

**Expected:** first two `yes`, NetworkPolicies `no` (the last is by design).

## Task 6 — deploy the producer/consumer application as Ivan

All four manifests exist on disk. Their namespace is `projectx`; they use the historical third-party teaching images `shekeriev/k8s-producer:latest` / `shekeriev/k8s-consumer:latest`. Their future image availability is an external dependency; inspect `kubectl describe pod` if an image cannot be pulled.

```bash
kubectl --kubeconfig=/root/m03-lab/ivan.kubeconfig apply -f "03. Security and Policies/Exercise/Solution/Problem 6/producer-deployment.yml"
kubectl --kubeconfig=/root/m03-lab/ivan.kubeconfig apply -f "03. Security and Policies/Exercise/Solution/Problem 6/producer-svc.yml"
kubectl --kubeconfig=/root/m03-lab/ivan.kubeconfig apply -f "03. Security and Policies/Exercise/Solution/Problem 6/consumer-deployment.yml"
kubectl --kubeconfig=/root/m03-lab/ivan.kubeconfig apply -f "03. Security and Policies/Exercise/Solution/Problem 6/consumer-svc.yml"

kubectl -n projectx rollout status deployment/producer-deploy --timeout=240s
kubectl -n projectx rollout status deployment/consumer-deploy --timeout=240s
kubectl -n projectx get deployments,pods,services
kubectl -n projectx get endpointslices
```

**Expected:** producer and consumer each have three Ready Pods, matching Service selectors; consumer exposed on NodePort **30001**, producer only ClusterIP.

Test network connectivity from a client Pod (label it explicitly; do not rely on `kubectl run` default labels):

```bash
kubectl -n projectx run client --image=alpine:3.22 --restart=Never --labels=role=client -- sleep 1d
kubectl -n projectx wait pod/client --for=condition=Ready --timeout=180s
kubectl -n projectx exec client -- sh -c "apk add --no-cache curl >/dev/null && curl --max-time 5 -sS http://consumer:5000/"
kubectl -n projectx exec client -- sh -c "curl --max-time 5 -sS http://producer:5000/"
```

**Expected before policies:** client can access both Services, assuming both apps are functioning.

## Task 7 — Calico NetworkPolicy producer ← consumer ← client

Two actual NetworkPolicy files in `Problem 7` cover both requested rules:
1. `producer-consumer-comunication.yaml` permits TCP **5000** to Pods `role=producer` **only** from Pods `role=consumer`.
2. `client-consumer-policy.yaml` permits TCP **5000** to Pods `role=consumer` **only** from Pods `role=client`.

Policy creation needs admin privileges because `devguru` deliberately excludes NetworkPolicy.

```bash
kubectl apply -f "03. Security and Policies/Exercise/Solution/Problem 7/producer-consumer-comunication.yaml"
kubectl apply -f "03. Security and Policies/Exercise/Solution/Problem 7/client-consumer-policy.yaml"
kubectl get networkpolicies -n projectx
kubectl describe networkpolicy -n projectx

# Client → consumer: ALLOWED
kubectl -n projectx exec client -- curl --max-time 5 -sS http://consumer:5000/
# Client → producer: DENIED (expect a timeout/non-zero exit)
kubectl -n projectx exec client -- curl --connect-timeout 3 --max-time 5 http://producer:5000/
```

Test the consumer → producer path with a separate **test-only** Pod that has `role=consumer` but **not** the `app=fun-facts` label (so it is not selected as an application Service endpoint):

```bash
kubectl -n projectx run consumer-debug --image=alpine:3.22 --restart=Never --labels=role=consumer -- sleep 1d
kubectl -n projectx wait pod/consumer-debug --for=condition=Ready --timeout=180s
kubectl -n projectx exec consumer-debug -- sh -c "apk add --no-cache curl >/dev/null && curl --max-time 5 -sS http://producer:5000/"
```

**Expected:** consumer-debug → producer succeeds. Another Pod without `role=client` cannot access consumer; a Pod without `role=consumer` cannot access producer. Kubernetes NetworkPolicies work additively and enforce **ingress on selected target Pods**; default egress remains allowed. The test client is not intended to reach producer directly.

If unexpected results occur, use `kubectl get pods -n projectx --show-labels`, `kubectl get endpointslices -n projectx`, `kubectl get tigerastatus`, `kubectl describe networkpolicy`. Verify the original app itself works **before** blaming NetworkPolicy.

## Cleanup

This deletes the dedicated lab namespace, which removes its Pods, NetworkPolicies, Services, quota, roles and other namespaced resources:

```bash
kubectl delete namespace projectx
rm -rf /root/m03-lab
```

The local temporary X.509 certificates are no longer used; they expire after 30 days. Their CA signing step was for a throwaway kubeadm cluster only. Do not copy the historical bundled private keys from the original course.

## Static acceptance checklist

- [ ] Both user kubeconfigs are created using **your** CA/server, and show membership in lower-case group `gurus`
- [ ] Quota/LimitRange objects exist in projectx
- [ ] devguru allows deployments/pods/services/replicasets, but not NetworkPolicies
- [ ] Both producer and consumer roll out and have healthy Service endpoints
- [ ] Client reaches consumer and **not** producer after policies
- [ ] Consumer-labelled debug Pod reaches producer
- [ ] Namespace deletion cleans up the lab
