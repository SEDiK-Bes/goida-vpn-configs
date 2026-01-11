# HAPP + Yandex Cloud proxy (crypt3)

Цель: чтобы HAPP не ходил напрямую на GitHub (таймауты/блокировки), а получал подписку через нейтральный endpoint в Yandex Cloud.

## 1) Создать Yandex Cloud Function

- Runtime: Python 3.11
- Timeout: 60s
- Memory: 256–512MB
- Код функции: `yandex_function/index.py`
- requirements: `yandex_function/requirements.txt`

### Environment variables (в консоли функции)

```
REMOTE_SOURCE_1=https://github.com/SEDiK-Bes/goida-vpn-configs/raw/refs/heads/main/githubmirror/ec.txt
REMOTE_SOURCE_2=https://github.com/SEDiK-Bes/goida-vpn-configs/raw/refs/heads/main/githubmirror/ru.txt
REMOTE_SOURCE_3=https://github.com/SEDiK-Bes/goida-vpn-configs/raw/refs/heads/main/githubmirror/world.txt
```

После деплоя получите URL вида:

- `https://<id>.serverless.yandexcloud.net`

Проверка (в браузере):

- `https://<id>.serverless.yandexcloud.net?source=set_a`

## 2) Получить happ://crypt3 ссылки

Скрипт `main.py` умеет автоматически запросить шифрование через HAPP Crypto API.

Запуск:

```bash
export MY_TOKEN=ghp_xxx
export YANDEX_PROXY_URL=https://<id>.serverless.yandexcloud.net
python3 main.py
```

Результат будет сохранён локально:

- `happ_crypt3_links.txt`

Файл НЕ пушится в репозиторий намеренно (для приватности).
