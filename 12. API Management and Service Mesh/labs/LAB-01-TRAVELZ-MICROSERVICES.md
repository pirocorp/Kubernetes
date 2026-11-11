# Lab 12-A — Travelz: microservices и service-to-service комуникация

**Цел:** да изградиш реални ASP.NET Core 10 приложения за Travelz — **Travel Agency v1**, **Travel Agency v2** и **Travel Portal** — и да проследиш заявката от portal към вътрешния service. Това е подготовката за Service Mesh, **без** да твърдим, че локалният HTTP трафик е защитен с mTLS.

**Оригинален източник:** [Red Hat Comprehensive Service Architecture — Travelz](https://www.solutionpatterns.io/solution-pattern-apim-servicemesh/comprehensive-service-architecture/index.html), [Architecture](https://www.solutionpatterns.io/solution-pattern-apim-servicemesh/comprehensive-service-architecture/02-architecture.html).

## 1. Предпоставки и необходими файлове

- Ubuntu/macOS/WSL с Bash, **.NET SDK 10**, Python **3.10+** и curl.
- Нужни са свободни loopback портове **5100, 5101, 5102, 5200, 5300**. Всички се проверяват предварително.
- Изпълнявай командите от **корена на Module 12**, а не от root на Kubernetes repository.
- Файлове: [C# app](../src/Travelz/Program.cs), [project](../src/Travelz/Travelz.csproj), [start.sh](../scripts/start.sh), [stop.sh](../scripts/stop.sh), [verify.py](../tools/verify.py).

```bash
pwd
dotnet --version
python3 --version
python3 tools/keys.py check-ports
test -f src/Travelz/Program.cs
test -f scripts/start.sh
```

**Очаквано:** .NET SDK започва с `10.`, Python >= 3.10, портовете са свободни. Ако портът вече е зает от предишно наше изпълнение, използвай `bash scripts/stop.sh`; **не** спирай чужди процеси.

## 2. Разбери трите роли на едно приложение

Един и същ **ASP.NET Core код** се стартира с различна конфигурация:

| `APP_MODE` | Порт | Основен endpoint | Роля |
|---|---:|---|---|
| `agency-v1` | 5101 | `GET /api/travels/{city}` | Legacy quotes за hotel/flight/car |
| `agency-v2` | 5102 | `GET /api/travels/{city}` | Нова версия с включена застраховка (`insuranceIncluded=true`) |
| `portal` | 5100 | `GET /portal/{city}` | Клиент на Agency service |
| Локален routing simulator | 5200 | `GET /api/travels/{city}` | Обяснява weighted routing; **не е Istio** |
| Partner gateway simulator | 5300 | `GET /partner/travels/{city}` | Обяснява API management; **не е 3scale** |

Защо microservices? Portal и Agency имат различни отговорности, lifecycle и потенциално различни екипи. `Service`/DNS (в Kubernetes) абстрахира Pod адресите. Реалната service-to-service инфраструктура, identity и telemetry се изучават в следващите labs.

## 3. Build и стартиране на всички локални процеси

```bash
bash scripts/start.sh
```

Скриптът **създава .runtime/keys.env с mode 0600**, компилира C# проекта, стартира пет локални процеса, записва собствените им PID файлове/логове и изпълнява `python3 tools/verify.py basic`. Няма Docker, Kubernetes или външна база данни. Ключовете са локални, синтетични и **не се разпечатват**.

**Очаквано:** `PASS health` за петте порта, `PASS agency v1`, `PASS agency v2`, `PASS portal-to-agency correlation` и `PASS partner access denied without credentials`.

## 4. Упражнение с реални HTTP заявки

```bash
curl -fsS http://127.0.0.1:5101/api/travels/Paris
curl -fsS http://127.0.0.1:5102/api/travels/Paris
curl -fsS http://127.0.0.1:5100/portal/Paris
curl -fsS http://127.0.0.1:5100/identity
python3 tools/verify.py basic
```

**Очаквано:** Agency v1 дава `"version":"v1"`, Agency v2 — `"version":"v2"` и `"insuranceIncluded":true`. Portal връща `channel=travel-portal`, `quote` и **един и същ correlationId** от portal до Agency. Синтетичните стойности са в EUR, не са реални оферти.

В локалния пример Portal ходи към routing simulator на :5200, който избира v1/v2. За **истински** Kubernetes cluster DNS и mesh се преминава към Labs 12-D и 12-E.

## 5. Защо това още НЕ е Service Mesh?

Виждаш две приложения и HTTP комуникация, но **няма proxy injection, certificate-based workload identities, mTLS, Istio control plane, Kiali или Jaeger**. `X-Correlation-Id` е **application-level request correlation**, не end-to-end distributed tracing storage. Локалните процеси слушат само на `127.0.0.1`.

Пълният Red Hat pattern добавя именно inter-domain/intra-domain security, observability и routing чрез OpenShift Service Mesh. Не приписвай тези свойства на обикновен HTTP proxy.

## 6. Troubleshooting

| Симптом | Проверка | Корекция |
|---|---|---|
| `dotnet` липсва | `dotnet --info` | Инсталирай .NET 10 SDK |
| Някой порт е зает | `python3 tools/keys.py check-ports` | Спри **собствения** предходен lab с `bash scripts/stop.sh` |
| Startup validation отказва | `cat .runtime/portal.log` или `cat .runtime/agency-v1.log` | Проверка на първата грешка; не стартирай втори набор |
| Portal връща 502 | `cat .runtime/router.log` и `cat .runtime/portal.log` | Провери :5200 и двата Agency ports |
| Correlation ID липсва | `python3 tools/verify.py basic` | Увери се, че използваш нашите source файлове |

## 7. Cleanup

```bash
bash scripts/stop.sh
python3 tools/keys.py check-ports
```

**Очаквано:** скриптът проверява PID/command line и спира само нашите пет процеса, портовете стават свободни. Логовете и ключовете остават под `.runtime/` за повторение и диагностика. Когато приключиш **всички** локални labs и след проверка на текущата директория, можеш да изтриеш само `.runtime/keys.env`.

**Приемане:** успешна C# компилация, пет локални health endpoints, две Agency версии и Portal → Agency correlation.