# Module 04 — Storage and Persistence lab (Kubernetes 1.37)

> **NOTE (2026):** This is the executable entry point for the original Module 04 practice and homework. The original DOCX/ZIP/README material records the 2021 course, including `gitRepo` (disabled since 1.36) and the deprecated PV `Recycle` policy. Use this guide and the revised YAML files instead of replaying those historical commands. Module 02's [SETUP-2026.md](../02.%20Cluster%20Setup%20and%20Management/SETUP-2026.md) provides the baseline Kubernetes 1.37 / containerd / Calico cluster.

## 1. Prerequisites and safety

- Working 1-control-plane + 2-worker cluster from Module 02; `kubectl` configured for the **lab cluster** and administrative permission to create PVs, Services and workloads.
- One separate reachable **Ubuntu 24.04 NFS server**, with 2 GiB+ free space per exported directory; example server IP `192.168.56.50`, **replace all addresses/subnets to match your lab**. The NFS server is not a Kubernetes worker and must be available while the app runs.
- DNS or `/etc/hosts` entry `nfs-server` from **all** cluster nodes and the machine running validation.
- Outbound HTTPS to pull container images, `nfs-common` client binaries on **every Kubernetes node**, TCP 2049 allowed **from Kubernetes node IPs to the NFS server**.
- Use a fresh lab; expected NodePort **30001** must be unused (it will conflict with other exercises using that same port). Run the earlier/other lab workloads sequentially, not concurrently.

```bash
kubectl version
kubectl get nodes -o wide
kubectl get storageclass
kubectl config current-context
```

**Expected:** cluster version 1.37.x; cp1 and both workers Ready; you have chosen the correct lab context. A default StorageClass is allowed: our **static** NFS solution explicitly uses `storageClassName: ""` for PVs and PVCs to prevent an accidental match to dynamic provisioning.

## 2. Prepare NFS exports (run on NFS server only)

**Dedicated disposable lab storage, not production.** The liberal directory mode below is intentional for the teaching exercise; for real deployments use mapped UID/GID, ACLs and the minimum necessary NFS export permissions.

```bash
sudo apt-get update
sudo apt-get install -y nfs-kernel-server
sudo mkdir -p /data/nfs/k8sdata /data/nfs/k8spva /data/nfs/k8spvb /data/nfs/k8spvc /data/nfs/k8spvd
sudo chmod 0777 /data/nfs/k8sdata /data/nfs/k8spva /data/nfs/k8spvb /data/nfs/k8spvc /data/nfs/k8spvd

# REPLACE 192.168.56.0/24 with your *Kubernetes node* subnet.
sudo tee /etc/exports.d/k8s-lab.exports >/dev/null <<'EOF'
/data/nfs/k8sdata 192.168.56.0/24(rw,sync,no_subtree_check)
/data/nfs/k8spva  192.168.56.0/24(rw,sync,no_subtree_check)
/data/nfs/k8spvb  192.168.56.0/24(rw,sync,no_subtree_check)
/data/nfs/k8spvc  192.168.56.0/24(rw,sync,no_subtree_check)
/data/nfs/k8spvd  192.168.56.0/24(rw,sync,no_subtree_check)
EOF
sudo exportfs -ra
sudo systemctl enable --now nfs-kernel-server
sudo exportfs -v
sudo systemctl is-active nfs-kernel-server
```

**Expected:** five exports active, including `k8spvd` (the original Module 06 screenshot omitted this path in an earlier step). Allow incoming TCP 2049 only from lab nodes in your NFS server firewall.

## 3. Prepare clients (run on cp1, wk1 and wk2)

```bash
sudo apt-get update
sudo apt-get install -y nfs-common
# REPLACE 192.168.56.50 with the IP of your NFS server, unless DNS already resolves nfs-server.
echo '192.168.56.50 nfs-server' | sudo tee -a /etc/hosts
getent hosts nfs-server
sudo mkdir -p /mnt/k8s-nfs-check
sudo mount -t nfs -o vers=4.1 nfs-server:/data/nfs/k8spva /mnt/k8s-nfs-check
mount | grep /mnt/k8s-nfs-check
sudo umount /mnt/k8s-nfs-check
```

**Expected:** name resolution works and the test share mounts and unmounts. Perform this on **all nodes**, not only cp1. If mounting fails, investigate TCP 2049, firewall, export CIDR, NFS server status and path permissions before continuing. A successful `ping` alone is insufficient.

## 4. ConfigMap and Secret homework (Problem 1)

From the repository root, navigate to `04. Storage and Persistence/Exercise/Solution/Problem 1 c/`. The following commands create the files required by the original homework and the provided `pod-hw.yaml`; use the **same namespace** for the ConfigMap, Secret and Pod (the example uses `default`).

