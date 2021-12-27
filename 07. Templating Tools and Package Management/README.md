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

![image](https://user-images.githubusercontent.com/34960418/147357972-a133c2f2-4542-4d50-be8a-d6a2f9c9f2f1.png)

#### Base Variant Kustomization

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

Base(original) Resources

Config Map (configMap.yaml)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: the-map
data:
  altGreeting: "Good Morning!"
  enableRisky: "false"
```

Deployment (deployment.yaml)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: the-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      deployment: hello
  template:
    metadata:
      labels:
        deployment: hello
    spec:
      containers:
      - name: the-container
        image: monopole/hello:1
        command: ["/hello",
                  "--port=8080",
                  "--enableRiskyFeature=$(ENABLE_RISKY)"]
        ports:
        - containerPort: 8080
        env:
        - name: ALT_GREETING
          valueFrom:
            configMapKeyRef:
              name: the-map
              key: altGreeting
        - name: ENABLE_RISKY
          valueFrom:
            configMapKeyRef:
              name: the-map
              key: enableRisky
```

Service (service.yaml)

```yaml
kind: Service
apiVersion: v1
metadata:
  name: the-service
spec:
  selector:
    deployment: hello
  type: LoadBalancer
  ports:
  - protocol: TCP
    port: 8666
    targetPort: 8080
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

#### Staging overlay

Kustomization

```yaml
namePrefix: staging-
commonLabels:
  variant: staging
  org: acmeCorporation
commonAnnotations:
  note: Hello, I am staging!
# Location of base variant
resources:
- ../../base
# Patch files
patchesStrategicMerge:
- map.yaml
```

ConfigMap patch (map.yaml)

```yaml
apiVersion: v1
# Kind and metadata describe patched resources.
kind: ConfigMap
metadata:
  name: the-map
data:
  altGreeting: "Have a pineapple!"
  enableRisky: "true"
```

Build staging variant

```bash
kustomize build $OVERLAYS/staging
```

Apply staging variant

```bash
kustomize build $OVERLAYS/staging | kubectl apply -f -
```

or

```bash
kubectl apply -k $OVERLAYS/staging
```

Delete staging variant

```bash
kustomize build $OVERLAYS/staging | kubectl delete -f -
```

or

```bash
kubectl delete -k $OVERLAYS/staging
```

#### Production overlay

Kustomization

```yaml
namePrefix: production-
commonLabels:
  variant: production
  org: acmeCorporation
commonAnnotations:
  note: Hello, I am production!
resources:
- ../../base
patchesStrategicMerge:
- deployment.yaml
```

Deployment (deployment.yaml)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: the-deployment
spec:
  replicas: 5
```

Build production variant

```bash
kustomize build $OVERLAYS/production
```

Apply production variant

```bash
kubectl apply -k $OVERLAYS/production
```

Delete production variant

```bash
kubectl delete -k $OVERLAYS/production
```

## Part 2

### Chart From Existing Manifest

Original manifest

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

#### Create Chart.yaml file

```yaml
apiVersion: v2
name: appchart
description: A simple Helm chart for Kubernetes based on an existing application

# Chart type. A chart can be either an 'application' or a 'library' chart
type: application

# Version of the chart
version: 0.1.0

# Version of the application. In our case this can be a custom version as it is our application
appVersion: "1.0.0"
```
