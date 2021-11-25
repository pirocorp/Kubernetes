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
    # the source from repository will be downloaded and will be mountet to mountPath specified in volumeMounts
    gitRepo:
      repository: "https://github.com/shekeriev/k8s-notes.git"
      revision: "main"
      directory: .
  - name: data-volume
    emptyDir: {}
```
