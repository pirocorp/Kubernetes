# Module 09 — OpenShift

**OpenShift е Kubernetes-базирана платформа за разработване, публикуване и поддръжка на контейнеризирани приложения.** Този урок започва от основните понятия и постепенно показва как се използват Projects, Builds, Routes, CLI, сигурност и наблюдение в една обща среда.

**Какво ще научиш:** как Kubernetes работи под OpenShift; какво допълва платформата; как се публикува приложение; кои са основните продукти и услуги; как изглежда работният процес в Developer Sandbox.

**Предварителни знания:** базови Kubernetes понятия (Pod, Deployment, Service, Namespace, RBAC и Ingress) от предходните модули. Не е нужен предишен опит с OpenShift.

### Учебен път

1. Прочети уводните раздели по-долу и разгледай двете архитектурни Mermaid диаграми.
2. Преговори ключовите термини и отговори на въпросите за самопроверка.
3. Премини към [практическите упражнения 09-A–09-E](./labs/README.md), подредени от първи стъпки до Virtualization.
4. При нужда използвай [оригиналните Red Hat обучения](./REDHAT-LEARNING-PATHS-2026.md) за допълнително четене.

---

## 1. Какво е OpenShift и как се свързва с Kubernetes

Достатъчни са основните понятия от Kubernetes: **контейнер**, **Pod**, **Deployment**, **Service**, **Namespace**, **RBAC** и **Ingress**. Ако ги знаеш, OpenShift няма да е нов свят от нулата — той използва Kubernetes и добавя интегрирана платформа за разработване, доставка, сигурност и експлоатация на приложения.

**Най-краткото определение:** *Red Hat OpenShift е Kubernetes-базирана платформа, която предоставя допълнителни интегрирани инструменти и управлявани компоненти за изграждане, внедряване и поддържане на приложения.*

Не бъркай **Kubernetes** (оркестрация на контейнери) с **OpenShift** (по-широка платформа, стъпила върху Kubernetes).

### Архитектурата в една схема

OpenShift включва Kubernetes като основен оркестратор и добавя интегрирани компоненти:

```mermaid
flowchart TB
    subgraph OCP["Red Hat OpenShift — интегрирана платформа"]
        direction TB
        TOOLS["Web Console · Routes · SCC · Builds · Operators · Monitoring"]
        subgraph K8S["Kubernetes — основният оркестратор"]
            direction TB
            CONTROL["API Server · Scheduler · Controllers · etcd"]
            WORKLOAD["Pods · Deployments · Services"]
            CONTROL --> WORKLOAD
        end
        TOOLS --> CONTROL
    end

    subgraph HOST["Инфраструктура / cluster nodes"]
        direction TB
        OS["Linux / CoreOS · VM / bare metal / cloud"]
        CRI["CRI-O runtime · container networking · storage"]
        OS --> CRI
    end

    WORKLOAD --> CRI
```

**Как да я четеш:** **Kubernetes е реалният orchestration engine в OpenShift**, а OpenShift предоставя интеграциите и начина за администриране. Отдолу съществуват Linux възли и container runtime. Диаграмата е **концептуална**, не deployment схема: много OpenShift компоненти сами работят като Pods/Operators вътре в Kubernetes; стрелките не означават, че платформата заобикаля Kubernetes API.

## 2. Контейнери, Kubernetes и OpenShift

![Слайд от видеото: Технологиите зад OpenShift](./OpenShift.png)

Разграничи три слоя от технологията:

1. **Docker** — познат инструмент за създаване на контейнерни образи и локална работа с контейнери. **Историческо уточнение:** не приемай, че съвременните OpenShift възли използват Docker Engine. OpenShift 4.x използва **CRI-O** като container runtime; OpenShift 5 също е базиран на CRI-O. Създаването на образ с Docker/Buildah/друг OCI-съвместим инструмент не е същото като runtime на клъстера.
2. **Kubernetes** — API и контролери, които управляват Pods, Deployments, Services, конфигурация, scheduling, възстановяване и мащабиране.
3. **Допълнителни инструменти** — специфичните за OpenShift удобства: Projects, Routes, Build механизми, web console, `oc` CLI, Security Context Constraints (SCC), Operators, интеграции за registry и управление на платформата.

