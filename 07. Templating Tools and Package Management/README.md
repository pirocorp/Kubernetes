# Manual Approach (using [sed](https://www.gnu.org/software/sed/manual/sed.html))

![image](https://user-images.githubusercontent.com/34960418/148054368-3da900a8-c995-4555-857a-581fc09e112a.png)


Manifest with placeholders prepared for ```sed```.

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
        image: %image%:%tag%
        env:
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
    nodePort: %nodeport%
    protocol: TCP
  selector:
    app: appa
```

If send it as it is to the cluster, will see that it will result in error as it is not valid. But having it prepared in this way, can change or adjust it on the fly. Can execute this command to change, for example the number of replicas

```bash
sed s/%replicas%/3/ appa.yaml
```


This way, we set just one placeholder and saw the new version of the manifest. In order to set all of them, must either execute a sequence of commands (skip this)

```bash
sed s/%replicas%/3/ 2-appa.yaml | sed s@%image%@shekeriev/k8s-environ@ | sed s/%tag%/latest/ | sed s/%approach%/MANUAL/ | sed s/%nodeport%/30001/
```

Or execute an extended (this is one of the possible ways) command (use this)

```bash
sed 's/%replicas%/3/ ; s@%image%@shekeriev/k8s-environ@ ; s/%tag%/latest/ ; s/%approach%/MANUAL/ ; s/%nodeport%/30001/' appa.yaml
```

Here (in either of two versions), there two things to notice. 

First, we are replacing **the first occurrence** of a placeholder. Should we want to replace all, we must change the rules. For example, instead of this ```s/%nodeport%/30001/``` we should have this ```s/%nodeport%/30001/g```.

Second, notice how is changed the separator in one of the rules. Was done because have the same character as part of the value that is using.


We can either use the above command (either of its versions) to store the new version of the manifest (skip this for now)

```bash
sed 's/%replicas%/3/ ; s@%image%@shekeriev/k8s-environ@ ; s/%tag%/latest/ ; s/%approach%/MANUAL/ ; s/%nodeport%/30001/' appa.yaml > new-appa.yaml
```

Or just send it to the cluster (use this approach)

```bash
sed 's/%replicas%/3/ ; s@%image%@shekeriev/k8s-environ@ ; s/%tag%/latest/ ; s/%approach%/MANUAL/ ; s/%nodeport%/30001/' appa.yaml | kubectl apply -f -
```

Open a browser tab and navigate to the following address ```http://<control-plane-ip>:30001```. It is working. 

Now, let’s change the values of the placeholders with the following command.

```bash
sed 's/%replicas%/3/ ; s@%image%@shekeriev/k8s-environ@ ; s/%tag%/green/ ; s/%approach%/MANUAL/ ; s/%nodeport%/30001/' appa.yaml | kubectl apply -f -
```

Return to the browser tab and refresh. It is still working but looking a little bit different. So, this appears to be a valid approach of templating. There is one drawback though, we must submit values for all placeholders before we can use the manifest even if we want to change just one. 

Clean Up 

```bash
kubectl delete deployment appa
kubectl delete service appa
```


# [Kustomize](https://kustomize.io/)

- Native Kubernetes configuration management
- Template-free way to customize application configuration
- Simplifies the use of off-the-shelf applications
- Built into **kubectl** as **apply -k**

![image](https://user-images.githubusercontent.com/34960418/148058002-cf97fa5c-7c09-4989-a322-d1fa52c03dc2.png)



## Installing Kustomize

Under any **Linux** distribution, we can download it (the latest version) with

```bash
curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
```

For other versions or operating systems, should check [here](https://github.com/kubernetes-sigs/kustomize/releases).


Once downloaded, we must make it executable and move it to a folder that is part of our executable path. We can check if the process went as expected by executing.

```bash
kustomize version
```

## Using Kustomize

![image](https://user-images.githubusercontent.com/34960418/147357972-a133c2f2-4542-4d50-be8a-d6a2f9c9f2f1.png)


### Base Variant Kustomization

Kustomization contains the base structure of our customizable application. Let’s create the base customization file (**base/kustomization.yaml**).

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

### Staging overlay

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

### Production overlay

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

# [Helm](https://helm.sh/)

- It is a **package manager** for Kubernetes.
- Its packages are called **charts**.
- Charts help us define, install, and upgrade complex applications.
- They are easy to create, version, share, and publish.
- Charts are **organized in repositories**.
- Repositories may be accessed either **directly** or via a **hub**.
- One such hub is the **ArtifactHUB** (https://artifacthub.io/).

[Architecture](https://helm.sh/docs/topics/architecture/) - Two parts in one executable – client and library

![image](https://user-images.githubusercontent.com/34960418/148059263-b2c0a6f3-15d0-40af-9dd3-21001aad6a31.png)

[Charts](https://helm.sh/docs/topics/charts/)

- Collection of files that describe a related set of Kubernetes resources
- A single chart might be used to deploy something simple like a single pod with nginx, redis, etc.
- Or a set of different resources. For example, a full web app stack with HTTP servers, databases, caches, and so on
- They are created as a set of files with particular names and structure and then packaged into versioned archives
- Chart is organized as a collection of files inside of a directory
- The directory name is the name of the chart without versioning information

## Chart Directory Structure

![image](https://user-images.githubusercontent.com/34960418/148059973-46ab0129-cb43-466d-aef2-e568d874d9ff.png)

## Helm Installation

There are multiple ways to install Helm and perhaps the easiest one is by downloading the binary file. For any **64-bit** **Linux** distribution this can be done in the following way.

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

Latest version for other OSes can be downloaded from [here](https://github.com/helm/helm/releases/latest).
Other options and further instructions can be found [here](https://v3.helm.sh/docs/intro/install/).

Once, we have it installed, we can test if it is working by executing

```bash
helm version
```

## Register Repository

Before can start working with charts, must register one or more repositories.

The easiest way to find some, is to use the [ArtifactHub](https://artifacthub.io/).

Enter **nginx** in the search box and press Enter. A list of **nginx** related charts will appear. The first one should be a one provided by **Bitnami**. Click on it (or visit this URL: https://artifacthub.io/packages/helm/bitnami/nginx). There, in the beginning, are the instructions on how to add the repository.

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
```

Now, can list all locally registered repositories (it should be just this one)

```bash
helm repo list
```

To see where the information about the repository has been stored use

```bash
helm env
```

Let’s check what is behind the **HELM_REPOSITORY_CACHE** and **HELM_REPOSITORY_CONFIG** variables

The first one (**HELM_REPOSITORY_CACHE**) points to a folder, where information (the packages they provide) about the registered repositories will be stored including the charts that we use

The second one (**HELM_REPOSITORY_CONFIG**) points to a file which contains information about the registered repositories.


## Install Chart From Repository


Now, let’s install the chart that we wanted

```bash
helm install my-nginx-1 bitnami/nginx
```

We can notice two sets of information. The first one, right after our command, is a short information on what we deployed. The second one, contains detailed instructions on how to interact with what we deployed.


Let’s see what we have so far. Our only chart (in fact a **release**, as it is deployed in the cluster) is shown

```bash
helm list
```

Get detailed information about the release with. Have seen this information already

```bash
helm status my-nginx-1
```

Let’s use the **kubectl** to check what we have

```bash
kubectl get pods,svc
```

One pod and a service which appears to be of type **LoadBalancer** by default. Is this all? We can check with

```bash
helm get manifest my-nginx-1
```

There is one more object – a **ConfigMap**. It is used to store some additional configuration for nginx. Let’s try this command. Way more than we saw earlier. Which of the options (**all**, **hooks**, **manifest**, **notes** or **values**) to use, depends on what we are looking for.

```bash
helm get all my-nginx-1
```

Let’s try to access the default web page of the **nginx** instance. Ask for the service first.

```bash
kubectl get service my-nginx-1
```

Open a browser tab and navigate to ```http://<control-plane-ip:port> ```. Okay, it is the default page.


## Configure Chart From Repository

Go to the chart’s [page](https://artifacthub.io/packages/helm/bitnami/nginx). Explore the **Parameters** section. Go to the **custom NGINX application parameters** sub-section. And more specially in the **staticSiteConfigmap**. We can use it to pass a custom index page to the nginx chart. Create a second nginx release but this time with a custom index page.

First, create the configuration map with

```bash
kubectl create configmap my-nginx-2-index --from-literal=index.html='<h1>Hello from NGINX chart :)</h1>'
```

Check that it is there, and the content is as expected

```bash
kubectl get cm
kubectl get cm my-nginx-2-index -o yaml
```

Sure, everything is just fine. Now, install the chart but this time execute this

```bash
helm install my-nginx-2 bitnami/nginx --set staticSiteConfigmap=my-nginx-2-index --dry-run
```

This will do as stated – a dry run and show to us what will be the outcome. It seems that everything is fine, so let’s re-execute the command but without the **--dry-run** option.

```bash
helm install my-nginx-2 bitnami/nginx --set staticSiteConfigmap=my-nginx-2-index
```

Check what we have by now with

```bash
helm list
kubectl get pods,svc
```

Copy the service port and open a browser tab and navigate to ```http://<control-plane-ip:port>```. Our custom index page is there.

## Clean Up Chart

Remove the releases by executing

```bash
helm uninstall my-nginx-1 my-nginx-2
```

We can then check with

```bash
kubectl get pods,svc,cm
```

Most of the resources are gone, but configuration map is not. Because it was created separately and not as part of the chart. Remove it

```bash
kubectl delete cm my-nginx-2-index
```

## Create Chart from Manifest

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

#### Create helm chart

Chart directory structure

![image](https://user-images.githubusercontent.com/34960418/147486012-5b3d7e10-9ab5-489c-b687-df609f99c73e.png)


Chart.yaml

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

deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-deployment
spec:
  replicas: {{ .Values.replicasCount }}
  selector:
    matchLabels:
      app: {{ .Release.Name }}
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}
    spec:
      containers:
      - name: main
        image: shekeriev/k8s-environ:latest
        env:
        - name: APPROACH
          value: {{ .Values.approachVar }}
        - name: FOCUSON
          value: {{ .Values.focusOnVar }}
```

service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}-service
spec:
  type: NodePort
  ports:
  - port: 80
    nodePort: {{ .Values.nodePort }}
    protocol: TCP
  selector:
    app: {{ .Release.Name }}
```

values.yaml

```yaml
replicasCount: 1
approachVar: "Helm Charts! :)"
focusOnVar: "APPROACH"
nodePort: 30001
```

Install chart. In the above example chart name is appchart. Release name is user provided

```bash
helm install <release name> <chart name>
```

Install chart with custom parameters.

```bash
helm install testRelease appchart --set nodePort=30002 --set replicasCount=3
```
