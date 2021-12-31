# Create and register two Kubernetes uses – Ivan (ivan) and Mariana (mariana) who are part of the Gurus (gurus) group

Create the two users

```bash
useradd -m -c 'Ivan' -s /bin/bash ivan 
useradd -m -c 'Mariana' -s /bin/bash mariana
```

Prepare the subfolders for both users

```bash
mkdir -p /home/{ivan,mariana}/{.certs,.kube}
```

Create the private keys for both users

```bash
openssl genrsa -out /home/ivan/.certs/ivan.key 2048
openssl genrsa -out /home/mariana/.certs/mariana.key 2048
```

Create a certificate signing request (CSR) for every user

```bash
openssl req -new -key /home/ivan/.certs/ivan.key -out /home/ivan/.certs/ivan.csr -subj "/CN=ivan/O=gurus"
openssl req -new -key /home/mariana/.certs/mariana.key -out /home/mariana/.certs/mariana.csr -subj "/CN=mariana/O=gurus"
```

Sign both CSRs with the Kubernetes CA certificate

```bash
openssl x509 -req -in /home/ivan/.certs/ivan.csr -CA /etc/kubernetes/pki/ca.crt -CAkey /etc/kubernetes/pki/ca.key -CAcreateserial -out /home/ivan/.certs/ivan.crt -days 365
openssl x509 -req -in /home/mariana/.certs/mariana.csr -CA /etc/kubernetes/pki/ca.crt -CAkey /etc/kubernetes/pki/ca.key -CAcreateserial -out /home/mariana/.certs/mariana.crt -days 365
```

Create the credentials for the two users

```bash
kubectl config set-credentials ivan --client-certificate=/home/ivan/.certs/ivan.crt --client-key=/home/ivan/.certs/ivan.key
kubectl config set-credentials mariana --client-certificate=/home/mariana/.certs/mariana.crt --client-key=/home/mariana/.certs/mariana.key
```

Create the contexts for the two users

```bash
kubectl config set-context ivan-context --cluster=kubernetes --user=ivan
kubectl config set-context mariana-context --cluster=kubernetes --user=mariana
```

Create configuration file for **ivan** at ```/home/ivan/.kube/config``` with the following content:

```yaml
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUM1ekNDQWMrZ0F3SUJBZ0lCQURBTkJna3Foa2lHOXcwQkFRc0ZBREFWTVJNd0VRWURWUVFERXdwcmRXSmwKY201bGRHVnpNQjRYRFRJeE1URXlNREV4TWpReU5Gb1hEVE14TVRFeE9ERXhNalF5TkZvd0ZURVRNQkVHQTFVRQpBeE1LYTNWaVpYSnVaWFJsY3pDQ0FTSXdEUVlKS29aSWh2Y05BUUVCQlFBRGdnRVBBRENDQVFvQ2dnRUJBTUdpClJKMHY3NEg5R3RRR3M2UVQ2Qzc3R1d0QXdXRmcxV0pGbFFaUU9rTmdzbU5LVzJNbHdOL01ydGZTYXlEU2ZJc0sKTjlzRjRGN3ZmYUFNQThhdVYxSTc0QVZZQTZ6aUxqc1NpNGhjeGhSUHJrSlRRSWVUVk1MUzVWaml5d0VnRTlCVwozOElmYVo3cjZBUXMwZ1Jlb3FXWGpkUDZzZFAyckZ2b1lzVE5oZFVodmVtenBEQXJ2ekpMRWtWSEhPc09Fa01OClo4WkZ5SFU2amM1YkUzRkVxaXpZdENVdHpxaENBYkhsQVVnMmN0cTJXbjl6ZGdGUUNKQXJPOWpJWVEwZFRjUngKYUV2UmlMSUZsTy91RHRuUkUydnEwdHF3cDduMzg0VlBmNXdQVndEY1ZGN0VZYk9BZUJJOHJsMmtsVGhlQm5nKwovT1NTbUhndjVhOGR5MkdvSXlNQ0F3RUFBYU5DTUVBd0RnWURWUjBQQVFIL0JBUURBZ0trTUE4R0ExVWRFd0VCCi93UUZNQU1CQWY4d0hRWURWUjBPQkJZRUZNSE5tLzNYUzJSZnZ4MkwxMGhsWnpyVHpjTUFNQTBHQ1NxR1NJYjMKRFFFQkN3VUFBNElCQVFBODJJNHBiR2VlUzNMNkFZRWlDanU3WnRTWERaOGJIMDFIZ20xWDBVQmNuOTU5aXZXYwphSHQyZVc4YzJWcFVGbVYzcFoxMXY1cWljVmk5NWlhUzFHT0VHdENpVUJHQ2FyWDZmdWdEWUdkQzlITmF6aEdiCndESkFMRU9Td0JLajZ1dTZxU2NlL0NlSmZhQjBsMzM2UjZaYU10eUNBU3RPSkYzMnBRVmxDZ21Xd3orQ0IvZmkKK0VySzUxamNtMGhVeVU3TVdhTlNEbHFHWDAyVzkxNjZuMUkvc1dxeGRpV0haMTBNZU1oMUJMWndDUFE5Mjc3dApFWCs5dkR5M0I5RnNzVVUzTHhCeldWd0ppTURNUGRYSklHUE9pYmlPUDZWcktrSHgrbzArSWk0OFBqTUVyME11Ckd5ZldUTG90SHdSWlZRMVVGTXhNY1RFK0Q5b21QMmxCc05FLwotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tCg==
    server: https://192.168.0.71:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: ivan
  name: ivan-context
current-context: ivan-context
kind: Config
preferences: {}
users:
- name: ivan
  user:
    client-certificate: /home/ivan/.certs/ivan.crt
    client-key: /home/ivan/.certs/ivan.key
```

Create configuration file for **mariana** at ```/home/mariana/.kube/config``` with the following content:

```yaml
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUM1ekNDQWMrZ0F3SUJBZ0lCQURBTkJna3Foa2lHOXcwQkFRc0ZBREFWTVJNd0VRWURWUVFERXdwcmRXSmwKY201bGRHVnpNQjRYRFRJeE1URXlNREV4TWpReU5Gb1hEVE14TVRFeE9ERXhNalF5TkZvd0ZURVRNQkVHQTFVRQpBeE1LYTNWaVpYSnVaWFJsY3pDQ0FTSXdEUVlKS29aSWh2Y05BUUVCQlFBRGdnRVBBRENDQVFvQ2dnRUJBTUdpClJKMHY3NEg5R3RRR3M2UVQ2Qzc3R1d0QXdXRmcxV0pGbFFaUU9rTmdzbU5LVzJNbHdOL01ydGZTYXlEU2ZJc0sKTjlzRjRGN3ZmYUFNQThhdVYxSTc0QVZZQTZ6aUxqc1NpNGhjeGhSUHJrSlRRSWVUVk1MUzVWaml5d0VnRTlCVwozOElmYVo3cjZBUXMwZ1Jlb3FXWGpkUDZzZFAyckZ2b1lzVE5oZFVodmVtenBEQXJ2ekpMRWtWSEhPc09Fa01OClo4WkZ5SFU2amM1YkUzRkVxaXpZdENVdHpxaENBYkhsQVVnMmN0cTJXbjl6ZGdGUUNKQXJPOWpJWVEwZFRjUngKYUV2UmlMSUZsTy91RHRuUkUydnEwdHF3cDduMzg0VlBmNXdQVndEY1ZGN0VZYk9BZUJJOHJsMmtsVGhlQm5nKwovT1NTbUhndjVhOGR5MkdvSXlNQ0F3RUFBYU5DTUVBd0RnWURWUjBQQVFIL0JBUURBZ0trTUE4R0ExVWRFd0VCCi93UUZNQU1CQWY4d0hRWURWUjBPQkJZRUZNSE5tLzNYUzJSZnZ4MkwxMGhsWnpyVHpjTUFNQTBHQ1NxR1NJYjMKRFFFQkN3VUFBNElCQVFBODJJNHBiR2VlUzNMNkFZRWlDanU3WnRTWERaOGJIMDFIZ20xWDBVQmNuOTU5aXZXYwphSHQyZVc4YzJWcFVGbVYzcFoxMXY1cWljVmk5NWlhUzFHT0VHdENpVUJHQ2FyWDZmdWdEWUdkQzlITmF6aEdiCndESkFMRU9Td0JLajZ1dTZxU2NlL0NlSmZhQjBsMzM2UjZaYU10eUNBU3RPSkYzMnBRVmxDZ21Xd3orQ0IvZmkKK0VySzUxamNtMGhVeVU3TVdhTlNEbHFHWDAyVzkxNjZuMUkvc1dxeGRpV0haMTBNZU1oMUJMWndDUFE5Mjc3dApFWCs5dkR5M0I5RnNzVVUzTHhCeldWd0ppTURNUGRYSklHUE9pYmlPUDZWcktrSHgrbzArSWk0OFBqTUVyME11Ckd5ZldUTG90SHdSWlZRMVVGTXhNY1RFK0Q5b21QMmxCc05FLwotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tCg==
    server: https://192.168.0.71:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: mariana
  name: mariana-context
current-context: mariana-context
kind: Config
preferences: {}
users:
- name: mariana
  user:
    client-certificate: /home/mariana/.certs/mariana.crt
    client-key: /home/mariana/.certs/mariana.key
```

