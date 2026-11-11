# Module 09 — официални Red Hat обучения: интеграционна карта (2026)

> **Статус:** трите Red Hat learning paths са **интегрирани като източници и план за адаптация**, но това **още НЕ са готови изпълними lab упражнения**.
>
> **Контекст:** [INTRO-2026.md](./INTRO-2026.md) вече обяснява основните понятия по видеото. Настоящият файл добавя официални учебни пътеки, оригинални линкове, съпоставка с Kubernetes Modules 00–08, рискове и договорен стандарт за бъдещите упражнения.
>
> **Проверено:** 11 ноември 2026 г. Тези материали са публикувани през 2023–2024 г.; не приемаме безусловно, че всички техни команди и UI стъпки са подходящи за актуална OpenShift версия или Sandbox.

## 1. Можем ли да интегрираме трите обучения?

**Да — и трите имат ясна практическа роля.** Препоръчителният ред е:

1. **[Foundations of OpenShift](https://developers.redhat.com/learn/openshift/foundations-openshift)** — **основна пътека** след въведението: Web Console, `oc`, image/Git deployment, скалиране, бази данни, monitoring.
2. **[Learn Kubernetes using the Developer Sandbox](https://developers.redhat.com/learn/openshift/learn-kubernetes-using-developer-sandbox)** — **интеграционен lab**: Python REST backend + React frontend + MariaDB, PVC, Secrets, Pod self-healing. Умишлено потвърждава познатите Kubernetes API в OpenShift.
3. **[OpenShift Virtualization and Application Modernization](https://developers.redhat.com/learn/openshift/openshift-virtualization-and-application-modernization-using-developer-sandbox)** — **опционален разширен lab**: стартиране на VM с legacy приложение, Service/Route и преминаване към контейнеризиран вариант.

И трите използват **Red Hat Developer Sandbox** — не е необходима инсталация на собствен OpenShift cluster, за да започнем. Но Sandbox е shared среда с лимитирани права; за cluster-admin упражнения ще е нужна друга lab среда.

**Лиценз/авторство:** запазваме оригиналните линкове и авторство. Пишем собствени обяснения и manifests; не копираме на едро чужди screenshots, уроци или source code. Ако в бъдеще включим upstream примерен код, трябва да проверим лиценза и commit/release.

## 2. Оригинални уроци и връзки

По-долу са **всичките 18 индивидуални урока**, заедно с линк към началната страница на всяка от трите пътеки. Заглавията са описателни, оригиналното съдържание остава на сайта на Red Hat.

### 2.1. [Foundations of OpenShift](https://developers.redhat.com/learn/openshift/foundations-openshift)

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

### 2.2. [Learn Kubernetes using the Developer Sandbox](https://developers.redhat.com/learn/openshift/learn-kubernetes-using-developer-sandbox)

**Оригинална публикация:** 01.03.2024; **ориентир за време:** около 60–90 мин..

| № | Официален урок (оригинален линк) | Към кои умения го отнасяме |
|---|---|---|
| 1 | [Set up your activity environment](https://developers.redhat.com/learning/learn:openshift:learn-kubernetes-using-developer-sandbox/resource/resources:set-your-activity-environment) | Sandbox access, kubeconfig, Git |
| 2 | [Create a back-end RESTful service](https://developers.redhat.com/learning/learn:openshift:learn-kubernetes-using-developer-sandbox/resource/resources:create-back-end-restful-service) | Python REST, Deployment, Service, Route |
| 3 | [Build a front-end React page](https://developers.redhat.com/learning/learn:openshift:learn-kubernetes-using-developer-sandbox/resource/resources:build-front-end-react-page) | React frontend и backend integration |
| 4 | [Create and populate a database in MariaDB](https://developers.redhat.com/learning/learn:openshift:learn-kubernetes-using-developer-sandbox/resource/resources:create-and-populate-database-mariadb) | MariaDB, PVC, Secret, self-healing |

### 2.3. [OpenShift virtualization and application modernization using the Developer Sandbox](https://developers.redhat.com/learn/openshift/openshift-virtualization-and-application-modernization-using-developer-sandbox)

**Оригинална публикация:** 29.07.2024; **ориентир за време:** не е обявена обща продължителност.

| № | Официален урок (оригинален линк) | Към кои умения го отнасяме |
|---|---|---|
| 1 | [Create a virtual machine](https://developers.redhat.com/learning/learn:openshift:openshift-virtualization-and-application-modernization-using-developer-sandbox/resource/resources:create-virtual-machine) | Fedora VM, cloud-init и virt-launcher |
| 2 | [Set up a legacy application](https://developers.redhat.com/learning/learn:openshift:openshift-virtualization-and-application-modernization-using-developer-sandbox/resource/resources:set-legacy-application) | httpd във VM, Service, Route |
| 3 | [Modernize the application](https://developers.redhat.com/learning/learn:openshift:openshift-virtualization-and-application-modernization-using-developer-sandbox/resource/resources:modernize-application) | httpd контейнер и cutover |

## 3. Съпоставка с предишните модули и предложени бъдещи exercises

| Група | Референция | Бъдещо самодостатъчно упражнение | Как ще се провери |
|---|---|---|---|
| **09-A Sandbox / CLI** | Foundations 1–3 | Профил, Sandbox, current Project, `oc` login, Web Terminal; безопасно управление на contexts | `oc whoami`, `oc project`, `oc get pods` и сравнение с `kubectl` |
| **09-B App deployment** | Foundations 4–6 | Deployment от Git и image през GUI/CLI; Build → image → Deployment → Service → Route | Build logs, Ready Pods, route HTTP отговор, teardown |
| **09-C Scaling / metrics** | Foundations 7–8, 11 | Ръчно `scale` през двата интерфейса, наблюдение и диагностика | replicas, endpoints, events и графики; обратно скалиране |
| **09-D Data / Secrets** | Foundations 9–10 | Database + приложение; Secret, PVC и разлика ephemeral/persistent | реална заявка, persistence проверка, безопасен cleanup |
| **09-E Full stack** | Kubernetes-in-Sandbox 1–4 | Python REST + React + MariaDB, Deployment/Service/Route/PVC/Secret, актуализация и отказ | работещи frontend/API/DB, scaling и възстановяване след Pod delete |
| **09-F Virtualization** | Virtualization 1–3 | Fedora/поддържана VM, legacy httpd, Route и контролирано прехвърляне към контейнер | VM status, route reachability, cutover, rollback, cleanup |

**Не дублираме** основните задачи от Modules 00–08: Namespace, Deployment, PVC, Secrets и NetworkPolicy вече са преподавани като Kubernetes. Новите exercises трябва да показват **OpenShift-специфичния workflow и практическите ограничения**, не да възпроизвеждат същия Kubernetes lesson втори път.

**Не сменяме произволно езиците на официалните упражнения:** оригиналният full-stack scenario остава Python/React/MariaDB. Отделен **ASP.NET Core/.NET вариант** е подходящ като надграждане, но той не е част от оригиналния Red Hat урок и ще се обсъжда след останалите предоставени материали.

## 4. Developer Sandbox — проверени предпоставки

**Официални линкове:** [Developer Sandbox](https://developers.redhat.com/developer-sandbox) · [Developer Sandbox FAQ](https://developers.redhat.com/developer-sandbox/FAQ).

- Безплатна **30-дневна** trial среда; изисква Red Hat account, без кредитна карта. Red Hat посочва и **проверка на телефонен номер** като anti-abuse механизъм.
- Shared multi-tenant среда. Нямаме гарантиран `cluster-admin` достъп, node-level SSH или права за инсталиране на всякакви Operators.
- Според актуалния FAQ, **Pods се изтриват след 12 часа непрекъснато изпълнение**; **Linux VMs се спират след 1 час**. Планирай лабораториите на кратки, възпроизводими сесии.
- Red Hat включва **OpenShift Virtualization** сред Sandbox възможностите, но наличните VM templates, ресурси и privileges са зависими от средата и се проверяват преди разработване на окончателни VM стъпки.
- Историческите уроци описват **един персонален `<username>-dev` проект**. Не предполагаме, че можем да създаваме нови projects в Sandbox, преди да проверим квоти/права.
- Достъпът до Kubernetes/OpenShift се настройва чрез `oc login` или kubeconfig. **Не** commit-ваме токени, personal kubeconfig, пароли или лични URL адреси.

**Безопасни read-only проверки, валидни след достъп:**

```bash
oc version
oc whoami
oc config current-context
oc project
oc get pods
oc get deployments,services,routes
oc get pvc
```

**Очакван резултат:** върнати username/project/context, а списъците могат да са и празни; `No resources found` не е автоматично грешка. `Unauthorized` означава проблем с authentication, `Forbidden` — липса на RBAC права. **Cleanup:** няма създадени ресурси. Това е само orientation preflight, **не** възпроизвеждане на трите learning paths.

## 5. Важни проблеми в оригиналните уроци — НЕ копирай без адаптация

| Конкретно наблюдение | Задължителна корекция в нашия курс |
|---|---|
| Много screenshots и интерфейсни инструкции са от 2023–2024 г.; една CLI демонстрация показва стар OpenShift 4.10 / Kubernetes 1.23 | Да се използват актуален UI и версия. Тук **не фиксираме** target OpenShift/OKD release. |
| Kubernetes environment урокът предлага да се изтрие цялото `~/.kube/config` | **Не**: това може да премахне съществуващи credentials/contexts. Да се използва изолиран `KUBECONFIG` или безопасно почистване само на конкретно създадения context. |
| MariaDB примерът използва base64-encoded, фиксирана демонстрационна парола | Да се използва собствен Secret и да се обясни, че **base64 не е криптиране**; без plaintext парола в Git. |
| Backend урокът показва **два различни quay.io paths** за един примерен image | Проверка на upstream repo, pinned image и консистентни references, преди да се твърди, че сценарият е изпълним. |
| „Plain Kubernetes“ demo използва OpenShift **Route** за публичен достъп | Да се маркира като OpenShift-specific ресурс, **не** като стандартен Kubernetes Ingress API. |
| Виртуализационният урок задава парола **`password`** и използва **Fedora 39** | Никакви слаби hard-coded credentials; нужна е проверка за текущо поддържан VM template. |
| Database labs разчитат на исторически image tags, ephemeral templates и непиннати примерни repositories | Проверка на съвместимост, manifest API, image availability и sandbox permissions; собствен reproducible setup. |
| Предложеният `kubectl delete all -l ...` не почиства непременно PVC, Secrets, Routes и всички създадени ресурси | Точен cleanup по обекти, с проверка на PV reclaim policy; без изтриване на чужди данни. |
| Resource-pressure пример се прилага от непиннат remote URL на `main` | Бъдещият lab да ползва commit-pinned и инспектиран manifest, не променящ се безконтролно URL. |

**Статус:** проблемите са **идентифицирани**, не решени. Текущият PR **не** добавя нови runnable source files и **не** претендира за успешни runtime tests.

## 6. Условия за завършено собствено упражнение

Преди да наречем някой от горните бъдещи labs „самодостатъчен“, той трябва да съдържа всички следни елементи:

1. Environment/версия, Sandbox или local/SNO, квоти, permissions, tools и съвместимости.
2. Пълни инструкции и необходимите manifests/sample code, pinned versions, ports, selectors и paths.
3. Команди в точната им последователност; никакви скрити ръчни предпоставки или стъпки „намери в документацията“.
4. Очакван резултат, проверки за Pod readiness, Route/network, persistence/VM, logs/events.
5. Troubleshooting, controlled failure/recovery когато е приложимо, rollback и изчерпателен cleanup.
6. Статичен audit като достатъчна приета проверка; **без** да заявяваме live success при липса на реално изпълнение.
7. Линк към всеки съответен **оригинален урок на Red Hat** и ясно разграничение между оригинала и нашата адаптация.

## 7. Предложени бъдещи PR-и — след всички материали

- **PR A:** актуализиран Sandbox onboarding, Projects, Web Console и CLI.
- **PR B:** Deploy from Git/image, Builds, Services/Routes/TLS, scaling/metrics.
- **PR C:** много-компонентно приложение с database, Secret/PVC и resilience.
- **PR D:** Virtualization и VM → container cutover, ако текущата среда го позволява.
- **PR E:** окончателен audit, integration със `COURSE-2026.md` и цялостен module navigation.

Това **не е окончателен план**: материалите на потребителя имат приоритет. Няма да стартира реална разработка на тези упражнения преди изричния сигнал **„ГОТОВО — приключих с подаването на информацията.“**

## 8. Източници и метод

Всички връзки към **трите основни учебни пътеки и 18-те отделни урока** са оригинални ресурси на [Red Hat Developer](https://developers.redhat.com/). Те са включени като **външни референции**, не като копирани чужди учебни файлове. Допълнителен контекст: [OpenShift product overview](https://developers.redhat.com/products/openshift/overview).

> **Проверки за тази стъпка:** статичен review на навигацията, Markdown и оригиналните source URLs. Не е правен live Sandbox, Kubernetes или Virtualization тест; **текущият документ е карта на интеграцията, не изпълним учебен lab**.
