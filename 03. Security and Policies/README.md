# Module 03 — Security and Policies

> **Learning edition (Kubernetes 1.37).** The original security concepts are taught next to their current X.509/RBAC, quota and NetworkPolicy exercises. Legacy user setup and multiple 2021 CNI-installation walkthroughs are **replaced**, not duplicated. The modern lab uses the **already installed Calico 3.33**, never Antrea or Weave on the same cluster.

## Learning path and objectives

Learn how API credentials, workload permissions, namespace resource controls and network isolation interact. Verify every allow/deny decision rather than relying on YAML alone. Use a disposable cluster from the [course README](../README.md).

## Kubernetes 1.37 integrated labs


<!-- MODERN_LAB_BEGIN SECURITY-2026.md 0 -->
## Module 03 — Security and NetworkPolicy homework (Kubernetes 1.37)

> **NOTE (2026):** Self-contained execution path for the seven original homework tasks. Use the **Calico 3.33 / VXLAN / BGP disabled** cluster prepared via [SETUP-2026.md](../02.%20Cluster%20Setup%20and%20Management/SETUP-2026.md); **do not** install an additional CNI. Original 2021 DOCX/author-solution certificates and old API addresses are **not reusable**.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SECURITY-2026.md 1 -->
### Before you begin

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
<!-- MODERN_LAB_END -->


<!-- PRESERVED_THEORY_BEGIN -->
## Default Cluster User

Log on to the control plane node. Check the cluster configuration file.

```bash
cat ~/.kube/config
```

We can see that there are several notable sections – clusters, contexts, current-context, and users. Clusters section contains currently registered clusters with their certificate authority data, control plane and name. Contexts section contains list of currently registered contexts that combine clusters with users. Current context specifies against which context our commands will be fired by default and without the need to explicitly specifying it. Users section contains the list of registered users with their name, certificate and key. Should we want to control more than one cluster or interact as different users, then we must alter this file or use another copy.
<!-- PRESERVED_THEORY_END -->


<!-- PRESERVED_THEORY_BEGIN -->
## Additional Cluster Users

Utilizing the option for using X.509 client certificates for cluster authentication.

Create the **pirocorp** OS user
<!-- PRESERVED_THEORY_END -->


<!-- MODERN_LAB_BEGIN SECURITY-2026.md 2 -->
### Task 1 — X.509 users Ivan and Mariana in `gurus`

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
<!-- MODERN_LAB_END -->


<!-- PRESERVED_THEORY_BEGIN -->
## Requests and Limits

When you specify a **Pod**, you can optionally specify how much of each resource a **container** needs. The most common resources to specify are CPU and memory (RAM); there are others.

When you specify the resource **request** for containers in a Pod, the kube-scheduler uses this information to decide which node to place the Pod on. When you specify a resource **limit** for a container, the kubelet enforces those limits so that the running container is not allowed to use more of that resource than the limit you set. The kubelet also **reserves** at least the request amount of that system resource specifically for that container to use.

If the node where a Pod is running has enough of a resource available, it's possible (and allowed) for a container to use more resource than its **request** for that resource specifies. However, a container is not allowed to use more than its resource **limit**.

*Note: If a container specifies its own memory limit, but does not specify a memory request, Kubernetes automatically assigns a memory request that matches the limit. Similarly, if a container specifies its own CPU limit, but does not specify a CPU request, Kubernetes automatically assigns a CPU request that matches the limit.*

### Check the available resources on the nodes

Focus on the sections **Capacity**, **Allocatable**, **Non-terminated Pods**, and **Allocated resources**