Now, change the ownership of the respective folders and files

```bash
chown -R ivan: /home/ivan
chown -R mariana: /home/mariana
```

# Create a LimitRange for the namespace to set defaults, minimum and maximum both for CPU and memory

Create a **limits.yaml** file with the following (sample) content

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: projectx-limits
spec:
  limits:
  - max:
      cpu: 500m
      memory: 500Mi
    min:
      cpu: 50m
      memory: 50Mi
    default:
      cpu: 100m
      memory: 100Mi
    type: Container
```

Deploy it to the cluster with

```bash
kubectl apply -f limits.yaml -n projectx
```

And check its status

```bash
kubectl describe limitrange -n projectx
```

# Create a **ResourceQuota** for the namespace to set **requests** and **limits** both for **CPU** and **memory**. In addition, add limits for **pods**, **services**, **deployments**, and **replicasets**. Use values that you consider suitable.

Create a **quotas.yaml** file with the following (sample) content

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: projectx-quotas
spec:
  hard:
    requests.cpu: 1
    requests.memory: 1Gi
    limits.cpu: 2
    limits.memory: 2Gi
    pods: 10
    services: 5
    count/deployments.apps: 2
    count/replicasets.apps: 2
```

Deploy the manifest to the cluster

```bash
kubectl apply -f quotas.yaml -n projectx
```

And check its status

```bash
kubectl describe quota -n projectx
```

# Create a custom role (**devguru**) which will allow the one that has it to do anything with any of the following resources **pods**, **services**, **deployments**, and **replicasets**. Grant the role to **ivan** and **mariana** (or to the group they belong to) for the namespace created earlier.

We can create the required role with

```bash
kubectl create role role-hw -n projectx --verb="*" --resource=pods,services,deployments.apps,replicasets.apps
```

Then check what we have created

```bash
kubectl describe role role-hw -n projectx
```

Now, we can bind the role either to each user individually (use either this one)

```bash
kubectl create rolebinding roleb-hw-ivan -n projectx --role role-hw --user ivan
kubectl create rolebinding roleb-hw-mariana -n projectx --role role-hw --user mariana
```

Or create a role binding to the group (or this one)

```bash
kubectl create rolebinding roleb-hw-gurus -n projectx --role role-hw --group gurus
```

And then check what we can do as ivan

```bash
kubectl auth can-i --list --namespace projectx --as ivan
```

Or

```bash
kubectl auth can-i --list --namespace projectx --as ivan --as-group gurus
```

