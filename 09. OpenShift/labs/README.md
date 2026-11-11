# Module 09 — самодостатъчни OpenShift упражнения (2026)

> **Статус:** практическите материали са подготвени в отделни GitHub PR-и и се приемат след **статични проверки**, без твърдение за реално изпълнение на Sandbox/VM. Всяко упражнение съдържа prerequisites, файлове, команди, expected results, troubleshooting и cleanup. **Никой PR не се слива автоматично.**
>
> **Начало:** [Уводни бележки по видеото, транскрипта и Mermaid](../INTRO-2026.md) · [Официални Red Hat обучения — карта на източниците](../REDHAT-LEARNING-PATHS-2026.md) (последният линк ще заработи след сливане на отделния PR с учебната карта).

## Препоръчителна последователност

| № | Практическо упражнение | Какво ще построиш и провериш | Оригинална пътека |
|---|---|---|---|
| **09-A** | [Sandbox, Console и oc](./LAB-01-SANDBOX-CLI-2026.md) | OpenShift Project, isolated KUBECONFIG, RBAC, API discovery, CLI vs UI, cleanup | [Foundations](https://developers.redhat.com/learn/openshift/foundations-openshift) |
| **09-B** | [Deployments, S2I builds, Routes, scaling](./LAB-02-DEPLOY-BUILDS-ROUTES-2026.md) | UBI9 Apache deployment, Python S2I image, Git import, Route, rollback, metrics | [Foundations](https://developers.redhat.com/learn/openshift/foundations-openshift) |
| **09-C** | [MariaDB, Secret, PVC, recovery](./LAB-03-MARIADB-PVC-2026.md) | Учебна база данни, Secret, PersistentVolumeClaim, SQL и Pod recreation | [Foundations Databases](https://developers.redhat.com/learn/openshift/foundations-openshift) |
| **09-D** | [Full stack — Python REST + React + MariaDB](./LAB-04-FULLSTACK-2026.md) | 3-tier app, Service discovery, frontend Route, API, database, resilience | [Kubernetes using Sandbox](https://developers.redhat.com/learn/openshift/learn-kubernetes-using-developer-sandbox) |
| **09-E** | [Virtualization — VM → container cutover](./LAB-05-VIRTUALIZATION-CUTOVER-2026.md) | Legacy Apache VM, virt-launcher labels, Service/Route, container replacement, rollback | [Virtualization & Modernization](https://developers.redhat.com/learn/openshift/openshift-virtualization-and-application-modernization-using-developer-sandbox) |

Трите оригинални Red Hat пътеки, всички техни 18 урока и конкретните референции са описани в [учебната карта](../REDHAT-LEARNING-PATHS-2026.md) и в началото на всеки lab guide. Изходният код и необходимите manifests са под [examples/](./examples/).

## Използвана среда и ограничения

**Основен учебен път:** [Red Hat Developer Sandbox](https://developers.redhat.com/developer-sandbox), в личен Project с разрешените от доставчика Kubernetes/OpenShift операции. Sandbox **не** е домашният Kubernetes 1.37 кластер с kubeadm + Calico.

**Важни външни ограничения:** Sandbox trial и квоти, текуща версия на managed OpenShift, позволени SCC/RBAC permissions, registry/npm/PyPI availability, VM catalog. Според [Sandbox FAQ](https://developers.redhat.com/developer-sandbox/FAQ) Pods могат да бъдат премахнати след 12 часа непрекъснато изпълнение, а Linux VMs се спират след 1 час. Изпълнявай лабовете **по един**, не едновременно.

**Security:** без фиксирани демонстрационни пароли, без публикуване на токени/Secret данни, без изтриване на default kubeconfig, без cluster-admin/SCC bypass. Учебните images използват актуални продуктови *families*, но някои upstream patch tags са подвижни; за production изисквай immutable image digests и реални runtime тестове.

## В кой ред да се сливат PR-ите?

1. **PR #23** — официалните Red Hat източници и roadmap.
2. **PR #24** — 09-A, 09-B и Python sample.
3. **PR #25** — 09-C, 09-D и full-stack source/database.
4. **PR #26** — 09-E, неговите manifests и този индекс (предназначен за последен merge).

Това е **препоръчителен ред**, за да не сочат линковете временно към още несляти файлове. **Не са слети автоматично.** За останалата модернизация на Module 09, пълна версия/OKD стратегия и окончателна интеграция в `COURSE-2026.md` продължаваме **след допълнителните ти материали и окончателния сигнал**.

## Стандарт за проверка

- [ ] Прочетени и налични всички Markdown source links и manifests.
- [ ] Във всеки lab: preflight, заданието, команди, expected outputs, failures и cleanup.
- [ ] Съвместими target ports и labels; стандартни `apps/v1`, `v1` и OpenShift `route.openshift.io/v1` / `build.openshift.io/v1`; VM `kubevirt.io/v1`.
- [ ] Не се твърди runtime успех при липса на реален Sandbox тест.
- [ ] Запазени всички оригинални Red Hat learning URLs.
- [ ] Финална проверка за неизтрити PVCs/Secrets/Routes/VM boot volumes след всеки lab.

**Авторство:** учебната адаптация е оригинална за това репо; Red Hat учебните ресурси са референции и не са копирани дословно.
