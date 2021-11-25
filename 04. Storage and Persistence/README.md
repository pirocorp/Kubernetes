# Manifest files explanations (YAML)

## Part 1

### Ephemeral Volumes

We should keep in mind that ephemeral volume will disappear together with the Pod once terminated.

#### emptydir-pod.yaml 

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
    # volumes are used with volumeMounts construct, but it is part of the container description.
    volumeMounts:
    - mountPath: /data
      name: data-volume
  # In volumes section volumes are defined
  volumes:
  - name: data-volume
    # volume type
    emptyDir: {}
```
