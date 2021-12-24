# Manifest files explanations (YAML)

## Part 1

### Using ```sed``` with parameterized manifests

#### Example for converting standart manifest into parameterized.

##### Standart Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: appa
spec:
  replicas: 1
  selector:
    matchLabels: 
      app: appa
  template:
    metadata:
      labels:
        app: appa
    spec:
      containers:
      - name: main
        image: shekeriev/k8s-environ:latest
        env:
        - name: APPROACH
          value: "STATIC"
        - name: FOCUSON
          value: "APPROACH"
---
apiVersion: v1
kind: Service
metadata:
  name: appa
spec:
  type: NodePort
  ports:
  - port: 80
    nodePort: 30001
    protocol: TCP
  selector:
    app: appa
```

##### Parameterized manifest

- The replicas value is parameterized
- The image and tag are parameterized
- The ```APPROACH``` environment variable is parameterized
- The NodePort (the port on which service is listening) is parameterized

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: appa
spec:
  # replicas value is parameterized
  replicas: %replicas%
  selector:
    matchLabels: 
      app: appa
  template:
    metadata:
      labels:
        app: appa
    spec:
      containers:
      - name: main
        # The image and tag are parameterized
        image: %image%:%tag%
        env:
        # The APPROACH environment variable is parameterized
        - name: APPROACH          
          value: "%approach%"
        - name: FOCUSON
          value: "APPROACH"
---
apiVersion: v1
kind: Service
metadata:
  name: appa
spec:
  type: NodePort
  ports:
  - port: 80
    # The NodePort is parameterized
    nodePort: %nodeport%
    protocol: TCP
  selector:
    app: appa
```

##### Using ```sed``` with parameterized manifests

To send it to file

```bash
sed 's/%replicas%/3/ ; s@%image%@shekeriev/k8s-environ@ ; s/%tag%/latest/ ; s/%approach%/MANUAL/ ; s/%nodeport%/30001/' 2-appa.yaml > 3-appa.yaml
```

To send it to cluster

```bash
sed 's/%replicas%/3/ ; s@%image%@shekeriev/k8s-environ@ ; s/%tag%/latest/ ; s/%approach%/MANUAL/ ; s/%nodeport%/30001/' 2-appa.yaml | kubectl apply -f -
```

### Using Kustomize with manifests

![image](https://user-images.githubusercontent.com/34960418/147357001-439aa23e-7709-4b36-9b58-db3729cf6a9a.png)

#### Base Kustomization

Kustomization contains the base structure of our customizable application

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: arbitrary

# Example configuration for the webserver
# at https://github.com/monopole/hello
commonLabels:
  app: hello

resources:
- deployment.yaml
- service.yaml
- configMap.yaml
```

```$BASE``` must point to kustomization location

This will display base configuration in yaml on console

```bash
kustomize build $BASE
```

To send configuration to cluster

```bash
kustomize build $BASE | kubectl apply -f -
```

To delete it from cluster

```bash
kustomize build $BASE | kubectl delete -f -
```

#### Stageing overlay



create overlays subfolder

```bash
mkdir -p $OVERLAYS/staging
```
