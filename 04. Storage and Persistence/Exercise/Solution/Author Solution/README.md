# Configuration maps and secrets

## Create a *ConfigMap* resource *hwcm* that:

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
  
##	Create a **Secret** resource **hwsec** that:
  1.	Has two data entries – **main.key** and **main.crt** created from files
  2.	The content for the above two generate by using the **openssl** utility. For example:
  ```bash
  openssl genrsa -out main.key 4096
  openssl req -new -x509 -key main.key -out main.crt -days 365 -subj /CN=www.hw.lab
  ```

## 	Mount the above resources to a pod created from the *shekeriev/k8s-environ* image (used during the practice) by 
  1.	**k8sver** and **k8sos** should be mounted as environment variables with prefix **HW_**
  2.	**main.conf** should be mounted as a volume to the **/config** folder inside the container
  3.	**port.conf** should be mounted as an environment variable **HW_PORT**
  4.	**main.key** and **main.crt** should be mounted as a volume to the **/secret** folder inside the container


Solution: 

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
