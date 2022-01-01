# Configuration maps and secrets

### Create a *ConfigMap* resource *hwcm* that:

  1. has two key-value pairs (**k8sver** and **k8sos**) initialized as literals that hold your **Kubernetes version** and the name of the **OS** where **Kubernetes** is running
  2. has two more key-value pairs (**main.conf** and **port.conf**) initialized from files. The first one (**main.conf**) should contain:
  ```
  # main.conf
  name=homework
  path=/tmp
  certs=/secret
  ```
  3. And the second one (**port.conf**):
  ```
  8080
  ```
  
### Create a **Secret** resource **hwsec** that:
  1.	Has two data entries – **main.key** and **main.crt** created from files
  2.	The content for the above two generate by using the **openssl** utility. For example:
  ```bash
  openssl genrsa -out main.key 4096
  openssl req -new -x509 -key main.key -out main.crt -days 365 -subj /CN=www.hw.lab
  ```

### Mount the above resources to a pod created from the *shekeriev/k8s-environ* image (used during the practice) by 
  1.	**k8sver** and **k8sos** should be mounted as environment variables with prefix **HW_**
  2.	**main.conf** should be mounted as a volume to the **/config** folder inside the container
  3.	**port.conf** should be mounted as an environment variable **HW_PORT**
  4.	**main.key** and **main.crt** should be mounted as a volume to the **/secret** folder inside the container


## Solution: 

Before we create the configuration map, we must prepare the two files – **main.conf** and **port.conf**.


Create the map with

```bash
kubectl create configmap hwcm --from-literal=k8sver=1.22.3 --from-literal=k8sos="Debian GNU/Linux 10 (buster)" --from-file=./main.conf --from-file=./port.conf
```

Prepare the key and the certificate first

```bash
openssl genrsa -out main.key 4096
openssl req -new -x509 -key main.key -out main.crt -days 365 -subj /CN=www.hw.lab
```

Create the secret with

```bash
kubectl create secret generic hwsec --from-file=main.key=./main.key  --from-file=main.crt=./main.crt
```

Prepare pod-svc.yaml

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-hw
  labels:
    app: environ
spec:
  containers:
  - image: shekeriev/k8s-environ
    name: cont-w-env
    volumeMounts:
    - name: main-config-volume
      mountPath: /config
    - name: secret-volume
      mountPath: /secret
    env:
    - name: HW_k8sver 
      valueFrom:
        configMapKeyRef:
          name: hwcm
          key: k8sver
    - name: HW_k8sos 
      valueFrom:
        configMapKeyRef:
          name: hwcm
          key: k8sos
    - name: HW_PORT 
      valueFrom:
        configMapKeyRef:
          name: hwcm
          key: port.conf
  volumes:
    - name: main-config-volume
      configMap:
        name: hwcm
        items:
        - key: main.conf
          path: ./main.conf
    - name: secret-volume
      secret:
        secretName: hwsec
---
apiVersion: v1
kind: Service
metadata:
  name: svc-hw
spec:
  type: NodePort
  ports:
  - port: 80
    nodePort: 30001
```


# Create and run a set of manifest files to spin the following application

![image](https://user-images.githubusercontent.com/34960418/147851307-799f5bb1-d649-4684-83d4-f15100bce20e.png)

-	**Service FE** should be of type **NodePort**.
-	**Pod FE** should use **shekeriev/k8s-facts-fe** image and should be initialized with two environment variables – **FACTS_SERVER** equal to the **name** of the **Service BE** and **FACTS_PORT** equal to the **port** of **Service BE**.
-	**Pod FE** listens on port **5000/tcp**.
-	**Service BE** should be of type **ClusterIP** (please note, that this is not the headless service but the “public” one).
-	**Pod BE** should use **shekeriev/k8s-facts** image and expects a volume to be mounted at **/data** folder.
-	**Pod BE** listens on port **5000/tcp**.
-	For the **PVs** and **PVCs** use **NFS** and storage capacity of **2Gi**.
-	Both the **Deployment** and the **StatefulSet** should spin three replicas.

## Solution

Assuming that there is a NFS server available and reachable by the name ```nfs-server``` from all the nodes. Assuming that there are three exported and writable folders - ```/data/nfs/k8spv{a,b,c}```.

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pvssa
  labels:
    purpose: ssdemo
spec:
  capacity:
    storage: 2Gi
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
    storage: 2Gi
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
    storage: 2Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Recycle
  mountOptions:
    - nfsvers=4.1
  nfs:
    path: /data/nfs/k8spvc
    server: nfs-server    
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: pod-be
spec:
  selector:
    matchLabels:
      app: facts
  serviceName: facts 
  replicas: 3
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
          storage: 2Gi          
---
apiVersion: v1
kind: Service
metadata:
  name: facts 
spec:
  selector:
    app: facts  
  clusterIP: None
  ports:
  - port: 5000
    protocol: TCP    
---
apiVersion: v1
kind: Service
metadata:
  name: service-be 
spec:
  type: ClusterIP
  selector:
    app: facts
  ports:
  - port: 5000
    targetPort: 5000
    protocol: TCP    
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: service-be-map
data:
  FACTS_SERVER: "service-be"
  FACTS_PORT: "5000"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fe-deploy
spec:
  replicas: 3
  selector:
    matchLabels: 
      app: facts-fe
  template:
    metadata:
      labels:
        app: facts-fe
    spec:
      containers:
      - name: facts-fe
        image: shekeriev/k8s-facts-fe 
        ports:
        - containerPort: 5000
        envFrom:
        - configMapRef:
            name: service-be-map
---

apiVersion: v1
kind: Service
metadata:
  name: service-fe 
spec:
  type: NodePort
  selector:
    app: facts-fe  
  ports:
  - port: 5000
    nodePort: 30001
    protocol: TCP
```
