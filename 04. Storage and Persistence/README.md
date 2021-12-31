# The [Docker Way](https://docs.docker.com/storage/volumes/)

- Bind Mounts are dependent on the OS and file system structure
- Volumes are managed by Docker
- tmpfs mount is for non-persistent state data

![image](https://user-images.githubusercontent.com/34960418/147826579-0d7af643-404c-44e0-9fb4-4c537dfda4d1.png)

## Bind Mounts

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

# Volumes

On-disk files in a container are ephemeral, which presents some problems for non-trivial applications when running in containers. One problem is the loss of files when a container crashes. The kubelet restarts the container but with a clean state. A second problem occurs when sharing files between containers running together in a Pod. The Kubernetes **volume** abstraction solves both of these problems.

**Ephemeral volume** types have a lifetime of a pod, but persistent volumes exist beyond the lifetime of a pod. When a pod ceases to exist, Kubernetes destroys ephemeral volumes; however, Kubernetes does not destroy persistent volumes. For any kind of volume in a given pod, data is preserved across container restarts.

At its core, a volume is a directory, possibly with some data in it, which is accessible to the containers in a pod. How that directory comes to be, the medium that backs it, and the contents of it are determined by the particular volume type used.

To use a volume, specify the volumes to provide for the Pod in ```.spec.volumes``` and declare where to mount those volumes into containers in ```.spec.containers[*].volumeMounts```. A process in a container sees a filesystem view composed from the initial contents of the container image, plus volumes (if defined) mounted inside the container. The process sees a root filesystem that initially matches the contents of the container image. Any writes to within that filesystem hierarchy, if allowed, affect what that process views when it performs a subsequent filesystem access. Volumes mount at the specified paths within the image. For each container defined within a Pod, you must independently specify where to mount each volume that the container uses.

## EmptyDir

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

## GitRepo (deprecated)

A gitRepo volume is an example of a volume plugin. This plugin mounts an empty directory and clones a git repository into this directory for your Pod to use.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-git
  labels:
    app: notes
spec:
  containers:
  - image: php:apache
    name: container-git
    volumeMounts:
    - mountPath: /var/www/html
      name: git-volume
    - mountPath: /data
      name: data-volume
  volumes:
    # First volume name
  - name: git-volume
    # First volume type
    gitRepo:
      # The repository that will be cloned.
      repository: "https://github.com/shekeriev/k8s-notes.git"
      # Repository branch
      revision: "main"
      # Directory in which will be cloned.
      directory: .
    # Second volume name
  - name: data-volume
    emptyDir: {}
```

## HostPath

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


## NFS

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

# Persistent Volumes and Claims

A PersistentVolume (PV) is a piece of storage in the cluster that has been provisioned by an administrator or dynamically provisioned using Storage Classes. PVs have a lifecycle independent of any individual Pod that uses the PV.


A PersistentVolumeClaim (PVC) is a request for storage by a user. It is similar to a Pod. Pods consume node resources and PVCs consume PV resources. Pods can request specific levels of resources (CPU and Memory). Claims can request specific size and access modes (e.g., they can be mounted ReadWriteOnce, ReadOnlyMany or ReadWriteMany).


![image](https://user-images.githubusercontent.com/34960418/145032191-76621524-d189-436c-81b4-f75f1cc40adf.png)

## Lifecycle of a volume and claim

PVs are resources in the cluster. PVCs are requests for those resources and also act as claim checks to the resource. The interaction between PVs and PVCs follows this lifecycle:

- **Provisioning** - There are two ways PVs may be provisioned: statically or dynamically. Static: a cluster administrator creates a number of PVs. They carry the details of the real storage, which is available for use by cluster users. They exist in the Kubernetes API and are available for consumption. Dynamic: This provisioning is based on StorageClasses.
- **Binding** - A user creates (or in the case of dynamic provisioning, has already created), a **PersistentVolumeClaim** with a specific amount of storage requested and with certain access modes. A control loop in the master watches for new PVCs, finds a matching PV (if possible), and binds them together. The user will always get at least what they asked for, but the volume may be in excess of what was requested. Once bound, **PersistentVolumeClaim** binds are exclusive, regardless of how they were bound. A PVC to PV binding is a one-to-one mapping, using a **ClaimRef** which is a bi-directional binding between the **PersistentVolume** and the **PersistentVolumeClaim**.
- **Using** - Pods use claims as volumes. The cluster inspects the claim to find the bound volume and mounts that volume for a Pod. For volumes that support multiple access modes, the user specifies which mode is desired when using their claim as a volume in a Pod.
- **Reclaiming** - When a user is done with their volume, they can delete the PVC objects from the API that allows reclamation of the resource. The reclaim policy for a PersistentVolume tells the cluster what to do with the volume after it has been released of its claim. Currently, volumes can either be Retained, Recycled, or Deleted.
  - **Retain** allows for manual reclamation of the resource
  - **Delete** removes both the PV object from Kubernetes, as well as the associated storage asset in the external infrastructure
  - **Recycle** performs a basic scrub on the volume and makes it available again (deprecated)

## Access Modes

A PersistentVolume can be mounted on a host in any way supported by the resource provider. For example, NFS can support multiple read/write clients. The access modes are:

- **ReadWriteOnce** - the volume can be mounted as read-write by a single node. ReadWriteOnce access mode still can allow multiple pods to access the volume when the pods are running on the same node.
- **ReadOnlyMany** - the volume can be mounted as read-only by many nodes.
- **ReadWriteMany** - the volume can be mounted as read-write by many nodes.
- **ReadWriteOncePod** - the volume can be mounted as read-write by a single Pod. Use ReadWriteOncePod access mode if you want to ensure that only one pod across whole cluster can read that PVC or write to it.


## Example

Let’s create one **pvnfs10gb.yaml** with the following content

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pvnfs10gb
  labels:
    purpose: demo
spec:
  capacity:
    storage: 10Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteMany
  # Deleting PVC will trigger the reclaim policy.
  persistentVolumeReclaimPolicy: Recycle
  mountOptions:
    - nfsvers=4.1
  nfs:
    path: /data/nfs/k8sdata
    server: nfs-server
```

Save and close the file. Send it to the cluster.

```bash
kubectl apply -f pvnfs10gb.yaml
```

Check the list of persistent volumes. Pay attention to the **STATUS** and **CLAIM** fields.

```bash
kubectl get pv
```

Describe the one that we created

```bash
kubectl describe pv pvnfs10gb
```

In order to use this persistent volume, we must claim it first. Create a pvc10gb.yaml manifest with the following content

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc10gb
# Set of criteria used to bind PVC to PV from available PVs
spec:
  accessModes:
    - ReadWriteMany
  volumeMode: Filesystem
  resources:
    requests:
      storage: 10Gi
  selector:
    matchLabels:
      purpose: demo
```

Save and close the file. Send it to the cluster.

```bash
kubectl apply -f pvc10gb.yaml
```

Get again the list of persistent volumes.

```bash
kubectl get pv
```

Check the list of persistent volumes. Pay attention to the **STATUS** and **CLAIM** fields. Ask for the list of persistent volume claims.

```bash
kubectl get pvc
```

And then describe it. We can see that the Used By field is empty.

```bash
kubectl describe pvc pvc10gb
```

preparing and launching a deployment pv-deployment.yaml with the following content.

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
        - mountPath: /data
          name: volume-by-claim
      volumes:
      - name: volume-by-claim
        # Make volume over PVC with claimName pvc10gb
        persistentVolumeClaim:
          claimName: pvc10gb
---
apiVersion: v1
kind: Service
metadata:
  name: svc-vol
spec:
  type: NodePort
  ports:
  - port: 80
    nodePort: 30001
    protocol: TCP
  selector:
    app: notes
```

Save and close the file. Send it to the cluster.

```bash
kubectl apply -f part1/pv-deployment.yaml
```

Monitor the pods with

```bash
kubectl get pods -o wide -w
```

Once all up and running, press Ctrl+C to stop. Then, check if the claim will be marked as used now.

```bash
kubectl describe pvc pvc10gb
```

It should state that it is being used by all three pods that were created by the deployment. Describe one of them to see how it appears.

```bash
kubectl describe pod notes-deploy-<specific-id>
```

Explore both the **Volumes** and **Mounts** sections. Now, open a browser tab, and navigate to ```http://<cluster-node-ip>:30001/index.php```. Let’s see what will happen when we delete both the deployment and the claim and then recreate them again.
  
```bash
kubectl delete -f pv-deployment.yaml
```

And then the claim

```bash
kubectl delete -f pvc10gb.yaml
```

Now, create them again. First the claim

```bash
kubectl apply -f pvc10gb.yaml
```

And then the deployment

```bash
kubectl apply -f pv-deployment.yaml
```

Once all pods are running, open a browser tab, and navigate to ```http://<cluster-node-ip>:30001/index.php```. There be no notes because the Persistent Volume (pvnfs10gb) with persistentVolumeReclaimPolicy is set to Recycle. Thus, when we deleted the persistent volume claim, the persistent volume was recycled (wiped).


Clean Up

```bash
kubectl delete -f part1/pv-deployment.yaml
kubectl delete -f part1/pvc10gb.yaml
kubectl delete -f part1/pvnfs10gb.yaml
```















## Part 2

### Pod with no environment variables

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-no-env
  labels:
    app: environ
spec:
  containers:
  - image: shekeriev/k8s-environ
    name: cont-no-env
    
 ---
 
apiVersion: v1
kind: Service
metadata:
  name: svc-environ
spec:
  type: NodePort
  ports:
  - port: 80
    nodePort: 30001
    protocol: TCP
  selector:
    app: environ

```

### Pod with environment variables

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

### ConfigMap

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

Consuming ConfigMap

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

### Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mysecrets
  namespace: default
# Secrets (list of key-value pairs)
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


### StatefulSet

StatefulSet is the workload API object used to manage stateful applications. Manages the deployment and scaling of a set of Pods, and provides guarantees about the ordering and uniqueness of these Pods. Like a Deployment, a StatefulSet manages Pods that are based on an identical container spec.

![image](https://user-images.githubusercontent.com/34960418/145412355-67d48f68-8078-444e-b5fc-462ae3ec5826.png)

Storage for a Pod must be provisioned **upfront** either automatically or by an administrator

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pvssa
  labels:
    purpose: ssdemo
spec:
  capacity:
    storage: 1Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Recycle
  mountOptions:
    - nfsvers=4.1
  nfs:
    path: /data/nfs/k8spva
    server: nfs-server
    
    ---
    
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pvssb
  labels:
    purpose: ssdemo
spec:
  capacity:
    storage: 1Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Recycle
  mountOptions:
    - nfsvers=4.1
  nfs:
    path: /data/nfs/k8spvb
    server: nfs-server
    
  ---
  
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pvssc
  labels:
    purpose: ssdemo
spec:
  capacity:
    storage: 1Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Recycle
  mountOptions:
    - nfsvers=4.1
  nfs:
    path: /data/nfs/k8spvc
    server: nfs-server
```

**Headless service** is required for the network identity of the pods

```yaml
apiVersion: v1
kind: Service
metadata:
  name: facts
spec:
  selector:
    app: facts
  # This make service headless. Allow pods to comunicate through their names.
  clusterIP: None
  ports:
  - port: 5000
    protocol: TCP
```

StatefulSet is managing Volume Claims

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: facts
spec:
  selector:
    matchLabels:
      app: facts
  serviceName: facts
  replicas: 2
  # POD template
  template:
    metadata:
      labels:
        app: facts
    spec:
      terminationGracePeriodSeconds: 10
      containers:
      - name: main
        image: shekeriev/k8s-facts
        ports:
        - name: app
          containerPort: 5000
        volumeMounts:
        - name: facts-data
          mountPath: /data
  # VolumeClaim template
  volumeClaimTemplates:
  - metadata:
      name: facts-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 1Gi
```

Public (NodePort) Service

Create a standard or public (in this case NodePort) service that will expose the pods.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: factsnp
spec:
  selector:
    app: facts
  type: NodePort
  ports:
  - port: 5000
    nodePort: 30001
    protocol: TCP
```