Мисловен модел:

```text
Твоят код (.NET, Java, Node.js...)
          |
       OCI image  <-- образът може да се изгради с различни инструменти
          |
 OpenShift application platform
   | Kubernetes API + workload controllers
   | Projects, Routes, security policies, console, operators, builds
          |
 Kubernetes cluster nodes + CRI-O + containers
```

**Важно:** Това е учебна схема, не точна мрежова или компонентна архитектура.

## 3. Защо OpenShift улеснява разработката

### 3.1. Защо съществува OpenShift?

Погледнато от гледната точка на разработчика: преди приложението да обслужи реален потребител, трябват изчислителни ресурси, ОС, мрежа, конфигурация, разгръщане и начин за наблюдение. OpenShift събира много от тези възможности в интегрирана платформа, така че разработчиците да се фокусират повече върху приложението.

Често се използва понятието **Platform as a Service (PaaS)**. Това е добро първо приближение за **управлявани** OpenShift услуги и за потребителското изживяване на един developer в готов клъстер. **Уточнение:** при self-managed OpenShift организацията продължава да носи съществена отговорност за инфраструктура, обновления, експлоатация, достъпи и капацитет. OpenShift не премахва автоматично всички DevOps/SRE задачи.

### 3.2. Обяснението с куфара и къщата

- **Docker / контейнерен image = „куфар“:** приложението се пакетира със зависимостите му, за да бъде възпроизводимо между среди.
- **Kubernetes = „управител на куфарите“:** оркестрира изпълнението, желаното състояние, replica-ите и възстановяването при отказ.
- **OpenShift = „обзаведена къща“:** Kubernetes плюс интегрирани, готови за използване възможности, UI, security, builds и оператори.

**Къде аналогията подвежда:** контейнерният image не е гаранция, че приложение ще работи на *всяка* ОС/CPU архитектура или с всякаква мрежа, secrets, storage и външни услуги. Kubernetes не стартира HPA скалиране само защото натоварването се е покачило — нужни са подходяща конфигурация и метрики. И контейнерът не е непременно създаден от Docker Engine.

### 3.3. Защо компании избират OpenShift?

Основните корпоративни мотиви са: стандартизирани разгръщания, улеснено управление, security инструменти, документация, поддръжка според конкретния договор и възможност за **on-premises** или cloud deployment. Споменават се банки, застрахователи и телекоми заради контрола над данни, инфраструктура и нормативни изисквания.

**Уточнение:** регулации сами по себе си не изискват всички такива организации да са on-premises. Допустимата среда зависи от конкретните правила, договори и risk assessment.

## 4. Основни компоненти на платформата

![Слайд от видеото: Основни компоненти на OpenShift](./OpenShift%20-%20Components.png)

### 4.1. Projects — работни пространства

В Kubernetes вече познаваш **Namespaces**. OpenShift **Project** е ориентираното към потребителя представяне на namespace с допълнителен проектен workflow и управление на достъпа.

- Един екип може да работи в проект `payments-dev`, друг — в `payments-test`.
- Pods, Deployments, Services и Routes са ресурси в даден namespace/project.
- Project **не** е отделен клъстер и не означава автоматично пълна мрежова изолация.
- **RBAC** определя кой потребител или service account може да извършва действия.

Аналогия: *Namespace е Kubernetes логическият обхват; Project е начинът OpenShift да представи и управлява този обхват за екипи.*

### 4.2. Builds — от изходен код до container image

**Build** процесът е за създаване на **image**, а **Deployment** е за изпълнение на този image като Pods. Това са различни фази.

Пример с ASP.NET Core:

```text
Git repository с .NET код
       |
       | build (в CI или чрез OpenShift build tooling)
       v
Container image
       |
       v
Registry
       |
       v
Deployment -> Pods, които изпълняват приложението
```

OpenShift е познат с **BuildConfig / Source-to-Image (S2I)** и **ImageStreams**, но не е задължително да ги използваш. Съществуват и външни CI системи, Dockerfile/OCI build workflows и други интеграции. Практическият [Lab 09-B](./labs/LAB-02-DEPLOY-BUILDS-ROUTES-2026.md) демонстрира S2I BuildConfig и ImageStream, а също и deployment директно от готов image.

