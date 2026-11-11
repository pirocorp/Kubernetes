# Lab 10-D — API management: authentication, quotas, analytics

**Цел:** отделяме **upstream API** от **gateway**, което контролира достъпа, брои заявките и прилага ограничение. В Red Hat това е ролята на **3scale/APIcast**; тук използваме собствен **локален преподавателски proxy**, който **не** е 3scale.

## Предпоставки

- Работещият ASP.NET Core API от [Lab 10-C](./LAB-03-ASPNET-IMPLEMENTATION.md) на **127.0.0.1:8080**, с `API_KEY` в същия shell.
- Python 3.10+, Bash, `curl`, свободен port **8081**. Няма нужда от OpenShift, 3scale license или cluster-admin.
- Примерният gateway: [tools/gateway.py](../tools/gateway.py).

## 1. Стартирай proxy

В Bash shell, в който е експортиран същият `API_KEY` като при API:

```bash
export ADMIN_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
test "${#API_KEY}" -ge 16
test "${#ADMIN_KEY}" -ge 16
export API_UPSTREAM=http://127.0.0.1:8080
python3 tools/gateway.py
```

Или във фон (същия shell): `python3 tools/gateway.py > /tmp/m10-gateway.log 2>&1 & GATEWAY_PID=$!`. **Не** стартирай две копия на порт 8081.

Gateway и API и двата валидират header `X-Api-Key`. Това е **учебна defense-in-depth схема**; няма потребители, IdP, истински API products или billing.

## 2. Authentication и rate limiting

```bash
curl -sS -o /dev/null -w 'no key -> %{http_code}\n' \
  http://127.0.0.1:8081/v1/products
for i in 1 2 3 4; do
  curl -sS -o /dev/null -w "request $i -> %{http_code}\n" \
    -H "X-Api-Key: $API_KEY" http://127.0.0.1:8081/v1/products
done
```

**Очаквано:** без ключ → **401**, първите три валидни заявки в рамките на 15 секунди → **200**, четвъртата → **429**. Ако ги изпълниш много бавно и прозорецът изтече, повтори непосредствено 4-те заявки; това е **in-memory rolling time-window**. Не подавай произволни production API keys.

## 3. Прочети counters

```bash
curl -fsS -H "X-Admin-Key: $ADMIN_KEY" http://127.0.0.1:8081/_metrics
curl -sS -o /dev/null -w 'metrics without admin key -> %{http_code}\n' \
  http://127.0.0.1:8081/_metrics
```

**Очаквано:** JSON counters с `requests`, `denied`, `limited` и втори отговор 401. Counter-ите се нулират след рестарт; локалната метрика **не** е production audit log.

## 4. Как това се отнася към Red Hat 3scale

| Нашата демонстрация | Enterprise capability с 3scale |
|---|---|
| Един `API_KEY` | Приложения, developer accounts и credentials |
| In-memory лимит 3/15 сек | Application plans, methods, metrics, quotas, configurable policies |
| Прокси с URL на upstream | APIcast gateway и маршрутизация към backend APIs |
| `/_metrics` counters | API analytics, usage reports, developer portal |
| Локален Python процес | Managed/self-managed gateway с lifecycle и интеграции |

Оригинал: [Red Hat API-First Solution Pattern](https://www.solutionpatterns.io/solution-pattern-api-first/api-first/index.html). Референция: [3scale — Getting started / API access policies](https://docs.redhat.com/en/documentation/red_hat_3scale_api_management/2.16/html/getting_started/launching-apis).

**За реална 3scale инсталация** са необходими достъп, лицензи/условия и поддържан OpenShift клъстер с нужните admin права. Не се опитвай да инсталираш 3scale Operator в общ Developer Sandbox. В този lab **не твърдим**, че локалният proxy имплементира production API management. JWT/OIDC, TLS между services, identity federation, distributed rate limits и persistent metrics са отделни enterprise задачи.

## Troubleshooting

`502` → upstream на 8080 не работи; `401` → различен/липсващ ключ; `429` → учебният лимит е достигнат; `Address already in use` → има втори gateway на 8081. **Не** променяй contract response, за да прикриеш gateway проблем.

## Cleanup

Ctrl+C за foreground gateway или `if test -n "${GATEWAY_PID:-}"; then kill "$GATEWAY_PID"; unset GATEWAY_PID; fi`. След упражнението: `unset ADMIN_KEY API_UPSTREAM`; `API_KEY` премахни когато приключиш и Lab 10-E. Няма клъстерни ресурси.

**Критерий:** наблюдавани **401 / 200 / 429** и admin-only метрика; разбираш защо gateway не замества backend security.
