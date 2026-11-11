# OpenShift — практически упражнения

След въведението в [Module 09](../README.md) премини през упражненията в следния ред. Всяко упражнение съдържа предпоставки, нужните файлове, последователност от команди, очаквани резултати, проверки, troubleshooting и cleanup.

| Ред | Упражнение | Какво ще упражниш | Официално обучение |
|---|---|---|---|
| **09-A** | [Developer Sandbox, Console и `oc`](./LAB-01-SANDBOX-CLI-2026.md) | Project, CLI login, RBAC, безопасен kubeconfig, API и Web Console | [Foundations](https://developers.redhat.com/learn/openshift/foundations-openshift) |
| **09-B** | [Deployments, S2I Builds, Services и Routes](./LAB-02-DEPLOY-BUILDS-ROUTES-2026.md) | Готов image, source build, ImageStream, scaling, rollback и metrics | [Foundations](https://developers.redhat.com/learn/openshift/foundations-openshift) |
| **09-C** | [MariaDB, Secrets и PVC](./LAB-03-MARIADB-PVC-2026.md) | База данни, SQL, persistent storage, възстановяване след изтриване на Pod | [Foundations — databases](https://developers.redhat.com/learn/openshift/foundations-openshift) |
| **09-D** | [Python REST + React + MariaDB](./LAB-04-FULLSTACK-2026.md) | Трислойно приложение, вътрешни Services, Route, probes и recovery | [Kubernetes using Sandbox](https://developers.redhat.com/learn/openshift/learn-kubernetes-using-developer-sandbox) |
| **09-E** | [OpenShift Virtualization](./LAB-05-VIRTUALIZATION-CUTOVER-2026.md) | Linux VM, legacy Apache, Service, Route, cutover към контейнер и rollback; fallback без VM за Route механиката | [Virtualization & Modernization](https://developers.redhat.com/learn/openshift/openshift-virtualization-and-application-modernization-using-developer-sandbox) |

## Учебна среда

Използвай [Red Hat Developer Sandbox](https://developers.redhat.com/developer-sandbox) с личен Project и разрешените за него операции. Това **не е** Kubernetes lab кластерът от Modules 00–08. Ако използваш локален `oc`, следвай първо [09-A](./LAB-01-SANDBOX-CLI-2026.md) за настройка на отделен kubeconfig.

Sandbox има ограничени права, resource quotas и ограничен срок на достъп. Според [официалния FAQ](https://developers.redhat.com/developer-sandbox/FAQ) Pods и Linux VMs имат ограничения за продължителност на работа. При Virtualization трябва да има наличен VM template и разрешение за VMs. Ако липсват, [Lab 09-E, раздел 12](./LAB-05-VIRTUALIZATION-CUTOVER-2026.md) предлага отделен контейнерен Route cutover, **който не замества VM учебната цел**.

Изпълнявай упражненията **по едно**, за да избегнеш конфликтни имена, квоти и неочаквани разходи. Не публикувай токени или пароли. Изтривай само обектите, които самото упражнение е създало.

## Примерни файлове

Всички необходими за упражненията собствени файлове се намират в [examples/](./examples/): Python, React/Node.js, MariaDB и манифести за VM → container cutover. Готовите `image.yaml`, `db.yaml`, `seed.sql` и VM fallback manifests не трябва да се пишат от нулата. В Lab 09-D е описано как да се генерира `package-lock.json` преди Node S2I build (локално или чрез Docker). За образи и пакети от външни registry източници провери реалната им достъпност по време на изпълнение.

## Допълнителни материали

[18 оригинални Red Hat урока с преки линкове](../REDHAT-LEARNING-PATHS-2026.md) · [Уводът на Module 09](../README.md).