**Капан:** Build ≠ Deploy. Успешно създаден image не доказва, че приложението е стартирало успешно.

### 4.3. Routes — достъп до приложението извън клъстера

Позната ти е схемата `Pod <- Service <- Ingress`. OpenShift традиционно предлага и ресурс **Route**, който публикува Service през ingress/router инфраструктурата.

```text
Клиент (браузър, API consumer)
         |
    HTTPS hostname
         |
    OpenShift Route
         |
    Service (port)
         |
    Pod (.NET API listening on targetPort)
```

- **Service** намира и балансира Pods вътре в клъстера.
- **Route** предоставя външен hostname и правила за публикуване; TLS конфигурацията зависи от конкретната Route.
- **Ingress** е стандартен Kubernetes API, който също може да бъде използван в OpenShift при подходяща конфигурация.
- Route не замества Deployment, Service или Pod.

**Капан:** портът на контейнера, `Service.port`, `Service.targetPort` и външният HTTPS порт не са непременно един и същ порт.

### 4.4. Web Console и `oc` CLI — два начина за работа

**Web Console** е графичен интерфейс за разглеждане и управление на приложения, ресурси и състоянието на клъстера според правата ти.

**`oc`** е OpenShift CLI. То поддържа много от познатите ти операции от `kubectl` и добавя OpenShift-специфични команди.

| Позната задача | Kubernetes | OpenShift |
|---|---|---|
| Избиране на контекст | `kubectl config current-context` | `oc config current-context` |
| Списък на Pods | `kubectl get pods -n payments-dev` | `oc get pods -n payments-dev` |
| Deployment | `kubectl get deployment -n payments-dev` | `oc get deployment -n payments-dev` |
| Работно пространство | `kubectl get namespaces` | `oc projects` (достъпни проекти) |
| Текуща идентичност | — | `oc whoami` |
| Избор на проект | `kubectl config set-context --current --namespace=payments-dev` | `oc project payments-dev` |
| OpenShift Routes | — (не е стандартен Kubernetes ресурс) | `oc get routes -n payments-dev` |

Това са **илюстративни команди**, а не готов lab: изискват инсталиран `oc`, достъп до OpenShift cluster и подходящи permissions. `payments-dev` е примерен проект, не предварително създаден ресурс.

**Бележка за конзолата:** снимки или по-стари видеа могат да показват отделни Developer/Administrator perspectives. Интерфейсът се развива; не приемай старото меню за задължително в актуалните версии.

### 4.5. SCC — Security Context Constraints

**Security Context Constraints** са OpenShift-механизъм за ограничения на това *как* могат да работят Pods/контейнери — например по отношение на UID, привилегии, capabilities и достъп до host ресурси.

Разграничи три неща:

| Механизъм | Отговаря на въпроса |
|---|---|
| **RBAC** | *Кой* може да създава/чете/променя ресурси? |
| **SCC** | *С какъв допустим security context* може да бъде допуснат Pod? |
| **NetworkPolicy** | *Кой мрежов трафик* е разрешен между избрани Pods/адреси? |

**Капан за .NET приложения:** образ, който очаква задължително да работи като root или да записва в root-owned директория, може да има проблем при по-строги security настройки. При .NET workloads поправяй image permissions и user configuration; не заобикаляй SCC чрез привилегирован Pod.

## 5. Kubernetes срещу OpenShift

![Трети оригинален слайд — Kubernetes vs OpenShift](./Kubernetes%20vs%20OpenShift.png)

Сравнението показва разликата между базовия оркестратор и готовата интегрирана платформа:

| Въпрос | Инженерно уточнение |
|---|---|
| Kubernetes е технология с отворен код; OpenShift е завършено корпоративно решение | Kubernetes е open source; комерсиалният OpenShift включва продуктови интеграции и възможности за поддръжка. **OKD** е community/upstream проектът в екосистемата — не всеки вариант на OpenShift е търговски управлявана услуга. |
| Kubernetes изисква допълнителни инструменти | В vanilla Kubernetes много неща (web console, мониторинг, registry, CI/CD) се инсталират/интегрират отделно; **не** означава, че Kubernetes е неспособен да ги предостави чрез други дистрибуции. |
| OpenShift се управлява „чрез платформата“, Kubernetes — „чрез API“ | **OpenShift също използва Kubernetes API.** Web Console и `oc` са интерфейси/клиенти, не отделен заместител на API. |

