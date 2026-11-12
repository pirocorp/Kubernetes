# Module 04 — Storage and Persistence

> **Learning edition (Kubernetes 1.37).** The theory of Docker/Kubernetes volumes, PV/PVC lifecycle, configuration and StatefulSets appears before the current matching exercises. Historical 2021 PV/StatefulSet deployment commands are **replaced** by the reproducible NFS and configuration labs below. Existing original DOCX/ZIP materials remain available as historical sources.

## Learning path and objectives

Understand how container storage lifetimes differ, how NFS/PersistentVolumes bind to claims, how ConfigMaps/Secrets configure applications, and why StatefulSets provide stable identity. Complete the modern labs using the [course baseline](../README.md), verifying `Retain` behavior rather than assuming deletion erases data.

## Kubernetes 1.37 integrated labs


<!-- MODERN_LAB_BEGIN STORAGE-2026.md 0 -->
## Module 04 — Storage and Persistence lab (Kubernetes 1.37)

> **NOTE (2026):** This is the executable entry point for the original Module 04 practice and homework. The original DOCX/ZIP/README material records the 2021 course, including `gitRepo` (disabled since 1.36) and the deprecated PV `Recycle` policy. Use this guide and the revised YAML files instead of replaying those historical commands. Module 02's [SETUP-2026.md](../02.%20Cluster%20Setup%20and%20Management/SETUP-2026.md) provides the baseline Kubernetes 1.37 / containerd / Calico cluster.
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN STORAGE-2026.md 1 -->
### 1. Prerequisites and safety

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
<!-- MODERN_LAB_END -->

> **Reading order:** The optional historical `gitRepo` replacement is numbered *6* in the original lab guide but appears early here because it directly demonstrates the `emptyDir` concept. The NFS and StatefulSet core exercises numbered 2–5 follow below.

## Containers and ephemeral data — original concepts

> The Docker examples here teach bind mounts and volumes conceptually. They are **supplementary** and are not the Kubernetes 1.37 homework procedure.


<!-- PRESERVED_THEORY_BEGIN -->
## The [Docker Way](https://docs.docker.com/storage/volumes/)

- Bind Mounts are dependent on the OS and file system structure
- Volumes are managed by Docker
- tmpfs mount is for non-persistent state data