Alternative Solution

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: devguru
  namespace: projectx
rules:
- apiGroups:
  - ""
  - extensions
  - apps
  resources:
  - pods
  - services
  - deployments
  - replicasets
  verbs:
  - get
  - list
  - watch
  - create
  - update
  - patch
  - delete  
---

apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: devguru
  namespace: projectx
subjects:
- kind: Group
  name: gurus
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: devguru
  apiGroup: rbac.authorization.k8s.io
```

# Using one of the two users, deploy the **producer-consumer** application (use the attached files – you may need to modify them a bit). Deploy one additional pod that will act as a (curl) **client**.

producer-deployment.yaml 

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: producer-deploy
  namespace: projectx
spec:
  replicas: 3
  selector:
    matchLabels: 
      app: fun-facts
      role: producer
  minReadySeconds: 15
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  template:
    metadata:
      labels:
        app: fun-facts
        role: producer
    spec:
      containers:
      - name: prod-container
        image: shekeriev/k8s-producer:latest
        ports:
        - containerPort: 5000
```

producer-svc.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: producer
  namespace: projectx
  labels:
    app: fun-facts
    role: producer
spec:
  type: ClusterIP
  ports:
  - port: 5000
    protocol: TCP
  selector:
    app: fun-facts
    role: producer
```

consumer-deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: consumer-deploy
  namespace: projectx
spec:
  replicas: 3
  selector:
    matchLabels: 
      app: fun-facts
      role: consumer
  minReadySeconds: 15
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  template:
    metadata:
      labels:
        app: fun-facts
        role: consumer
    spec:
      containers:
      - name: cons-container
        image: shekeriev/k8s-consumer:latest
        ports:
        - containerPort: 5000
```

consumer-svc.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: consumer
  namespace: projectx
  labels:
    app: fun-facts
    role: consumer
spec:
  type: NodePort
  ports:
  - port: 5000
    nodePort: 30001
    protocol: TCP
  selector:
    app: fun-facts
    role: consumer
```

Switch the session as ivan

```bash
su ivan
```

Then deploy the provided manifests

```bash
kubectl apply -n projectx -f producer-deployment.yaml 
kubectl apply -n projectx -f producer-svc.yaml
kubectl apply -n projectx -f consumer-deployment.yaml
kubectl apply -n projectx -f consumer-svc.yaml
```

Then, deploy a simple pod to act as a client for testing purposes

```bash
kubectl run client -n projectx --image alpine -- sleep 1d
```

Finally, check how the deployment went

```bash
kubectl get pods,svc,rs,deployments -n projectx
```

# Create **NetworkPolicy** resources in order to allow communication to the **producer** only from the **consumer** and allow communication to the **consumer** only from the **client**.

As our two users (**ivan** and **mariana**) does not have rights to create network policies, next part we must execute as the **admin** user.

First, let’s connect to the client pod

```bash
kubectl exec -n projectx -it client -- sh
```

And update and install the curl package

```bash
apk update
apk add curl
```

Then, try to talk to the consumer and then the producer services

```bash
curl http://consumer:5000
curl http://producer:5000
```

Now, close the session

```bash
exit
```

And then create the first network policy manifest **np-prod.yaml** with the following content

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: np-prod
spec:
  podSelector:
    matchLabels:
      role: producer
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: consumer
```

Deploy it with

```bash
kubectl apply -n projectx -f np-prod.yaml
```

Then create the second network policy manifest **np-cons.yaml** with the following content

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: np-cons
spec:
  podSelector:
    matchLabels:
      role: consumer
  ingress:
  - from:
    - podSelector:
        matchLabels:
          run: client
```

And deploy it with 

```bash
kubectl apply -n projectx -f np-cons.yaml
```

Finally, connect to the client pod

```bash
kubectl exec -n projectx -it client – sh
```

And test again

```bash
curl --connect-timeout 5 http://consumer:5000
curl --connect-timeout 5 http://producer:5000
```