**Извод:** Kubernetes и OpenShift не са две независими взаимозаменяеми технологии от един и същи слой. OpenShift е Kubernetes-базиран цялостен продукт.

## 6. От изходен код до работещ HTTPS endpoint

Да си представим, че екипът публикува `payments-api`:

1. **Project `payments-dev`** определя логическия обхват и правата на екипа.
2. Кодът се **build-ва** до контейнерен образ чрез избрания pipeline.
3. Образът се поставя в **registry**.
4. **Deployment** описва желаните replicas и image; Kubernetes създава **Pods**.
5. **SCC** и останалите security механизми влияят върху допускането и изпълнението на Pods.
6. **Service** насочва трафика към готовите Pods.
7. **Route** публикува API-то чрез hostname, например `payments.example.test` (пример, не действащ адрес).
8. **Web Console** и **`oc`** позволяват да се наблюдават status, events и logs.

Това е *концептуална последователност*, не предписана система за автоматизация на builds/deployments.

## 7. Какво вече знаем от Kubernetes

| Вече знаеш от Kubernetes | Какво добавя/променя OpenShift |
|---|---|
| Namespace, RBAC | Project workflow и интеграция с потребители и права |
| Pods, Deployments, Services | Същите основни Kubernetes API обекти, плюс платформени инструменти |
| Ingress и TLS | OpenShift Routes и router/ingress integration |
| CI/CD и container images | OpenShift build инструменти, registry/ImageStreams при избор на тези workflow-и |
| `kubectl` | `oc` CLI и web console |
| Pod security context, RBAC, NetworkPolicy | Допълнителни SCC правила и платформени defaults |
| kubeadm + containerd + Calico във вашия lab | **Не** се пренася механично: OpenShift има собствен installation/cluster lifecycle и обичайно използва CRI-O и интегрирано управлявана мрежова конфигурация |

**Особено важно:** не инсталирай OpenShift „върху“ готовия kubeadm/Calico lab като поредния addon. За [упражненията 09-A–09-E](./labs/README.md) използвай **отделната Red Hat Developer Sandbox среда**, а не Kubernetes клъстера с Calico.

## 8. Дистрибуции и управлявани услуги

| Продукт или услуга | Какво представлява |
|---|---|
| **OKD** | Community/upstream Kubernetes дистрибуция в OpenShift екосистемата. Няма стандартния търговски Red Hat support, предлаган с платени продукти. Не приемай, че е просто „същият платен OpenShift, но без лиценз“. |
| **OpenShift Online** | Историческо наименование за хоствана услуга. **Не избирай** инсталационен или учебен път само по това старо име — провери наличните предложения към момента на обучението. |
| **OpenShift Dedicated** | Управляван OpenShift продукт върху облачна инфраструктура, с обхват и отговорности според конкретната услуга. |
| **OpenShift Enterprise** | Самостоятелно управляваното on-premises корпоративно решение се позиционира днес като **Red Hat OpenShift Container Platform**. |
| **ROSA — Red Hat OpenShift Service on AWS** | Управляван OpenShift върху AWS. **Не е** еквивалент на Amazon EKS; и двете използват Kubernetes, но са различни услуги. |
| **AKS / EKS** | Съответно Kubernetes услуги на Azure и AWS, но не са OpenShift. |
| **Azure Red Hat OpenShift (ARO)** | OpenShift работи като управлявана услуга **и в Azure**, предоставяна съвместно от Microsoft и Red Hat. |
| **OpenShift Virtualization** | Управление и изпълнение на виртуални машини като част от Kubernetes/OpenShift платформата; не означава, че всяка VM автоматично става контейнер. |

**Какво означава „безплатно“?** OKD е общностна дистрибуция, а **Developer Sandbox** е безплатен ограничен trial на управлявана среда. Това са *различни неща*. Нито едното не премахва ресурсните ограничения или операционните отговорности на собствена инсталация.