![image](https://user-images.githubusercontent.com/34960418/147826579-0d7af643-404c-44e0-9fb4-4c537dfda4d1.png)

### Bind Mounts

For the usual example, create a ~/html folder. There, we can create an **index.html** file.

```bash
echo 'A simple <b>bind mount</b> test' | tee ~/html/index.html
```

Finally, we can run a NGINX based container and mount the folder there

```bash
docker container run -d --name web -p 80:80 -v $(pwd)/html:/usr/share/nginx/html:ro nginx
```

Then, of course, if we ask for the web page

```bash
curl http://localhost
```

We will see our sample page. Should we want, we can ask for detailed information about the container.

```bash
docker container inspect web
```

We should pay attention to the **Mounts** section and especially on the **Type** which should be set to **bind**.

![image](https://user-images.githubusercontent.com/34960418/147827027-0e6560c4-89b8-43b8-a81c-dafaa703c85f.png)

Remove the container

```bash
docker container rm web --force
```

#
<!-- PRESERVED_THEORY_END -->


<!-- PRESERVED_THEORY_BEGIN -->
## Volumes

First, create a volume

```bash
docker volume create demo
```

Then list the available volumes

```bash
docker volume ls
```

And then, inspect the volume we just created

```bash
docker volume inspect demo
```

Now, that we know where its data reside, we can work directly with it. Let’s create a custom **index.html** page again.

```bash
echo 'A simple <b>volume</b> test' | tee /var/lib/docker/volumes/demo/_data/index.html
```

Now, start a container that will mount the volume

```bash
docker container run -d --name web -p 80:80 -v demo:/usr/share/nginx/html:ro nginx
```

Alternatively, use the --mount option. Then the command will look like


```bash
docker container run -d --name web -p 80:80 --mount source=demo,destination=/usr/share/nginx/html nginx
```

Ask for the web page. Will see the sample page.

```bash
curl http://localhost
```

Let’s ask for detailed information about the container. Again, pay attention to the **Mounts** section and especially on the **Type** which should this time be set to **volume**.

```bash
docker container inspect web
```

Remove the container

```bash
docker container rm web --force
```

And then remove the volume as well

```bash
docker volume rm demo
```

## Volumes

On-disk files in a container are ephemeral, which presents some problems for non-trivial applications when running in containers. One problem is the loss of files when a container crashes. The kubelet restarts the container but with a clean state. A second problem occurs when sharing files between containers running together in a Pod. The Kubernetes **volume** abstraction solves both of these problems.

**Ephemeral volume** types have a lifetime of a pod, but persistent volumes exist beyond the lifetime of a pod. When a pod ceases to exist, Kubernetes destroys ephemeral volumes; however, Kubernetes does not destroy persistent volumes. For any kind of volume in a given pod, data is preserved across container restarts.

At its core, a volume is a directory, possibly with some data in it, which is accessible to the containers in a pod. How that directory comes to be, the medium that backs it, and the contents of it are determined by the particular volume type used.

To use a volume, specify the volumes to provide for the Pod in ```.spec.volumes``` and declare where to mount those volumes into containers in ```.spec.containers[*].volumeMounts```. A process in a container sees a filesystem view composed from the initial contents of the container image, plus volumes (if defined) mounted inside the container. The process sees a root filesystem that initially matches the contents of the container image. Any writes to within that filesystem hierarchy, if allowed, affect what that process views when it performs a subsequent filesystem access. Volumes mount at the specified paths within the image. For each container defined within a Pod, you must independently specify where to mount each volume that the container uses.

### EmptyDir

An **emptyDir** volume is first created when a Pod is assigned to a node, and exists as long as that Pod is running on that node. As the name says, the **emptyDir** volume is initially empty. All containers in the Pod can read and write the same files in the **emptyDir** volume, though that volume can be mounted at the same or different paths in each container. When a Pod is removed from a node for any reason, the data in the **emptyDir** is deleted permanently.

***Note***: A container crashing does not remove a Pod from a node. The data in an **emptyDir** volume is safe across container crashes.

Depending on your environment, **emptyDir** volumes are stored on whatever medium that backs the node such as disk or SSD, or network storage. However, if you set the ```emptyDir.medium``` field to ```"Memory"```, Kubernetes mounts a tmpfs (RAM-backed filesystem) for you instead. While tmpfs is very fast, be aware that unlike disks, tmpfs is cleared on node reboot and any files you write count against your container's memory limit.


![image](https://user-images.githubusercontent.com/34960418/143465833-9840c0d1-ecb4-4dbd-ad3f-5e713ebd9994.png)
![image](https://user-images.githubusercontent.com/34960418/143465996-27bdadde-f83c-4c6d-af43-7ee57dbca3f7.png)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-ed
  labels:
    app: notes
spec:
  containers:
  - image: shekeriev/k8s-notes
    name: container-ed
    # Where to mount those volumes into containers
    volumeMounts:
      # Mount path in container
    - mountPath: /data
      # Volume name
      name: data-volume
  # Volumes descriptions
  volumes:
    # Volume name
  - name: data-volume
    # Volume type
    emptyDir: {}
```
<!-- PRESERVED_THEORY_END -->


<!-- MODERN_LAB_BEGIN STORAGE-2026.md 6 -->
### 6. `gitRepo` alternative

Use [README.md — Git repository files in a Pod](./README.md#git-repository-files-in-a-pod--emptydir--init-container-kubernetes-137), which includes the complete supported init-container YAML, apply, readiness, logging, port-forward and cleanup steps. Do not execute the original `part1/git-pod.yaml` from the historical ZIP.
<!-- MODERN_LAB_END -->


<!-- PRESERVED_THEORY_BEGIN -->
### HostPath

A **hostPath** volume mounts a file or directory from the host node's filesystem into your Pod. In addition to the required **path** property, you can optionally specify a **type** for a **hostPath** volume.

The supported values for field **type** are:


| Value             	| Behavior                                                                                                                                                               	|
|-------------------	|------------------------------------------------------------------------------------------------------------------------------------------------------------------------	|
|                   	| Empty string (default) is for backward compatibility, which means that no checks will be performed before mounting the hostPath volume.                                	|
| DirectoryOrCreate 	| If nothing exists at the given path, an empty directory will be created there as needed with permission set to 0755, having the same group and ownership with Kubelet. 	|
| Directory         	| A directory must exist at the given path                                                                                                                               	|
| FileOrCreate      	| If nothing exists at the given path, an empty file will be created there as needed with permission set to 0644, having the same group and ownership with Kubelet.      	|
| File              	| A file must exist at the given path                                                                                                                                    	|
| Socket            	| A UNIX socket must exist at the given path                                                                                                                             	|
| CharDevice        	| A character device must exist at the given path                                                                                                                          |
| BlockDevice        	| A block device must exist at the given path
               

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: notes-deploy
spec:
  replicas: 3
  selector:
    matchLabels: 
      app: notes
  template:
    metadata:
      labels:
        app: notes
    spec:
      containers:
      - name: container-hp
        image: shekeriev/k8s-notes
        volumeMounts:
        - mountPath: /data
          name: hp-data
      volumes:
      - name: hp-data
        # volume type
        hostPath:
          # path from node (this path must exist on every worker node) where container is started. And will be mount to mountPath.
          path: /tmp/data
          type: Directory
```


### NFS

An **nfs** volume allows an existing NFS (Network File System) share to be mounted into a Pod. Unlike **emptyDir**, which is erased when a Pod is removed, the contents of an **nfs** volume are preserved and the volume is merely unmounted. This means that an NFS volume can be pre-populated with data, and that data can be shared between pods. NFS can be mounted by multiple writers simultaneously.


***Note***: You must have your own NFS server running with the share exported before you can use it.

Assume that there is a **NFS** server available and accessible by name (**nfs-server**).

-	That the NFS server is reachable by that name from all nodes
```bash
echo 'nfs-server-ip   nfs-server' >> /etc/hosts
```

-	That on every node there is NFS client installed
```bash
apt-get update && apt-get install -y nfs-common
```

-	That the exported path is writable (in our case by everyone)
```bash
chmod -R 777 /data/nfs/k8sdata
```

Prepare the **nfs-deployment.yaml** manifest with the following content.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: notes-deploy
spec:
  replicas: 3
  selector:
    matchLabels: 
      app: notes
  template:
    metadata:
      labels:
        app: notes
    spec:
      containers:
      - name: container-nfs
        image: shekeriev/k8s-notes
        volumeMounts:
          # On which path for container exposed path will be mounted
        - mountPath: /data
          name: nfs-data
      volumes:
      - name: nfs-data
        nfs:
          server: nfs-server
          # Exposed path by NFS Server
          path: /data/nfs/k8sdata
```

Push deployment to the cluster

```bash
kubectl apply -f nfs-deployment.yaml
```

Check the pods and where they went

```bash
kubectl get pods -o wide
```

Now, open a browser tab, and navigate to ```http://<cluster-node-ip>:30001/index.php```. Enter a few notes. Refresh a few times. Notes are there and seen by all pods. Describe one of the pods. And pay attention to the **Volumes** section

```bash 
kubectl describe pod notes-deploy-<specific-id>
```

Clean up

```bash
kubectl delete -f nfs-deployment.yaml
```
<!-- PRESERVED_THEORY_END -->


<!-- MODERN_LAB_BEGIN STORAGE-2026.md 2 -->
### 2. Prepare NFS exports (run on NFS server only)

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
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN STORAGE-2026.md 3 -->
### 3. Prepare clients (run on cp1, wk1 and wk2)

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
<!-- MODERN_LAB_END -->


<!-- PRESERVED_THEORY_BEGIN -->
## Persistent Volumes and Claims

A PersistentVolume (PV) is a piece of storage in the cluster that has been provisioned by an administrator or dynamically provisioned using Storage Classes. PVs have a lifecycle independent of any individual Pod that uses the PV.


A PersistentVolumeClaim (PVC) is a request for storage by a user. It is similar to a Pod. Pods consume node resources and PVCs consume PV resources. Pods can request specific levels of resources (CPU and Memory). Claims can request specific size and access modes (e.g., they can be mounted ReadWriteOnce, ReadOnlyMany or ReadWriteMany).


![image](https://user-images.githubusercontent.com/34960418/145032191-76621524-d189-436c-81b4-f75f1cc40adf.png)

### Lifecycle of a volume and claim

PVs are resources in the cluster. PVCs are requests for those resources and also act as claim checks to the resource. The interaction between PVs and PVCs follows this lifecycle:

- **Provisioning** - There are two ways PVs may be provisioned: statically or dynamically. Static: a cluster administrator creates a number of PVs. They carry the details of the real storage, which is available for use by cluster users. They exist in the Kubernetes API and are available for consumption. Dynamic: This provisioning is based on StorageClasses.
- **Binding** - A user creates (or in the case of dynamic provisioning, has already created), a **PersistentVolumeClaim** with a specific amount of storage requested and with certain access modes. A control loop in the master watches for new PVCs, finds a matching PV (if possible), and binds them together. The user will always get at least what they asked for, but the volume may be in excess of what was requested. Once bound, **PersistentVolumeClaim** binds are exclusive, regardless of how they were bound. A PVC to PV binding is a one-to-one mapping, using a **ClaimRef** which is a bi-directional binding between the **PersistentVolume** and the **PersistentVolumeClaim**.
- **Using** - Pods use claims as volumes. The cluster inspects the claim to find the bound volume and mounts that volume for a Pod. For volumes that support multiple access modes, the user specifies which mode is desired when using their claim as a volume in a Pod.
- **Reclaiming** - When a user is done with their volume, they can delete the PVC objects from the API that allows reclamation of the resource. The reclaim policy for a PersistentVolume tells the cluster what to do with the volume after it has been released of its claim. The actively supported reclaim-policy choices for this lab are **Retain** and **Delete** (the historical **Recycle** behavior is deprecated).
  - **Retain** allows for manual reclamation of the resource
  - **Delete** removes both the PV object from Kubernetes, as well as the associated storage asset in the external infrastructure
  - **Recycle (historical only)** attempted automatic scrubbing; deprecated and **not used** in the 2026 lab. Use **Retain** for the static NFS examples, where data is preserved and reclaim is manual.

### Access Modes

A PersistentVolume can be mounted on a host in any way supported by the resource provider. For example, NFS can support multiple read/write clients. The access modes are:

- **ReadWriteOnce** - the volume can be mounted as read-write by a single node. ReadWriteOnce access mode still can allow multiple pods to access the volume when the pods are running on the same node.
- **ReadOnlyMany** - the volume can be mounted as read-only by many nodes.
- **ReadWriteMany** - the volume can be mounted as read-write by many nodes.
- **ReadWriteOncePod** - the volume can be mounted as read-write by a single Pod. Use ReadWriteOncePod access mode if you want to ensure that only one pod across whole cluster can read that PVC or write to it.
<!-- PRESERVED_THEORY_END -->

> **Modernization:** The legacy manual `pvnfs10gb.yaml` walkthrough and the old StatefulSet deployment examples are replaced by the verified file paths and PVC binding checks of **Problem 2** below. The storage concepts above still apply.


<!-- PRESERVED_THEORY_BEGIN -->
## Environment Variables

- **Key-value pairs** used to pass data to the containers inside a pod.
- Created in the manifest via **env** or **envFrom** blocks.
- **Override** any environment variables in the container.
- They may **reference** each other but then their **definition order is important**.
- Reference is done via the **$(REFVAR)** construct

When you create a Pod, you can set environment variables for the containers that run in the Pod. To set environment variables, include the ```env``` or ```envFrom``` field in the configuration file.

Environment variables that you define in a Pod's configuration can be used elsewhere in the configuration, for example in commands and arguments that you set for the Pod's containers.

***Note***: The environment variables set using the env or envFrom field override any environment variables specified in the container image.

***Note***: Environment variables may reference each other, however ordering is important. Variables making use of others defined in the same context must come later in the list. Similarly, avoid circular references.


```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-w-env
  labels:
    app: environ
spec:
  containers:
  - image: shekeriev/k8s-environ
    name: cont-w-env
    # Environment variables (key - value pairs)
    env:
    - name: XYZ1
      value: "VALUE1"
    - name: XYZ2
      value: "42"
```

Send it to the cluster

```bash
kubectl apply -f pod-w-env.yaml
```

Llet’s describe it to see if the variables will appear there. Pay attention to the Environment section. Our variables are there.

```bash
kubectl describe pod pod-w-env
```

Clean up

```bash
kubectl delete -f pod-w-env.yaml
```

## Configuration Maps

- Used to store **non-confidential data** in key-value pairs.
- Pods can consume them as **environment variables**, **command-line arguments**, or as **configuration files in volumes**.
- We use them to **separate configuration data** from **application code**.
- They are not designed to store large chucks of data (**max 1 MiB**).
- The name of a **ConfigMap** must be a **valid DNS subdomain** name.


A ConfigMap is an API object used to store non-confidential data in key-value pairs. Pods can consume ConfigMaps as environment variables, command-line arguments, or as configuration files in a volume.

A ConfigMap allows you to decouple environment-specific configuration from your container images, so that your applications are easily portable.

A ConfigMap is not designed to hold large chunks of data. The data stored in a ConfigMap cannot exceed 1 MiB. If you need to store settings that are larger than this limit, you may want to consider mounting a volume or use a separate database or file service.

A ConfigMap is an API object that lets you store configuration for other objects to use. Unlike most Kubernetes objects that have a ```spec```, a ConfigMap has ```data``` and ```binaryData``` fields. These fields accept key-value pairs as their values. Both the ```data``` field and the ```binaryData``` are optional. The ```data``` field is designed to contain UTF-8 byte sequences while the ```binaryData``` field is designed to contain binary data as base64-encoded strings. The keys stored in ```data``` must not overlap with the keys in the ```binaryData``` field.

**Caution**: ConfigMap does not provide secrecy or encryption. If the data you want to store are confidential, use a Secret rather than a ConfigMap, or use additional (third party) tools to keep your data private.

You can write a Pod ```spec``` that refers to a ConfigMap and configures the container(s) in that Pod based on the data in the ConfigMap. The Pod and the ConfigMap must be in the same namespace.

***Note***: The spec of a static Pod cannot refer to a ConfigMap or any other API objects.

There are four different ways that you can use a ConfigMap to configure a container inside a Pod:

- Inside a container command and args
- Environment variables for a container
- Add a file in read-only volume, for the application to read
- Write code to run inside the Pod that uses the Kubernetes API to read a ConfigMap

### Using ConfigMaps as files from a Pod

To consume a ConfigMap in a volume in a Pod:

1. Create a ConfigMap or use an existing one. Multiple Pods can reference the same ConfigMap.
2. Modify your Pod definition to add a volume under ```.spec.volumes[]```. Name the volume anything, and have a ```.spec.volumes[].configMap.name``` field set to reference your ConfigMap object.
3. Add a ```.spec.containers[].volumeMounts[]``` to each container that needs the ConfigMap. Specify ```.spec.containers[].volumeMounts[].readOnly = true``` and ```.spec.containers[].volumeMounts[].mountPath``` to an unused directory name where you would like the ConfigMap to appear.
4. Modify your image or command line so that the program looks for files in that directory. Each key in the ConfigMap ```data``` map becomes the filename under ```mountPath```.

Each ConfigMap you want to use needs to be referred to in ```.spec.volumes```.

If there are multiple containers in the Pod, then each container needs its own ```volumeMounts``` block, but only one ```.spec.volumes``` is needed per ConfigMap.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: environ-map-1
# Evnironment variables (list of key-value pairs)
data:
  XYZ1: "VALUE1"
  XYZ2: "42"
  XYZ3: "3.14"
```

We can load an environment variable with data coming from a ConfigMap

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-cm-env-var
  labels:
    app: environ
spec:
  containers:
  - image: shekeriev/k8s-environ
    name: cont-w-env
    # Declaring environment variables
    env:
    # Value for variable XYZ_FROM_CM will be taken from environ-map-1 ConfigMap variable XYZ2
    - name: XYZ_FROM_CM
      valueFrom:
        configMapKeyRef:
          name: environ-map-1
          key: XYZ2
```

Get all keys from the config map and send them as variables.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-cm-env-vars
  labels:
    app: environ
spec:
  containers:
  - image: shekeriev/k8s-environ
    name: cont-w-env
    # Consuming ConfigMaps or Secrets
    envFrom:
    # Add environment values from ConfigMap environ-map-1
    - configMapRef:
        name: environ-map-1
      #prefix: CM_ # Use this to prefix variables created from the ConfigMap
```

## Secrets

- Contain a small amount of sensitive data such as a **password**, a **token**, or a **key**.
- This way confidential data is separated from the application code.
- Similar to **ConfigMaps** but are specifically intended to hold confidential data.
- Consumed via **files in a volume**, **environment variables**, or by the kubelet while pulling images for the pod (**imagePullSecrets**).
- Secrets can be **opaque**, **tls**, **token**, **service-account-token**, etc.


A Secret is an object that contains a small amount of sensitive data such as a password, a token, or a key. Such information might otherwise be put in a Pod specification or in a container image. Using a Secret means that you don't need to include confidential data in your application code.

Because Secrets can be created independently of the Pods that use them, there is less risk of the Secret (and its data) being exposed during the workflow of creating, viewing, and editing Pods. Kubernetes, and applications that run in your cluster, can also take additional precautions with Secrets, such as avoiding writing confidential data to nonvolatile storage.

Secrets are similar to ConfigMaps but are specifically intended to hold confidential data.

To use a Secret, a Pod needs to reference the Secret. A Secret can be used with a Pod in three ways:

- As files in a volume mounted on one or more of its containers.
- As container environment variable.
- By the kubelet when pulling images for the Pod.

### Types of Secret

When creating a Secret, you can specify its type using the type field of a Secret resource, or certain equivalent kubectl command line flags (if available). The type of a Secret is used to facilitate programmatic handling of different kinds of confidential data.

Kubernetes provides several builtin types for some common usage scenarios. These types vary in terms of the validations performed and the constraints Kubernetes imposes on them.

| Value             	| Behavior                                                                                                                                                               	|
|-------------------	|------------------------------------------------------------------------------------------------------------------------------------------------------------------------	|
|                   	| Empty string (default) is for backward compatibility, which means that no checks will be performed before mounting the hostPath volume.                                	|
| DirectoryOrCreate 	| If nothing exists at the given path, an empty directory will be created there as needed with permission set to 0755, having the same group and ownership with Kubelet. 	|
| Directory         	| A directory must exist at the given path                                                                                                                               	|
| FileOrCreate      	| If nothing exists at the given path, an empty file will be created there as needed with permission set to 0644, having the same group and ownership with Kubelet.      	|
| File              	| A file must exist at the given path                                                                                                                                    	|
| Socket            	| A UNIX socket must exist at the given path                                                                                                                             	|
| CharDevice        	|                                                                                                                                                                        	|

### Opaque secrets

**Opaque** is the default Secret type if omitted from a Secret configuration file. When you create a Secret using **kubectl**, you will use the **generic** subcommand to indicate an **Opaque** Secret type. For example, the following command creates an empty Secret of type **Opaque**.

```bash
kubectl create secret generic empty-secret
kubectl get secret empty-secret
```

Create Secret From Manifest

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mysecrets
  namespace: default
# Secrets (list of key-value pairs) values are base64 encoded.
data:
  password1: S3ViZXJuZXRlc1JvY2tzIQo=
  password2: U3VwZXJTZWNyZXRQQHNzdzByZAo=
  message: S3ViZXJuZXRlcyBpcyBib3RoIGZ1biBhbmQgZWFzeSB0byBsZWFybiA7KQo=
```

Consuming secrets

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-secret
  labels:
    app: environ
spec:
  containers:
  - image: shekeriev/k8s-environ
    name: cont-w-env
    envFrom:
    # Add environment values from Secret mysecrets
    - secretRef:
        name: mysecrets
      prefix: XYZ_
```
<!-- PRESERVED_THEORY_END -->


<!-- MODERN_LAB_BEGIN STORAGE-2026.md 4 -->
### 4. ConfigMap and Secret homework (Problem 1)

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
<!-- MODERN_LAB_END -->


<!-- PRESERVED_THEORY_BEGIN -->
## StatefulSet

- Used to manage **stateful applications**.
- Manage the deployment of a **set of Pods**.
- Pods are with identical container specifications just **like** with **Deployment** and **ReplicaSet**.
- The main **difference** here is that the Pods have **persistent identifiers** that are **maintained across rescheduling**.
- **Storage volumes** can be used as part of the solution for providing persistence.

StatefulSet is the workload API object used to manage stateful applications. Manages the deployment and scaling of a set of Pods, and provides guarantees about the ordering and uniqueness of these Pods. Like a Deployment, a StatefulSet manages Pods that are based on an identical container spec. Unlike a Deployment, a StatefulSet maintains a sticky identity for each of their Pods. These pods are created from the same spec, but are not interchangeable: each has a persistent identifier that it maintains across any rescheduling.

If you want to use storage volumes to provide persistence for your workload, you can use a StatefulSet as part of the solution. Although individual Pods in a StatefulSet are susceptible to failure, the persistent Pod identifiers make it easier to match existing volumes to the new Pods that replace any that have failed.

Using StatefulSets

StatefulSets are valuable for applications that require one or more of the following.

- Stable and unique network identifiers
- Stable and persistent storage
- Ordered graceful deployment and scaling
- Ordered and automated rolling updates

* Stable = persistence across pod (re)scheduling.
* Ordered = when scaling up it is done from 0 to N and when scaling down it is done from N to 0.

Stateful Sets Limitations

- Storage for a Pod must be provisioned **upfront** either automatically or by an administrator.
- Deleting or scaling down **doesn’t delete the associated volumes**.
- **Headless service** is required for the network identity of the pods.
- StatefulSet deletion **doesn’t guarantee the pods termination order**. If required, first we must scale it down to 0.
- Rolling updates (with OrderedReady policy) may get broken and then a manual intervention may be required.


![image](https://user-images.githubusercontent.com/34960418/145412355-67d48f68-8078-444e-b5fc-462ae3ec5826.png)
<!-- PRESERVED_THEORY_END -->


<!-- MODERN_LAB_BEGIN STORAGE-2026.md 5 -->
### 5. NFS + StatefulSet + frontend homework (Problem 2)

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

#### Clean up the lab without erasing NFS data

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
<!-- MODERN_LAB_END -->


<!-- MODERN_LAB_BEGIN STORAGE-2026.md 7 -->
### Static validation / troubleshooting checklist

- [ ] Correct K8s context and Ready nodes
- [ ] NFS server shares exported, client can mount NFSv4.1 from every node
- [ ] Manifest PV storageClassName matches PVC storageClassName (`""`)
- [ ] StatefulSet PV/PVC counts and capacity match the task
- [ ] Only one lab occupies TCP NodePort 30001 at a time
- [ ] Verify actual Pods/Services/PVCs rather than trusting old 2021 screenshots
- [ ] Clean up PVCs explicitly; understand `Retain` and manual PV reclamation

External references: [Kubernetes volumes](https://kubernetes.io/docs/concepts/storage/volumes/), [PersistentVolume reclaiming](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#reclaiming), [NFS server](https://ubuntu.com/server/docs/service-nfs).
<!-- MODERN_LAB_END -->