```bash
kubectl config set-context --current --namespace=default
cat >main.conf <<'EOF'
name=homework
path=/tmp
certs=/secret
EOF
printf '8080\n' >port.conf

# Replace values with your cluster version and node OS if different.
kubectl create configmap hwcm --from-literal=k8sver=1.37 --from-literal=k8sos="Ubuntu 24.04" \
  --from-file=main.conf --from-file=port.conf
openssl genrsa -out main.key 2048
openssl req -new -x509 -key main.key -out main.crt -days 30 -subj /CN=www.hw.lab
kubectl create secret generic hwsec --from-file=main.key --from-file=main.crt
kubectl apply -f pod-hw.yaml
kubectl wait --for=condition=Ready pod/pod-hw --timeout=180s
kubectl describe pod pod-hw
kubectl exec pod-hw -- ls /config /secret
kubectl exec pod-hw -- printenv HW_PORT
```

**Expected:** the Pod is Ready, `/config/main.conf`, `/secret/main.key`, `/secret/main.crt` exist and `HW_PORT=8080`. These lab private keys must never be committed or reused. Clean up before moving on:

```bash
kubectl delete pod pod-hw --ignore-not-found
kubectl delete configmap hwcm --ignore-not-found
kubectl delete secret hwsec --ignore-not-found
rm -f main.key main.crt main.conf port.conf
```

## 5. NFS + StatefulSet + frontend homework (Problem 2)

Use `Exercise/Solution/Problem 2/solution.yaml` **from this repository**. It contains **three PVs** (`pvssa`, `pvssb`, `pvssc`), a 3-replica `StatefulSet/pod-be`, headless `Service/facts`, backend `Service/service-be`, 3-replica `Deployment/fe-deploy`, frontend `Service/service-fe`, and ConfigMap. PV reclaim policy is `Retain`, and static storage-class matching is explicit.

```bash
# From repository root:
kubectl apply -f "04. Storage and Persistence/Exercise/Solution/Problem 2/solution.yaml"
kubectl rollout status statefulset/pod-be --timeout=240s
kubectl rollout status deployment/fe-deploy --timeout=240s
kubectl get pv,pvc,pods,svc,deploy,statefulset
kubectl get endpointslices -l kubernetes.io/service-name=service-fe
```

**Expected:** 3 bound PVCs (one per StatefulSet ordinal), `pod-be-0..2` Ready, 3 frontend Pods Ready, NodePort **30001** on the frontend Service. The `spec.volumeClaimTemplates` in the StatefulSet use 2Gi each and match static PVs. If PVCs are Pending, check `kubectl describe pvc`, `kubectl get pv`, selectors/class, NFS exports and node reachability. PVCs need **no dynamic provisioner**.

From your workstation, open `http://<reachable-node-ip>:30001` (replace the placeholder; ensure the node firewall permits TCP 30001). Verify the frontend can reach the backend and storage persists across Pod restarts.

### Clean up the lab without erasing NFS data

```bash
# Remove workloads and namespaced resources first; do NOT delete the PVs yet.
kubectl delete deployment fe-deploy --ignore-not-found
kubectl delete statefulset pod-be --ignore-not-found
kubectl delete service facts service-be service-fe --ignore-not-found
kubectl delete configmap service-be-map --ignore-not-found
# StatefulSet PVCs are retained by default; delete them explicitly.
kubectl get pvc
kubectl delete pvc facts-data-pod-be-0 facts-data-pod-be-1 facts-data-pod-be-2 --ignore-not-found
# PVs with Retain now become Released, and NFS data remains.
kubectl get pv
```

**Important:** PVC deletion causes PVs with `Retain` to move to **Released**; the NFS data **remains**. A Released PV is not automatically available for another PVC. For another run, confirm/backup or delete the test files on NFS, delete those Released PV **objects**, and re-apply the solution. **Do not delete arbitrary NFS data**. This change avoids the deprecated automatic `Recycle` scrub.

```bash
# Only after verifying retained lab data and deciding to reclaim the storage:
kubectl delete pv pvssa pvssb pvssc --ignore-not-found
# Recreate the original PVs with the same YAML when starting another clean run.
```

## 6. `gitRepo` alternative

Use [README.md — Git repository files in a Pod](./README.md#git-repository-files-in-a-pod--emptydir--init-container-kubernetes-137), which includes the complete supported init-container YAML, apply, readiness, logging, port-forward and cleanup steps. Do not execute the original `part1/git-pod.yaml` from the historical ZIP.

## Static validation / troubleshooting checklist

- [ ] Correct K8s context and Ready nodes
- [ ] NFS server shares exported, client can mount NFSv4.1 from every node
- [ ] Manifest PV storageClassName matches PVC storageClassName (`""`)
- [ ] StatefulSet PV/PVC counts and capacity match the task
- [ ] Only one lab occupies TCP NodePort 30001 at a time
- [ ] Verify actual Pods/Services/PVCs rather than trusting old 2021 screenshots
- [ ] Clean up PVCs explicitly; understand `Retain` and manual PV reclamation

External references: [Kubernetes volumes](https://kubernetes.io/docs/concepts/storage/volumes/), [PersistentVolume reclaiming](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#reclaiming), [NFS server](https://ubuntu.com/server/docs/service-nfs).
