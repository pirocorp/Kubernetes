# OpenShift — официални обучения и допълнителни ресурси

Трите учебни пътеки на **Red Hat Developer** допълват Module 09. Следвай ги в този ред, ако искаш повече демонстрации от официалния източник:

1. [Foundations of OpenShift](https://developers.redhat.com/learn/openshift/foundations-openshift) — Web Console, `oc`, builds, deployment, scaling и monitoring.
2. [Learn Kubernetes using the Developer Sandbox](https://developers.redhat.com/learn/openshift/learn-kubernetes-using-developer-sandbox) — backend, frontend, MariaDB, PVC и Secrets.
3. [OpenShift Virtualization and Application Modernization](https://developers.redhat.com/learn/openshift/openshift-virtualization-and-application-modernization-using-developer-sandbox) — VM, legacy приложение и миграция към контейнер.

Нашите [упражнения 09-A–09-E](./labs/README.md) използват същите учебни цели, но съдържат собствени команди и файлове за изпълнение. Оригиналните уроци може да показват различни версии или по-стар изглед на конзолата.

## Оригиналните уроци

Всяко заглавие води към съответния урок на сайта на Red Hat.

### 1. [Foundations of OpenShift](https://developers.redhat.com/learn/openshift/foundations-openshift)

**Оригинална публикация:** 27.06.2023; **ориентир за време:** 3 ч. 40 мин..

| № | Официален урок (оригинален линк) | Към кои умения го отнасяме |
|---|---|---|
| 1 | [OpenShift and the Developer Sandbox](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:openshift-and-developer-sandbox) | Sandbox, onboarding, project |
| 2 | [Overview of the web console](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:overview-web-console) | Конзола и Projects |
| 3 | [Use the terminal window within the web console](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:use-terminal-window-within-red-hat-openshift-web-console) | Web Terminal, oc, kubectl |
| 4 | [Install application from GitHub using web console](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:install-application-source-code-github-repository-using-openshift-web-console) | Git → build → Deployment → Route |
| 5 | [Install application from image using oc](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:install-application-linux-container-image-using-oc-cli-tool) | CLI deployment от OCI image |
| 6 | [Install application from source using oc](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:install-application-source-code-using-oc-cli-tool) | CLI deployment от Git |
| 7 | [Scale using web console](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:scale-applications-using-openshift-web-console) | Реплики през GUI |
| 8 | [Scale using oc CLI](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:scale-applications-using-oc-cli-tool) | Реплики през CLI |
| 9 | [Work with databases using oc](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:work-databases-openshift-using-oc-cli-tool) | MongoDB + Node.js през CLI |
| 10 | [Work with databases in web console](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:work-databases-openshift-web-console) | MongoDB + Node.js през GUI |
| 11 | [View performance information](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:view-performance-information-using-openshift-web-console) | Metrics, performance dashboard |

### 2. [Learn Kubernetes using the Developer Sandbox](https://developers.redhat.com/learn/openshift/learn-kubernetes-using-developer-sandbox)

**Оригинална публикация:** 01.03.2024; **ориентир за време:** около 60–90 мин..

| № | Официален урок (оригинален линк) | Към кои умения го отнасяме |
|---|---|---|
| 1 | [Set up your activity environment](https://developers.redhat.com/learning/learn:openshift:learn-kubernetes-using-developer-sandbox/resource/resources:set-your-activity-environment) | Sandbox access, kubeconfig, Git |
| 2 | [Create a back-end RESTful service](https://developers.redhat.com/learning/learn:openshift:learn-kubernetes-using-developer-sandbox/resource/resources:create-back-end-restful-service) | Python REST, Deployment, Service, Route |
| 3 | [Build a front-end React page](https://developers.redhat.com/learning/learn:openshift:learn-kubernetes-using-developer-sandbox/resource/resources:build-front-end-react-page) | React frontend и backend integration |
| 4 | [Create and populate a database in MariaDB](https://developers.redhat.com/learning/learn:openshift:learn-kubernetes-using-developer-sandbox/resource/resources:create-and-populate-database-mariadb) | MariaDB, PVC, Secret, self-healing |

### 3. [OpenShift virtualization and application modernization using the Developer Sandbox](https://developers.redhat.com/learn/openshift/openshift-virtualization-and-application-modernization-using-developer-sandbox)

**Оригинална публикация:** 29.07.2024; **ориентир за време:** не е обявена обща продължителност.

| № | Официален урок (оригинален линк) | Към кои умения го отнасяме |
|---|---|---|
| 1 | [Create a virtual machine](https://developers.redhat.com/learning/learn:openshift:openshift-virtualization-and-application-modernization-using-developer-sandbox/resource/resources:create-virtual-machine) | Fedora VM, cloud-init и virt-launcher |
| 2 | [Set up a legacy application](https://developers.redhat.com/learning/learn:openshift:openshift-virtualization-and-application-modernization-using-developer-sandbox/resource/resources:set-legacy-application) | httpd във VM, Service, Route |
| 3 | [Modernize the application](https://developers.redhat.com/learning/learn:openshift:openshift-virtualization-and-application-modernization-using-developer-sandbox/resource/resources:modernize-application) | httpd контейнер и cutover |

## Практически упражнения по теми

| Официална тема | Практика в Module 09 |
|---|---|
| Sandbox, Console и CLI | [09-A — Sandbox и `oc`](./labs/LAB-01-SANDBOX-CLI-2026.md) |
| Images, Builds, Routes, Scaling, Metrics | [09-B — Deployment и Builds](./labs/LAB-02-DEPLOY-BUILDS-ROUTES-2026.md) |
| Databases, PVC и Secrets | [09-C — MariaDB](./labs/LAB-03-MARIADB-PVC-2026.md) |
| REST backend, React frontend и database integration | [09-D — Full Stack](./labs/LAB-04-FULLSTACK-2026.md) |
| Virtual machines и modernizing legacy apps | [09-E — Virtualization](./labs/LAB-05-VIRTUALIZATION-CUTOVER-2026.md) |

## Бележки за използването на по-старите примери

- Използвай **личен, изолиран kubeconfig**; не изтривай `~/.kube/config`.
- **base64 не е криптиране**; не съхранявай демонстрационни пароли и токени в Git.
- Различавай OpenShift **Route** от стандартния Kubernetes **Ingress**.
- Проверявай дали образите, API версиите, storage класовете и VM templates са налични в текущата Sandbox среда.
- Проверявай отделно Build, Deployment readiness, публичен Route и persistence — успех на една стъпка не доказва успех на останалите.
- След всяко упражнение изпълнявай точния cleanup, включително PVC и Secrets, а при Virtualization — собствените VM дискове.

**Официален Sandbox:** [Start](https://developers.redhat.com/developer-sandbox) · [FAQ и ограничения](https://developers.redhat.com/developer-sandbox/FAQ).