## 9. Версии и съвместимост

На **9 ноември 2026 г.** Red Hat обяви обща наличност (**GA**) на **OpenShift 5**, базиран на **Kubernetes 1.36 и CRI-O 1.36**. Това е важно, защото основният Kubernetes курс е за **Kubernetes 1.37** — **номерата не трябва да се изравняват изкуствено**.

Винаги проверявай версията на конкретния кластер чрез `oc version`. Developer Sandbox е управлявана среда и не е задължително да използва същата версия като самостоятелния ни Kubernetes 1.37 lab.

## 10. Практически пример: Developer Sandbox

Примерният сценарий демонстрира **Developer Sandbox for Red Hat OpenShift** с примерен **Node.js** проект от GitHub. Целта е да покаже developer workflow, без участниците да инсталират клъстер локално.

### 10.1. Типичен работен процес

1. Отвори **Red Hat Developer Sandbox** и влез с личния си Red Hat акаунт.
2. Избери OpenShift Sandbox и отвори **Web Console**.
3. Ако има Web Terminal, разгледай основни Linux инструменти за системна информация, като `lscpu`, `df -h` и `free -h`. Резултатите описват съответната терминална среда, **не гарантираната квота на целия клъстер**.
4. В избрания Project отвори **Import from Git**.
5. Посочи изходен Git repository с приложение. За възпроизводим пример използвай [изходния код от Lab 09-B](./labs/LAB-02-DEPLOY-BUILDS-ROUTES-2026.md), вместо случаен публичен repository.
6. Прегледай разпознатите настройки на приложението, builder и deployment стратегията; използвай defaults само ако са подходящи.
7. Стартирай **Create** и проследи състоянието на Build от `Running` до `Complete`, като разгледаш логовете.
8. Прегледай **Metrics**, декларативния **YAML**, **Events** и визуализацията **Topology**.
9. Сравни състоянието на ресурсите в UI и през `oc`.
10. Отвори **публикувания URL** и провери HTTP отговора на приложението.
11. Провери дали приложението има база данни или PVC: без подходящо persistent storage **не можеш да приемаш, че данните се запазват**.

### 10.2. Какви Kubernetes/OpenShift обекти участват?

Типичната последователност от обекти и действия е:

```mermaid
flowchart LR
    G["Git repository с код"] --> B["Build (инструмент според template/версия)"]
    B --> I["Container image"]
    I --> R["Container registry"]
    R --> D["Deployment"]
    D --> P["Pod(ове)"]
    P --> S["Service"]
    S --> RT["Route / HTTPS URL"]
    RT --> U["Браузър"]
```

Конкретните имена на ресурсите, използваният builder и регистърът за образи зависят от избрания deployment workflow. Схемата показва логическия модел, а не фиксирана конфигурация на всеки OpenShift клъстер.

### 10.3. Как проверяваме успеха?

- **Build succeeded:** изходният код е превърнат успешно в image/артефакт по избраната стратегия.
- **Deployment healthy:** приложението може да стартира и Pod-овете достигат готовност — това не следва само от успешния build.
- **Route reachable:** потребителят вижда уеб приложението през външен URL.
- **Persistence:** ако приложението записва състояние, то трябва да използва подходящ datastore, PVC или друга стратегия за съхранение.

**Практика:** изпълни [Lab 09-B](./labs/LAB-02-DEPLOY-BUILDS-ROUTES-2026.md), където има изходен код, build, Service, Route, проверки и cleanup.

## 11. Често задавани технически въпроси

### Docker, Kubernetes и OpenShift „едно в друго“ ли са?

Често се използва опростеното обяснение „Docker → Kubernetes → OpenShift“. **По-точно:** контейнерният image може да се създаде с Docker, но Kubernetes управлява контейнери чрез CRI-съвместим runtime; OpenShift е Kubernetes дистрибуция и платформа, която обичайно ползва **CRI-O**, не Docker Engine на възлите. Виж основната Mermaid диаграма по-горе.

### Какво е миграция от SDN към OVN?

