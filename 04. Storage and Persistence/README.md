# Manifest files explanations (YAML)

## Part 1

### Ephemeral Volumes

We should keep in mind that ephemeral volume will disappear together with the Pod once terminated.

#### Emptydir

![image](https://user-images.githubusercontent.com/34960418/143465833-9840c0d1-ecb4-4dbd-ad3f-5e713ebd9994.png)
![image](https://user-images.githubusercontent.com/34960418/143465996-27bdadde-f83c-4c6d-af43-7ee57dbca3f7.png)


```yaml
# Pod definition
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
    # volumes are used with volumeMounts construct, but it is part of the container description.
    volumeMounts:
    - mountPath: /data
      name: data-volume
  # In volumes section volumes are defined
  volumes:
  - name: data-volume
    # volume type
    emptyDir: {}
    
    ---

# Service definition
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

#### GitRepo

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
  - name: git-volume
    # volume type
    # the source from repository will be downloaded and will be mountet to mountPath specified in volumeMounts
    gitRepo:
      repository: "https://github.com/shekeriev/k8s-notes.git"
      revision: "main"
      directory: .
  - name: data-volume
    emptyDir: {}
```

### Persistent Volumes

#### HostPath

While working, it binds us (or our Pod) to the host’s filesystem, so we should use it with care. In addition, it may expose security vulnerabilities, so we should use it in read only mode until we know what we are doing. (Data in this path on different nodes will be different.)

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
          # path from node (this path must exist on every worker node) where container is started will be mount to mountPath
          path: /tmp/data
          type: Directory
```

#### NFS

One of the most useful types of volumes in Kubernetes is nfs. NFS stands for Network File System – it's a shared filesystem that can be accessed over the network. The NFS must already exist – Kubernetes doesn't run the NFS, pods in just access it.

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
          # On which path for containers(pods) exposed path will be mounted
        - mountPath: /data
          name: nfs-data
      volumes:
      - name: nfs-data
        nfs:
          server: nfs-server
          # Exposed path by NFS Server
          path: /data/nfs/k8sdata
```

### Persistent Volumes and Claims

We can define Persistent Volumes and then let them to be claimed via Persistent Volume Claims

#### PersistentVolume (PV)

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

#### PersistentVolumeClaim (PVC)

PersistentVolumeClaim (PVC) is a request for storage by a user.

Binding is the process of matching and attaching a PVC to PV. This is done on a set of criteria. It is ono-to-one mapping

![image](https://user-images.githubusercontent.com/34960418/145032191-76621524-d189-436c-81b4-f75f1cc40adf.png)

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

#### Consuming PVC

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
```