![image](https://user-images.githubusercontent.com/34960418/147819663-cff90f05-477c-40ea-86eb-8ae5d03e5812.png)

```bash
kubectl describe nodes
```

### Pod with Requests and Limits

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-3a
  namespace: reslim
spec:
  containers:
  - image: busybox
    command: ["dd", "if=/dev/zero", "of=/dev/null", "bs=64M"]
    name: main
    # Manage resource on container level
    resources:
      # Resources reserved for container in order for container to run. If there are no such free (unreserved) resources the container won't start.
      requests:
        cpu: 250m
        memory: 16Mi
      # limits the container how many resources it can consume. If pod overconsume resources (ex. Memory leak in app) kubernetes will kill it and start a new instance.
      limits:
        cpu: 500m
        memory: 128Mi
```

## Limit Ranges

- Enforce minimum and maximum compute resources usage per Pod or Container in a namespace.
- Enforce minimum and maximum storage request per PersistentVolumeClaim in a namespace.
- Enforce a ratio between request and limit for a resource in a namespace.
- Set default request/limit for compute resources in a namespace and automatically inject them to Containers at runtime.
- The LimitRanger admission controller enforces defaults and limits for all Pods and Containers that do not set compute resource requirements and tracks usage to ensure it does not exceed resource minimum, maximum and ratio defined in any LimitRange present in the namespace.
- LimitRange validations occurs only at Pod Admission stage, not on Running Pods.

LimitRangeis for managing constraints at a pod and container level within the project. LimitRanges can specify and requests (reservations).

- defaultRequest — is **how much CPU/Memory will be reserved** to Container, if it doesn't specify it's own value.
- default — is **default limit** for amount of CPU/Memory for Container, if it doesn't specify it's own value
- max — is maximum limit for amount of CPU/Memory that Container/Pod can ask for. I.e. it **can't set it's own limit more than that**
- min — is minimum limit amount of CPU/Memory that Container/Pod can ask for. I.e. it **can't set it's own limit less than that**

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: limits
  namespace: reslim
spec:
  limits:
  # limits on pod level
  - type: Pod
    max:
      cpu: 1
      memory: 1Gi
    min:
      cpu: 100m
      memory: 16Mi
  # limist on container level
  - type: Container
    defaultRequest:
      cpu: 100m
      memory: 16Mi
    default:
      cpu: 200m
      memory: 32Mi
    max:
      cpu: 1
      memory: 1Gi
    min:
      cpu: 100m
      memory: 16Mi
```

## Resource Quotas

Resource quotas are a tool for administrators to address the need of sharing cluster resources between teams of users. They are defined by the **ResourceQuota** object. Provide constraints that limit **aggregate resource consumption per namespace**. Limit the **quantity of objects** that can be created in a namespace by type. Limit the **total amount of compute resources** that may be consumed by resources.

ResourceQuota is for limiting the total resource consumption of a namespace.

An individual Pod or Container that requests resources outside of these LimitRange constraints will be rejected, whereas a ResourceQuota only applies to all of the namespace/project's objects in aggregate.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: quota
  namespace: reslim
spec:
  hard:
    pods: 3
    requests.cpu: 1
    requests.memory: 1Gi
    limits.cpu: 2
    limits.memory: 2Gi
```
<!-- PRESERVED_THEORY_END -->


<!-- MODERN_LAB_BEGIN SECURITY-2026.md 3 -->
### Tasks 2–4 — Namespace, LimitRange, ResourceQuota

The checked-in files are real working manifests; unlike the author README's illustrative names (`limits.yaml`, `quotas.yaml`), these are the actual paths:

```bash
kubectl apply -f "03. Security and Policies/Exercise/Solution/Problem 3/limit-range.yml"
kubectl apply -f "03. Security and Policies/Exercise/Solution/Problem 4/resource-quota.yaml"
kubectl get limitrange,resourcequota -n projectx
kubectl describe limitrange -n projectx
kubectl describe resourcequota -n projectx
```

**Expected:** LimitRange supplies CPU/memory defaults/min/max; quota limits Requests/Limits, Pods, Services, Deployments and ReplicaSets. Note `count/replicasets.apps: 2`: do not trigger unnecessary Deployment rollouts during this constrained lab, since a rolling update may temporarily create another ReplicaSet and hit the quota. Tune the quota for additional troubleshooting Pods if needed.
<!-- MODERN_LAB_END -->

## Authorization, Roles, RoleBindings and ServiceAccounts

A **Role** specifies allowed verbs on API resources; a **RoleBinding** associates a Role with user, group or ServiceAccount identities in a namespace. Authorization does not grant a certificate identity by itself: authentication and authorization are distinct. Always verify the effective identity using `kubectl auth can-i` and namespace-specific requests.


<!-- PRESERVED_THEORY_BEGIN -->
## Permission Check

Check for current user or ```as``` other user.

```bash
kubectl auth can-i [command] [type] [flags]
kubectl auth can-i create pods
kubectl auth can-i create pods -n demo-prod
kubectl auth can-i create pods -n demo-prod --as pirocorp
```

Furthermore, instead of asking for individual actions, we can ask for everything one can do in a namespace

```bash
kubectl auth can-i --list --namespace demo-dev --as pirocorp
```
<!-- PRESERVED_THEORY_END -->


<!-- PRESERVED_THEORY_BEGIN -->
## Extend Service Account Permitions

The **default** service account doesn’t have any permissions granted by default.

![image](https://user-images.githubusercontent.com/34960418/147775473-ff572e21-4805-48a6-aa44-7156db592829.png)

Create Service Account
<!-- PRESERVED_THEORY_END -->


<!-- MODERN_LAB_BEGIN SECURITY-2026.md 4 -->
### Task 5 — devguru Role and RBAC group binding

`Problem 5/devguru-role.yaml` contains the Role and RoleBinding for **`gurus`** (corrected in 2026 from incorrect `Gurus`). Permissions cover Pods, Services, Deployments and ReplicaSets in namespace `projectx`, **not** NetworkPolicies.

```bash
kubectl apply -f "03. Security and Policies/Exercise/Solution/Problem 5/devguru-role.yaml"
kubectl get role,rolebinding -n projectx
kubectl --kubeconfig=/root/m03-lab/ivan.kubeconfig auth can-i create deployments -n projectx
kubectl --kubeconfig=/root/m03-lab/mariana.kubeconfig auth can-i create pods -n projectx
kubectl --kubeconfig=/root/m03-lab/ivan.kubeconfig auth can-i create networkpolicies -n projectx
```

**Expected:** first two `yes`, NetworkPolicies `no` (the last is by design).
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SECURITY-2026.md 5 -->
### Task 6 — deploy the producer/consumer application as Ivan

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
<!-- MODERN_LAB_END -->


<!-- PRESERVED_THEORY_BEGIN -->
## [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)

Make sure that our cluster is using a **Network plugin** that supports **Network Policies**. Partial list of them can be found [here](https://kubernetes.io/docs/tasks/administer-cluster/declare-network-policy/) (**Flannel** plugin does not support network policies).
<!-- PRESERVED_THEORY_END -->


<!-- PRESERVED_THEORY_BEGIN -->
### Network policy example

Network policies are defined on namespace level

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: access-oracle
  namespace: basicnp
spec:
  # which pods will be affected by this policy in the namespace.
  podSelector:
    matchLabels:
      app: oracle
  # policy type (ingress - incomming communication, egress outgoing communication)
  ingress:
  # in egress policy section will be `to` (not from)
  - from:
    - podSelector:
        matchLabels:
          access: "true"
      namespaceSelector: {}
  # ports:
  # - protocol: TCP
  #   port: 6379  
```

***Note***: NetworkPolicy includes a ```podSelector``` which selects the grouping of Pods to which the policy applies. You can see this policy selects Pods with the label ```app=oracle```. An empty ```podSelector``` selects all pods in the namespace.

### Behavior of ```to``` and ```from``` selectors

There are four kinds of selectors that can be specified in an ```ingress``` ```from``` section or ```egress``` ```to``` section:

***podSelector*** - This selects particular Pods in the same namespace as the NetworkPolicy which should be allowed as ingress sources or egress destinations.

***namespaceSelector*** - This selects particular namespaces for which all Pods should be allowed as ingress sources or egress destinations.

***namespaceSelector*** and ***podSelector*** - A single ```to```/```from``` entry that specifies both ```namespaceSelector``` and ```podSelector``` selects particular Pods within particular namespaces. Be careful to use correct YAML syntax.

Example: 

Contains a single from element allowing connections ```from``` Pods with the label ```role=client``` in namespaces with the label ```user=alice```

```yaml
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          user: alice
      podSelector:
        matchLabels:
          role: client
```

Contains two elements in the ```from``` array, and allows connections from Pods in the local Namespace with the label ```role=client```, or from any Pod in any namespace with the label ```user=alice```.

```yaml
ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          user: alice
    - podSelector:
        matchLabels:
          role: client
```

When in doubt, use kubectl describe to see how Kubernetes has interpreted the policy.

### Default policies

By default, if no policies exist in a namespace, then all ingress and egress traffic is allowed to and from pods in that namespace. The following examples let you change the default behavior in that namespace.


#### Deny all ingress traffic

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

#### Allow all ingress traffic

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-all-ingress
spec:
  podSelector: {}
  ingress:
  - {}
  policyTypes:
  - Ingress
```

#### Deny all egress traffic

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-egress
spec:
  podSelector: {}
  policyTypes:
  - Egress
```

#### Allow all egress traffic 

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-all-egress
spec:
  podSelector: {}
  egress:
  - {}
  policyTypes:
  - Egress
```

#### Deny all ingress and all egress traffic

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```
<!-- PRESERVED_THEORY_END -->


<!-- MODERN_LAB_BEGIN SECURITY-2026.md 6 -->
### Task 7 — Calico NetworkPolicy producer ← consumer ← client

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
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SECURITY-2026.md 7 -->
### Cleanup

This deletes the dedicated lab namespace, which removes its Pods, NetworkPolicies, Services, quota, roles and other namespaced resources:

```bash
kubectl delete namespace projectx
rm -rf /root/m03-lab
```

The local temporary X.509 certificates are no longer used; they expire after 30 days. Their CA signing step was for a throwaway kubeadm cluster only. Do not copy the historical bundled private keys from the original course.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN SECURITY-2026.md 8 -->
### Static acceptance checklist

- [ ] Both user kubeconfigs are created using **your** CA/server, and show membership in lower-case group `gurus`
- [ ] Quota/LimitRange objects exist in projectx
- [ ] devguru allows deployments/pods/services/replicasets, but not NetworkPolicies
- [ ] Both producer and consumer roll out and have healthy Service endpoints
- [ ] Client reaches consumer and **not** producer after policies
- [ ] Consumer-labelled debug Pod reaches producer
- [ ] Namespace deletion cleans up the lab
<!-- MODERN_LAB_END -->