Това е преминаване от исторически **OpenShift SDN** към **OVN-Kubernetes**. Важни са проверките, NetworkPolicy, производителността и план за миграция. **Уточнение:** downtime не трябва да бъде обявяван за *неизбежен* при всеки случай — допустимият migration path, downtime, изискванията и ограниченията са **строго версионно зависими**. Това е отделна административна операция, която изисква версия-специфично ръководство и тестова среда.

### В Azure има ли OpenShift, или само AKS?

**Има и двете.** **AKS** е Azure Kubernetes Service, а **ARO — Azure Red Hat OpenShift** е отделна управлявана услуга. В AWS аналогичната разлика е **EKS** срещу **ROSA**.

### Защо `etcd` е критичен и как се прави възстановяване?

`etcd` съхранява желаното и наблюдавано конфигурационно състояние на Kubernetes API обектите. Препоръчват се **редовни backup-и и тестови възстановявания в отделна съвместима среда**.

**Уточнение:** etcd snapshot не е автоматичен backup на приложните данни в PVC или външна DB. Restore на production cluster state е високорискова операция и се прави по конкретния **поддържан OpenShift runbook**, а не с произволна kubeadm процедура.

### Може ли OpenShift „сам“ да deploy-не frontend, backend и DB?

Да, тези компоненти могат да работят в OpenShift. **Но** правилното им свързване изисква deployment definitions, Services, Secrets, Storage, конфигурация на connection strings, migrations и readiness probes; Helm, Pipelines, GitOps и Operators могат да автоматизират част от процеса. OpenShift не отгатва бизнес архитектурата от произволно repository.

### Може ли CronJob да чисти PVC и логове?

**Технически е възможно** чрез Kubernetes `CronJob` с подходящ mount и permissions, но това трябва да е съобразено с **лог lifecycle и retention policy**. Приложни логове е за предпочитане да се изпращат към централизирана logging система; безразборно триене от PVC може да наруши работа, разследвания или retention изисквания. Това изисква отделно планиране на retention policy и безопасно почистване; не бъркай CronJob с управлявана logging система.

### Защо при cluster upgrade и двете replicas на приложение могат да отпаднат?

При две едновременно недостъпни replicas няма достатъчно информация за коренната причина без диагностика. Проверяват се `Deployment` update strategy (`maxUnavailable`, `maxSurge`), `PodDisruptionBudget`, node drains, readiness, startup/liveness probes, termination grace period, ресурсни ограничения, pod placement, events и application logs. **PDB не гарантира наличност при всички видове откази** и не е решение само по себе си.

### Какво е OpenShift Virtualization?

Платформена възможност за изпълнение на **VM workloads** заедно с контейнеризирани приложения на Kubernetes инфраструктура чрез подходящ virtualization stack. Тази възможност може да се използва като вариант за постепенна миграция от виртуални машини към контейнери — полезна мотивация, но не означава автоматична конверсия на приложенията.

## 12. Важни разграничения и често срещани грешки

| Често срещано погрешно твърдение | По-точна формулировка |
|---|---|
| Docker „е под“ Kubernetes/OpenShift | Docker е познат build и local container инструмент; актуалният OpenShift runtime на nodes е CRI-O. |
| Приложението „гарантирано“ работи навсякъде след containerization | Не, съвместимостта зависи от CPU/OS, конфигурация, секрети, storage, networking и външни услуги. |
| Kubernetes сам засича CPU load и автоматично създава replicas | Автоматичното скалиране изисква правилно конфигуриран autoscaler, метрики и достатъчно ресурси. |
| OpenShift напълно премахва системната поддръжка | Степента на поета от Red Hat/cloud provider отговорност зависи от управлявана срещу self-managed услуга и договора. |
| „В Azure няма OpenShift“ | **Невярно:** има **Azure Red Hat OpenShift (ARO)**. |
| OpenShift е алтернатива на Kubernetes | OpenShift е интегрирана Kubernetes-базирана дистрибуция и продукт. |
| SDN → OVN задължително причинява downtime | Рискът и допустимият метод се проверяват по конкретна версия, topology и документация. |
| Sandbox терминалът показва „ресурсите на целия клъстер“ | Терминалната среда и quota на потребителя **не** означават административен достъп до всички nodes или гарантиран капацитет. |
| Build complete = приложението е deploy-нато и устойчиво | Трябват отделни checks за rollout, endpoints/Route и persistence. |

