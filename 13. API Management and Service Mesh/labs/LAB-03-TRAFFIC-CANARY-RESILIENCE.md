# Lab 12-C — East–West: canary routing, fallback и observability

**Цел:** да разбереш как мрежовият слой може да разпределя вътрешния service-to-service трафик и да реагира на отказ, без да променя Portal source code. Оригинал: [Red Hat — Service Mesh Traffic Management, Kiali and Canary](https://www.solutionpatterns.io/solution-pattern-apim-servicemesh/comprehensive-service-architecture/03-demo.html).

**Това упражнение използва `tools/mesh_sim.py` като локален routing simulator. Той НЕ е реален Istio sidecar или Service Mesh.** Истинските `VirtualService`, `DestinationRule` и mTLS policies се изпълняват в [Lab 12-E](./LAB-05-REAL-ISTIO-MESH.md).

## 1. Предпоставки и start

Нужни са .NET SDK 10, Python 3.10+, Bash и същите пет локални порта. Корен на Module 12:

```bash
bash scripts/stop.sh
bash scripts/start.sh
python3 tools/verify.py basic
```

**Очаквано:** всички услуги са Healthy; `http://127.0.0.1:5200` маршрутизира Agency заявки. Няма нужда от OpenShift/cluster-admin за тази част.

## 2. Weighted traffic splitting — 80% v1 / 20% v2

Simulator избира **всяка пета GET заявка** към v2, останалите към v1. Това е умишлено **детерминистично** упражнение за ясно измерване; в реален mesh weight е статистическа политика и 20 заявки не гарантират точни 16/4.

```bash
python3 tools/verify.py canary
curl -fsS http://127.0.0.1:5200/_stats
python3 tools/mesh_sample.py --base-url http://127.0.0.1:5100 --count 20
```

**Очаквано:** `PASS deterministic local 80/20 demonstration: v1=16, v2=4`. С `mesh_sample.py` виждаш кои версии достига самото Portal приложение. `_stats` показва броя избрани backend версии, не Kiali/Prometheus telemetry.

**В реален Istio** `VirtualService` избира `DestinationRule` subset `v1` или `v2`; Envoy sidecars прилагат policy без change на business код. Примерът е включен в [mesh/canary-80-20.yaml](../mesh/canary-80-20.yaml).

## 3. Resilience — симулиран отказ на v2

В примерния C# код `agency-v2` връща **503 само за град `Failover`**. Router прави **един повторен GET към v1**, когато предварително избраният backend е v2 и получи 503.

```bash
python3 tools/verify.py fallback
curl -fsS http://127.0.0.1:5200/_stats
```

**Очаквано:** пет заявки `Failover`, едно v2 503, един retry към v1 и накрая `PASS one simulated v2 failure recovered by v1 GET retry`. **Retry на POST/booking/payment операции не е безопасен без idempotency policy**; тук сме ограничили операцията до GET.

**Не прави неправилния извод**, че всеки Istio retry винаги превключва към друга версия. Реалните retry policies зависят от route selection, Envoy clusters, service endpoints и failure type. Няма универсална гаранция за cross-version failover.

## 4. Наблюдение и сигурност

Portal създава собствен `X-Correlation-Id`, който преминава през нашия router и Agency. Провери:

```bash
curl -fsS http://127.0.0.1:5100/portal/Sofia
tail -n 10 .runtime/portal.log
tail -n 10 .runtime/agency-v1.log
tail -n 10 .runtime/agency-v2.log
```

**Очаквано:** синтетична оферта, correlation ID и версия в логовете. Това е **логова корелация**, не end-to-end Jaeger distributed tracing. **Няма mTLS**, SPIFFE identity или zero-trust policies в локалния simulator.

## 5. Разлика между API Management и Service Mesh

| Случай | Основен компонент |
|---|---|
| Red partner надвишава quota | API Management — gateway `429` |
| Portal към Agency без външни credentials | Service Mesh — east-west traffic |
| Canary 80/20 по версия | Istio traffic management |
| Partner self-signup и monetization | 3scale Developer Portal/Plans |
| Pod-to-Pod mTLS/identity | Service Mesh |
| Business contract schemas/OpenAPI | API design/governance |

## 6. Troubleshooting и cleanup

| Проблем | Диагноза | Действие |
|---|---|---|
| Не получаваш 16/4 | Симулаторът може да е стар/тестове успоредно | Изпълни 20 последователни заявки; `_stats` показва разликата |
| `/_stats` е 404 | Объркан порт | Използвай :5200, не :5300 |
| Няма retry | API v2 не е върнал 503, или броят заявки е различен | Използвай точно `python3 tools/verify.py fallback` |
| Portal HTTP 502 | Router или Agency не работят | `cat .runtime/router.log`, `cat .runtime/agency-v1.log` |
| Липсва correlation | API е стартиран с различен код | `bash scripts/stop.sh; bash scripts/start.sh` |

```bash
bash scripts/stop.sh
```

**Приемане:** доказана локална 80/20 демонстрация, един GET fallback и работеща application-level корелация, с точно разграничение от реално Istio.