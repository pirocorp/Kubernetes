# Lab 09-A — Red Hat Developer Sandbox, Web Console, Projects и oc CLI (2026)

> **Тип:** изпълнимо, самодостатъчно упражнение · **Трудност:** начало · **Не изисква cluster-admin**.
>
> **Оригинални Red Hat уроци:** [Foundations of OpenShift](https://developers.redhat.com/learn/openshift/foundations-openshift) — [OpenShift and Developer Sandbox](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:openshift-and-developer-sandbox), [Overview of Web Console](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:overview-web-console) и [Web Console Terminal](https://developers.redhat.com/learning/learn:openshift:foundations-openshift/resource/resources:use-terminal-window-within-red-hat-openshift-web-console). Допълнително: [Red Hat Developer Sandbox FAQ](https://developers.redhat.com/developer-sandbox/FAQ).
>
> **Проверка:** статичен review (11.11.2026); **не** е извършен реален sandbox run. Менютата и наличните права могат да се различават според версията. Това упражнение НЕ предполага Kubernetes 1.37 от основния kubeadm курс.

## 1. Цел и резултат

След изпълнение трябва да можеш сам да посочиш връзката `OpenShift Project ≈ Kubernetes Namespace`, да използваш едни и същи Kubernetes API обекти през Web Console и `oc`, да разпознаваш `Forbidden` от `Unauthorized`, да виждаш своите ресурси **без** cluster-admin и да излезеш без промяна на съществуващия kubeconfig.

## 2. Предпоставки и избрана среда

- Съвременен Chrome/Firefox/Edge и [Red Hat Developer account](https://developers.redhat.com/developer-sandbox); Sandbox е безплатен **30-дневен**, споделен, с **ограничен обхват**. При активация може да се изисква телефонна проверка; няма кредитна карта. Няма гаранция за определен Kubernetes/OpenShift minor version в hosted Sandbox.
- За **път A (препоръчван)**: локален `oc`, инсталиран от **? → Command line tools / Download oc** в самата OpenShift конзола; терминал с Bash, `curl` (незадължително); `kubectl` е опционален.
- За **път B:** вграден OpenShift Web Terminal, **ако е разрешен** в твоя sandbox. Неговият workspace/контейнер е отделен от локалната ОС.
- Права в твоя предварително предоставен Sandbox Project (обикновено завършва на `-dev`). **Не** създавай сам нов Project, не опитвай `oc adm` или `oc get nodes -A` като условие за успех.
- **Няма нужда да инсталираш Calico, containerd, kubeadm или собствен OpenShift.** Това е друг cluster с друг lifecycle.

**Важни ограничения:** според актуалния [FAQ](https://developers.redhat.com/developer-sandbox/FAQ) sandbox Pods могат да бъдат премахнати след 12 часа непрекъснато изпълнение; Linux VM спират след 1 час. Това упражнение не разчита на дълго работещи ресурси.

## 3. Път A — влизане със защитен локален kubeconfig

**Използвай Bash на своя компютър**; ако работиш само през Web Terminal, премини към т. 4. Командите по-долу са за Bash (Linux/macOS/WSL/Git Bash), не за PowerShell.

1. В браузъра: отвори [Developer Sandbox](https://developers.redhat.com/developer-sandbox) → **Start your sandbox** → избери **OpenShift** → отвори **Web Console**. Запиши **API server URL** от конзолата (обичайно от **Copy login command**); не копирай/commit-вай token.
2. От страницата на Red Hat инсталирай `oc` за съответната ОС/архитектура. Провери:

   ```bash
   oc version --client
   oc login --help | grep -- --web
   ```

   **Очаквано:** версия на `oc` и наличен `--web` флаг. Ако флагът липсва, изтегли по-нов `oc` от конзолата; не преминавай към стар token-in-history login.

3. Изолирай напълно този lab от собствените Kubernetes contexts:

   ```bash
   export OPENSHIFT_LAB_KCFG_DIR="$(mktemp -d)"
   chmod 700 "$OPENSHIFT_LAB_KCFG_DIR"
   export KUBECONFIG="$OPENSHIFT_LAB_KCFG_DIR/config"
   test ! -e "$KUBECONFIG" && echo "Isolated kubeconfig prepared"
   ```

4. Вместо да пишеш secret в command line, изпълни (замени **само** примерния API server адрес с този от конзолата):

   ```bash
   oc login https://api.YOUR-SANDBOX.example:6443 --web
   ```

   Това отваря браузърния authentication flow; има **локален HTTP callback listener**. Използвай **лична**, не споделена машина и затвори login процеса след завършване. Ако Sandbox identity provider не позволява browser login, спри и използвай **път B** от конзолата; не поставяй access token в repo, screenshots, history или command output.

5. Провери самоличността и контекста:

   ```bash
   oc whoami
   oc config current-context
   oc projects
   oc project
   oc version
   ```

   **Очаквано:** собствен login, валиден context, списък от достъпните Projects и един текущ Project. Ако липсва текущ Project, избери **само** предоставения ти чрез `oc project ИМЕ_НА_ТВОЯ_PROJECT`. **Не** изписвай парола, token, kubeconfig или съдържанието на `oc whoami -t`.

## 4. Път B — само през Web Console

1. В Developer/Administrator perspective (наличните менюта зависят от версията) отвори **Project** selector и избери своя предоставен project.
2. Отвори **Topology / Workloads / Pods / Deployments / Services / Routes**. В чиста среда списъците може да са празни — това е нормално.
3. Ако има **Web Terminal** (икона `>_` или terminal plugin), стартирай го и изпълни:

   ```bash
   oc whoami
   oc project
   oc get pods
   oc get deployment,svc,route
   ```

4. Ако Web Terminal **липсва**, **не** инсталирай непознат оператор заради това упражнение. Достатъчни са конзолата и път A или само UI наблюденията. Не е нужен специален debug Pod.

## 5. Общи проверки — Project, RBAC и API

Всички команди се изпълняват в текущия Sandbox Project:

```bash
oc project -q
oc get pods
oc get deployments
oc get services
oc get routes.route.openshift.io
oc get events --sort-by=.lastTimestamp
oc auth can-i get pods
oc auth can-i create deployments
oc auth can-i create routes.route.openshift.io
oc api-resources --namespaced=true | grep -E '^(pods|deployments|routes)[[:space:]]'
oc explain deployment.spec.replicas
oc explain route.spec.to
```

**Очаквани резултати:**
- `oc get` връща списък или `No resources found`, не се изискват налични apps.
- `oc auth can-i` показва `yes/no`, но никъде не приемаме гарантирани права за създаване на всеки ресурс.
- `oc explain` потвърждава, че `Deployment` е стандартен Kubernetes API, а `Route` е OpenShift-specific API extension.

**За сравнение с Kubernetes** (ако имаш `kubectl` инсталиран и същия `KUBECONFIG`):

```bash
kubectl get pods
oc get pods
kubectl get namespaces
oc projects
```

Двата първи списъка трябва да отразяват един и същ namespace, но `kubectl get namespaces` може да върне `Forbidden`, защото изброяването на всички namespaces е cluster-scoped. `oc projects` е по-подходящо за обикновения OpenShift потребител.

## 6. Грешки, диагностика и възстановяване

| Симптом | Какво означава | Проверка/решение |
|---|---|---|
| `Unauthorized` | Невалидна/изтекла автентикация | Нов browser login; провери дали trial е активен |
| `Forbidden` | RBAC отказ за **конкретна** операция | `oc auth can-i <verb> <resource>`; не ползвай `cluster-admin` |
| `No resources found` | Няма обекти от този тип | Не е грешка при празен проект |
| `the server doesn't have a resource type "routes"` | Грешен cluster/context или липсва Route API | `oc config current-context`; `oc api-resources` |
| `x509: certificate signed by unknown authority` | Липсва валидно доверие на сертификат | Увери се, че използваш официалния API адрес/CA от Sandbox; **не** добавяй `--insecure-skip-tls-verify` |
| `oc: command not found` | `oc` липсва в PATH | Инсталирай CLI от конзолата, съответстващ на клъстера |
| Sandbox trial expired | Trial жизнен цикъл | Запази собствените си публични manifests преди trial end; нова среда може да има различни URLs |

## 7. Cleanup — само на това упражнение

**Не е създаден нито един cluster object.** Ако си ползвал **път A**, излез от OpenShift и премахни *само изолирания файл*, никога стандартния `~/.kube/config`:

```bash
if test -z "${OPENSHIFT_LAB_KCFG_DIR:-}" || test -z "${KUBECONFIG:-}" || \
   test "$KUBECONFIG" != "$OPENSHIFT_LAB_KCFG_DIR/config" || \
   test ! -d "$OPENSHIFT_LAB_KCFG_DIR" || \
   test ! -f "$KUBECONFIG"; then
  echo "Safety guard failed: NOT changing credentials or deleting files" >&2
else
  oc logout
  rm -f -- "$KUBECONFIG"
  rmdir -- "$OPENSHIFT_LAB_KCFG_DIR"
  unset KUBECONFIG OPENSHIFT_LAB_KCFG_DIR
fi
```

`oc logout` обезсилва текущия контекст/сесия според възможностите на identity provider. При активен Web Terminal затвори само своя терминален session/tab. Не изтривай Project, pods на средата или чужди resources.

## 8. Критерии за успешно упражнение

- [ ] Знаеш OpenShift cluster версията от `oc version`, **без** да приемаш, че съвпада с Kubernetes 1.37.
- [ ] Виждаш своя Project и можеш да изпълниш `oc get pods`.
- [ ] Можеш да покажеш, че `Deployment` е Kubernetes API, а `Route` — OpenShift API.
- [ ] Можеш да диагностицираш `Unauthorized` / `Forbidden` / празен списък.
- [ ] Не си променил първоначалния си `~/.kube/config`, не си публикувал credentials.
- [ ] Няма оставени ресурси/разходи/дълготрайни workloads от този lab.

**Версионни референции:** [официален OpenShift CLI](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/cli_tools/openshift-cli-oc), [Sandbox FAQ](https://developers.redhat.com/developer-sandbox/FAQ). Тук няма остарели основни API-та, а учебните команди са read-only.
