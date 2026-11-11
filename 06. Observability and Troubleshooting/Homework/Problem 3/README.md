# PersistentVolume reclaim policy — Exercise 3

В [Step 5 - Apply pvss.yaml](./Step%205%20-%20Apply%20pvss.yaml) политиката за четирите статични NFS PersistentVolumes е променена от `Recycle` на `Retain`, защото `Recycle` е deprecated в Kubernetes.

| Поведение | Старо: `Recycle` | Ново: `Retain` |
|---|---|---|
| Изтриваш PVC | Стартира автоматично рециклиране | PV преминава в `Released` |
| Данните върху NFS | Опитва да ги изтрие | Запазват се |
| Автоматично повторно използване | Да, при успешно рециклиране | Не |
| Необходима ръчна намеса | Обикновено не | Да |
| Риск от загуба на данни | По-висок | По-нисък |
| Поддръжка | Deprecated | Поддържана политика |

**Важно:** С `Retain` пазим данните, но поемаме ръчното управление на повторното използване. Политиката `Retain` на PV влиза в действие чак когато съответният PVC действително бъде изтрит. Самото изтриване на StatefulSet не означава непременно изтриване на PVC.

Източник: [Kubernetes — Reclaiming PersistentVolumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#reclaiming).


> **NOTE (2026) — complete lab:** Use [Module 06 LAB-2026.md](../../LAB-2026.md#3-scenario-4--nfs-backed-statefulset-with-4-replicas) for NFS server/client setup, commands, verification and cleanup. The historical screenshots disagree: Step 1 lists three NFS exports, whereas Step 3.1 and the actual four-PV manifest require **all four** `k8spva`, `k8spvb`, `k8spvc` and **`k8spvd`**. Ensure all exist before creating the StatefulSet.