## 13. Първа ориентация в Sandbox

**[Red Hat Developer Sandbox](https://developers.redhat.com/developer-sandbox)** е официална **временна**, управлявана тестова среда; към 11.11.2026 Red Hat документира **30 дни**, безплатен Red Hat акаунт и **без кредитна карта**. Достъпът е ограничен и средата може да бъде променена от доставчика.

Кратка ориентация, преди да започнеш пълните упражнения:

1. Прочети официалния [Sandbox FAQ](https://developers.redhat.com/developer-sandbox/FAQ) и провери текущите quota/ограничения.
2. След активиране на sandbox, намери текущия **Project**, **Topology**, **Pods**, **Deployments**, **Routes** и секциите за logs/metrics (менютата зависят от версията и permissions).
3. Ако Web Terminal е достъпен, използвай **read-only** `oc` команди за наблюдение:
   ```bash
   oc whoami
   oc project
   oc get pods
   oc get deployments
   oc get services
   oc get routes
   ```
4. **Очакван резултат:** установяваш собствената си идентичност и текущия проект. Някои списъци могат да са **празни** преди първото deployment; при липса на достъп до Terminal използвай web console.
5. **Troubleshooting:** `Forbidden` означава липсващи права, `Unauthorized` — липсваща/изтекла автентикация, `no resources found` — липсващи обекти, не задължително проблем с клъстера.
6. **Cleanup:** няма създадени ресурси; не трий чужди или предварително предоставени sandbox обекти.

За изграждане и публикуване на реално приложение продължи с [Lab 09-B: Builds, Services и Routes](./labs/LAB-02-DEPLOY-BUILDS-ROUTES-2026.md).

## 14. Самопроверка

1. Каква е разликата между Kubernetes и OpenShift?
2. Ако имаш `Dockerfile`, задължително ли е node runtime да е Docker Engine?
3. С какво Projects и Namespaces си приличат?
4. Защо зеленият Build #1 не е достатъчен, за да заявим, че приложението е здраво и устойчиво?
5. Какво правят Service и Route?
6. Защо не можем да твърдим, че sample приложението ще съхрани данни без storage/DB?
7. Какво различава AKS от ARO и EKS от ROSA?
8. Защо snapshot на etcd не е равнозначен на backup на PostgreSQL данните?
9. Защо HPA, PDB, probes и update strategy се настройват, а не се приемат като магическа гаранция?
10. Защо OpenShift трябва да се учи в **отделна среда**, а не като addon към вече изградения kubeadm/Calico lab?

**Отговори накратко:** 1) OpenShift е Kubernetes-базирана платформа. 2) Не — Kubernetes и OpenShift използват CRI съвместим runtime, например CRI-O. 3) Project е OpenShift представяне на namespace. 4) Build не доказва readiness, Service endpoints или persistence. 5) Service насочва към Pods; Route публикува Service. 6) Без persistent backing store няма гарантирано съхранение. 7) AKS/EKS са управлявани Kubernetes услуги, ARO/ROSA — управлявани OpenShift. 8) etcd пази cluster state, не DB съдържанието. 9) HPA/PDB/probes/strategy изискват коректна конфигурация и не покриват всички откази. 10) OpenShift се инсталира и управлява като отделна дистрибуция, а не като addon върху произволен kubeadm клъстер.

## Източници и следващо обучение

Учебните илюстрации са трите слайда от [уводната видеолекция](https://www.youtube.com/watch?v=soQ8B6f_0w4), а техническите уточнения са съпоставени с [документацията на Red Hat OpenShift](https://docs.redhat.com/en/documentation/openshift_container_platform/) и [Kubernetes](https://kubernetes.io/docs/home/).

**Практически упражнения:** [09-A–09-E](./labs/README.md) · **Официални материали:** [Red Hat Foundations](https://developers.redhat.com/learn/openshift/foundations-openshift), [Kubernetes with Sandbox](https://developers.redhat.com/learn/openshift/learn-kubernetes-using-developer-sandbox), [Virtualization & Modernization](https://developers.redhat.com/learn/openshift/openshift-virtualization-and-application-modernization-using-developer-sandbox).
