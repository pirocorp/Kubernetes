# Module 03 — Security and Policies

> **Integrated edition · Kubernetes 1.37 (2026).** This README now contains the entire current hands-on lesson **and** the untouched original explanation and examples. The historical material remains educational but its retired APIs/CNI/scripts must not be replayed on the modern cluster.

## Recommended learning path

1. Use the course-wide [Kubernetes 1.37 roadmap](../COURSE-2026.md) to establish the required environment.
2. Read the preserved original lecture for conceptual depth, then complete [the integrated labs](#kubernetes-137-integrated-labs) in order with their verification and cleanup steps.
3. Contrast historical methods with their current counterparts below; retain the principle, not obsolete commands or manifest API versions.

| Preserved original concepts | Integrated current treatment |
|---|---|
| kubeconfig, identities and authorization | Fresh X.509 users, groups and RBAC; permission-denial checks |
| Resource requests, limits, quota | LimitRange and ResourceQuota with verifiable effects |
| NetworkPolicy ingress and egress | Calico 3.33 traffic allow/deny on the existing cluster; no CNI mixing |

## Kubernetes 1.37 integrated labs

> **Supported execution path:** Follow these instructions and modernized repository manifests. Historical lecture commands after this section are a reference, not a deployable 1.37 runbook. The written procedure is statically reviewed, not live-cluster certified.

## Module 03 — Security and NetworkPolicy homework (Kubernetes 1.37)

> **NOTE (2026):** Self-contained execution path for the seven original homework tasks. Use the **Calico 3.33 / VXLAN / BGP disabled** cluster prepared via [SETUP-2026.md](../02.%20Cluster%20Setup%20and%20Management/SETUP-2026.md); **do not** install an additional CNI. Original 2021 DOCX/author-solution certificates and old API addresses are **not reusable**.

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

### Cleanup

This deletes the dedicated lab namespace, which removes its Pods, NetworkPolicies, Services, quota, roles and other namespaced resources:

```bash
kubectl delete namespace projectx
rm -rf /root/m03-lab
```

The local temporary X.509 certificates are no longer used; they expire after 30 days. Their CA signing step was for a throwaway kubeadm cluster only. Do not copy the historical bundled private keys from the original course.

### Static acceptance checklist

- [ ] Both user kubeconfigs are created using **your** CA/server, and show membership in lower-case group `gurus`
- [ ] Quota/LimitRange objects exist in projectx
- [ ] devguru allows deployments/pods/services/replicasets, but not NetworkPolicies
- [ ] Both producer and consumer roll out and have healthy Service endpoints
- [ ] Client reaches consumer and **not** producer after policies
- [ ] Consumer-labelled debug Pod reaches producer
- [ ] Namespace deletion cleans up the lab

---

## Preserved original lecture — historical reference

> **2021 course snapshot.** This original Markdown lecture is preserved byte-for-byte to retain its educational value. For runnable commands, use the modern lab above.

<!-- ORIGINAL_MODULE_README_PRESERVED_START -->
> **Kubernetes 1.37 (2026) homework:** Start with [SECURITY-2026.md](./SECURITY-2026.md) to complete all seven tasks with real user certificates, quota/LimitRange, devguru RBAC, Calico NetworkPolicy testing, expected results and cleanup. The historical practice and author certificates are not reusable.

# Security and Policies

# Default Cluster User

Log on to the control plane node. Check the cluster configuration file.

```bash
cat ~/.kube/config
```

We can see that there are several notable sections – clusters, contexts, current-context, and users. Clusters section contains currently registered clusters with their certificate authority data, control plane and name. Contexts section contains list of currently registered contexts that combine clusters with users. Current context specifies against which context our commands will be fired by default and without the need to explicitly specifying it. Users section contains the list of registered users with their name, certificate and key. Should we want to control more than one cluster or interact as different users, then we must alter this file or use another copy.

# Additional Cluster Users

Utilizing the option for using X.509 client certificates for cluster authentication.

Create the **pirocorp** OS user

```bash
useradd -m -s /bin/bash pirocorp
```
Switch to its home folder

```bash
cd /home/pirocorp
```

Create a folder for the certificate related files and change to it

```bash
mkdir .certs && cd .certs
```

Create a private key

```bash
openssl genrsa -out pirocorp.key 2048
```

Create a certificate signing request

```bash
openssl req -new -key pirocorp.key -out pirocorp.csr -subj "/CN=pirocorp"
```

Sign the **CSR** with the **Kubernetes CA** certificate

```bash
openssl x509 -req -in pirocorp.csr -CA /etc/kubernetes/pki/ca.crt -CAkey /etc/kubernetes/pki/ca.key -CAcreateserial -out pirocorp.crt -days 365
```

Return to the home folder. Create the user in **Kubernetes**.

```bash
kubectl config set-credentials pirocorp --client-certificate=/home/pirocorp/.certs/pirocorp.crt --client-key=/home/pirocorp/.certs/pirocorp.key
```

Create context for the user as well

```bash
kubectl config set-context pirocorp-context --cluster=kubernetes --user=pirocorp
```

Create a folder to store the user configuration

```bash
mkdir /home/pirocorp/.kube
```

And create a file config there with the following content (most of it is skipped but borrowed from **/etc/kubernetes/admin.conf**). Everithumg up to ```contexts``` is borrowed.

```yaml
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUM1ekNDQWMrZ0F3SUJBZ0lCQURBTkJna3Foa2lHOXcwQkFRc0ZBREFWTVJNd0VRWURWUVFERXdwcmRXSmwKY201bGRHVnpNQjRYRFRJeE1URXhNekUwTlRrME1Wb1hEVE14TVRFeE1URTBOVGswTVZvd0ZURVRNQkVHQTFVRQpBeE1LYTNWaVpYSnVaWFJsY3pDQ0FTSXdEUVlKS29aSWh2Y05BUUVCQlFBRGdnRVBBRENDQVFvQ2dnRUJBTkIwClIvUi9lYkJkVVRteUxuMVBzb2tLQ2JaQU16TXBKMHRKS1prZlVxb0Jqa0dRVC9FUmVPK1krOS81MHZKTTNBUnoKTGMwR21MTGROVXdzeXFTb0xCUW5zWUVGaHBKNHhGSkhOU2hRb2EwYXdoZ3dWUUdwNEJaeHhNVE8zWkJIM2U3WQorZzZ1dlhSaFNmMWNNNURsRmtFcjhwTVFBS0hQdVFFMnRscWZBSzRQT0t3OWk5dHZ4SmpJbE1oNmVSQmRJOXFOCmh0c3dta0F0NFQ4MThPZVdOeXdGRWdyQjF0R1MwbnhDWENmMlZDbFJkejZEcVdRa1lGUElhN2NmTWlvMXh3MWQKdXNWekhEMW1rSDB2L1hkek1asdZ4Q3AwYTBTODZxdHA0aGo0d2tnb3RsSHhmeW14YWpmRUhiKzc5UWlFSFpJeQpFN0NYdlRyNXQ0Tlh1RXVKekZzQ0F3RUFBYU5DTUVBd0RnWURWUjBQQVFIL0JBUURBZ0trasdasdExVWRFd0VCCi93UUZNQU1CQWY4d0hRWURWUjBPQkJZRUZEazQ5Z094YXpoT2J0NUxOOWlJem9OTndkM3FNQTBHQ1NxR1NJYjMKRFFFQkN3VUFBNElCQVFDT0Z1eEd5SkgyVHNDaTkvN1ROTFNyVE1CNDU4c3JUdzB5d3d3WEpSYm5PNFQ2eDROdwpjOGF5ZUxybjFYQ1pSMGc1RVZTVHIrT3FqR0ZLM1lmRko0YjZ6V21zZ0ZKZm1JSStMWUZSMi9UaWhYZkI5cnNzCjZWb3lrdVdjbVVOZGNrYkhzSnk3MVFhS0FxQnFiSzdub2FEUlJiaHI4ZVpvTFpwOHRYa011cko4VzFIeFY1ODcKeml0REFCZW9wRG4wYStmVk9Vam9NYWJzNnRPTGJ6QXhIVGdpdlJLMk5HcURwQUUvRGRpdGtKcjk4Q0ZFK3U1LwpWMzJhekthUmJuS1N1aGFiWHhLSjlmM29LY2tYQWgyM3ZjaHNkb2ZPdGxRVHYybk9HMGUxcjc3emowRWk4SDl4CkZMV3hiajU0QkNGNzNPbWlVa2ZoWDJoV0RWYVpQNUtpV2MzWQotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tCg==
    server: https://192.168.0.53:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: pirocorp
  name: pirocorp-context
current-context: pirocorp-context
kind: Config
preferences: {}
users:
- name: pirocorp
  user:
    client-certificate: /home/pirocorp/.certs/pirocorp.crt
    client-key: /home/pirocorp/.certs/pirocorp.key
```

Save and close the file.

*Note that in the above example we are using **client-certificate** and **client-key** and not **client-certificate-data** and **client-key-data** as with the **admin.conf** file. We may go with the second pair, but then we must first encode using **base64** the content of both files and then use the result here.*


Change the ownership of the files

```bash
chown -R pirocorp: /home/pirocorp/
```

# Bind Cluster User to Role (RoleBinding)

- First rolebinding allows ```pirocorp``` to ```edit``` objects in ```demo-prod``` namespace.
- Second rolebinding allows ```pirocorp``` to ```view``` objects in ```demo-dev``` namespace.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: demo-prod-edit
  namespace: demo-prod
# Subcects (multiple) for which rolebinding is applied.
subjects:
- kind: User
  name: pirocorp
  apiGroup: rbac.authorization.k8s.io
# Role which will be bound to subjects
roleRef:
  # Role type (resource type) 
  kind: ClusterRole
  name: edit
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: demo-dev-view
  namespace: demo-dev
subjects:
- kind: User
  name: pirocorp
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: view
  apiGroup: rbac.authorization.k8s.io
```

Save and close the file and push it to the cluster.

```bash
kubectl apply -f role-bindings.yaml
```

# Permission Check

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

# Extend Service Account Permitions

The **default** service account doesn’t have any permissions granted by default.

![image](https://user-images.githubusercontent.com/34960418/147775473-ff572e21-4805-48a6-aa44-7156db592829.png)

Create Service Account

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: demo-sa
  namespace: rbac-ns
```

Save and close the file. Send the **Service Account** to the cluster.

```bash
kubectl apply -f service-account.yaml
```

Create Role

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
# Metadata specifies role name and in which namespace role is defined
metadata:
  name: demo-role
  namespace: rbac-ns
# Role can have multiple resources (resource types) with different access rights (verbs)
rules:
- apiGroups:
  - ""
  resources:
  - pods
  verbs:
  - get
  - list
  - create
  - delete
- apiGroups:
  - ""
  resources:
  - services
  verbs:
  - get
  - list
  - create
```

Save and close the file. Send the **Role** to the cluster.

```bash
kubectl apply -f role.yaml
```

Then create a **RoleBinding** for the Service Account and Role.

```bash
kubectl create rolebinding demo-role-binding --role=demo-role --serviceaccount=rbac-ns:demo-sa --namespace=rbac-ns
```

or send this yaml to cluster

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
# Specifies binding name and namespace
metadata:
  name: demo-role-binding
  namespace: rbac-ns
# Subjects (objects) which will be bound to the role
subjects:
- kind: ServiceAccount
  name: demo-sa
  namespace: rbac-ns
# Role to which objects are bound
roleRef:
  kind: Role
  name: demo-role
  apiGroup: rbac.authorization.k8s.io
```

Check that it got some of the permissions that we wanted to grant

```bash
kubectl auth can-i get pods --namespace rbac-ns --as system:serviceaccount:rbac-ns:demo-sa
kubectl auth can-i get services --namespace rbac-ns --as system:serviceaccount:rbac-ns:demo-sa
kubectl auth can-i delete pods --namespace rbac-ns --as system:serviceaccount:rbac-ns:demo-sa
kubectl auth can-i delete services --namespace rbac-ns --as system:serviceaccount:rbac-ns:demo-sa
```

Now, let’s start a new pod that will use this service account and check from there

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: demo-pod
  namespace: rbac-ns
spec:
  containers:
  - image: shekeriev/k8s-oracle
    name: demo-pod
  # Explisit specification of service account for this pod
  serviceAccount: demo-sa
  serviceAccountName: demo-sa
```

Save and close the file. Send the **Pod** to the cluster.

```bash
kubectl apply -f pod.yaml
```

Now, open a session to the pod


```bash
kubectl exec -it demo-pod -n rbac-ns -- bash
```

Install the missing curl command

```bash
apt-get update && apt-get install -y curl
```

Prepare a set of environment variables

```bash
APISERVER=https://kubernetes.default.svc
SERVICEACCOUNT=/var/run/secrets/kubernetes.io/serviceaccount
NAMESPACE=$(cat ${SERVICEACCOUNT}/namespace)
TOKEN=$(cat ${SERVICEACCOUNT}/token)
CACERT=${SERVICEACCOUNT}/ca.crt
```

Let’s check for the pods

```bash
curl --cacert ${CACERT} --header "Authorization: Bearer ${TOKEN}" \
-X GET ${APISERVER}/api/v1/namespaces/rbac-ns/pods
```

Let’s check for the services

```bash
curl --cacert ${CACERT} --header "Authorization: Bearer ${TOKEN}" \
-X GET ${APISERVER}/api/v1/namespaces/rbac-ns/services
```

# Requests and Limits

When you specify a **Pod**, you can optionally specify how much of each resource a **container** needs. The most common resources to specify are CPU and memory (RAM); there are others.

When you specify the resource **request** for containers in a Pod, the kube-scheduler uses this information to decide which node to place the Pod on. When you specify a resource **limit** for a container, the kubelet enforces those limits so that the running container is not allowed to use more of that resource than the limit you set. The kubelet also **reserves** at least the request amount of that system resource specifically for that container to use.

If the node where a Pod is running has enough of a resource available, it's possible (and allowed) for a container to use more resource than its **request** for that resource specifies. However, a container is not allowed to use more than its resource **limit**.

*Note: If a container specifies its own memory limit, but does not specify a memory request, Kubernetes automatically assigns a memory request that matches the limit. Similarly, if a container specifies its own CPU limit, but does not specify a CPU request, Kubernetes automatically assigns a CPU request that matches the limit.*

## Check the available resources on the nodes

Focus on the sections **Capacity**, **Allocatable**, **Non-terminated Pods**, and **Allocated resources**

![image](https://user-images.githubusercontent.com/34960418/147819663-cff90f05-477c-40ea-86eb-8ae5d03e5812.png)

```bash
kubectl describe nodes
```

## Pod with Requests and Limits

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

# Limit Ranges

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

# Resource Quotas

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

# [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)

Make sure that our cluster is using a **Network plugin** that supports **Network Policies**. Partial list of them can be found [here](https://kubernetes.io/docs/tasks/administer-cluster/declare-network-policy/) (**Flannel** plugin does not support network policies).

## CNI setup for the 2026 Kubernetes lab

> **NOTE (2026):** The Antrea, Calico and Weave Net install commands preserved below are **historical course examples**. Do **not** run them against the current Kubernetes 1.37 lab or mix them with another installed CNI. Install **one** CNI in a **fresh** cluster, with Pod CIDR matching the chosen network configuration.
>
> Our supported course path is **Calico v3.33.0 with VXLAN / BGP disabled** on Pod CIDR `10.244.0.0/16`. Follow [SETUP-2026.md — section 5, Install Calico](../02.%20Cluster%20Setup%20and%20Management/SETUP-2026.md#5-install-calico-v3330--vxlan--bgp-disabled-control-plane-node-only) and then [section 15, Validate NetworkPolicy](../02.%20Cluster%20Setup%20and%20Management/SETUP-2026.md#15-validate-networkpolicy-calico). **Do not reinstall Calico** when continuing Module 03 on an already-configured cluster.
>
> A Kubernetes `NetworkPolicy` resource has **no enforcement effect** unless the installed networking solution implements NetworkPolicy. Basic Flannel alone does not enforce these policies.

Verify your **existing** Calico installation before running the exercises:

```bash
kubectl get nodes
kubectl get tigerastatus
kubectl get pods -n calico-system
```

**Other CNIs:** Antrea is an alternative only on a **separate fresh cluster**; choose a published version-specific [Antrea release manifest](https://antrea.io/docs/v2.5.0/docs/getting-started/), not the moving `main` branch. **Weave Net is not recommended for a new lab:** its [upstream repository was archived in June 2024](https://github.com/weaveworks/weave), and the old `cloud.weave.works` installer should not be used.

<details>
<summary>Historical CNI installation examples (2021): Antrea, Calico, Weave Net — do not run on the current lab</summary>

## Instalation of [Antrea](https://github.com/antrea-io/antrea/blob/main/docs/getting-started.md) plugin

Assuming that cluster is created with 

```bash
kubeadm init --apiserver-advertise-address=<cp-address> --pod-network-cidr 172.16.0.0/16
```

Then the **Antrea** plugin can be installed with

```bash
kubectl apply -f https://raw.githubusercontent.com/antrea-io/antrea/main/build/yamls/antrea.yml
```


## Instalation of [Calico](https://docs.projectcalico.org/getting-started/kubernetes/quickstart )


Assuming that cluster is created with 

```bash
kubeadm init --apiserver-advertise-address=<cp-address> --pod-network-cidr 172.16.0.0/16
```

Then the Calico plugin can be installed with

```bash
kubectl apply -f https://docs.projectcalico.org/manifests/tigera-operator.yaml
```

Then download the custom resources manifest

```bash
curl https://docs.projectcalico.org/manifests/custom-resources.yaml -O
```

Adjust the configuration if needed by editing the **custom-resources.yaml** manifest (especially if you used something different than 192.168.0.0/16 for pod network). Then apply it.

```bash
kubectl apply -f custom-resources.yaml
```

## Instalation of [Weave Net](https://github.com/weaveworks/weave)

Assuming that we created our cluster with

```bash
kubeadm init --apiserver-advertise-address=<cp-address> --pod-network-cidr 10.32.0.0/12
```

Then the Weave Net plugin can be installed with

```bash
kubectl apply -f "https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d '\n')"
```

Should we want to change the configuration, for example the pod network addresses, we ca change it to

```bash
kubectl apply -f "https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d 'n')&env.IPALLOC_RANGE=10.200.0.0/16"
```
</details>

## Network policy example

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

## Behavior of ```to``` and ```from``` selectors

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

## Default policies

By default, if no policies exist in a namespace, then all ingress and egress traffic is allowed to and from pods in that namespace. The following examples let you change the default behavior in that namespace.


### Deny all ingress traffic

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

### Allow all ingress traffic

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

### Deny all egress traffic

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

### Allow all egress traffic 

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

### Deny all ingress and all egress traffic

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
