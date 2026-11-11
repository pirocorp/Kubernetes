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
