# 📚 README_GITHUB_ACTIONS.md — Полная Документация

**Дата создания:** 10.01.2026 23:49 MSK  
**Версия:** 1.0  
**Статус:** ✅ Полностью актуально  

---

## 📑 ОГЛАВЛЕНИЕ

1. [Обзор](#обзор)
2. [Архитектура](#архитектура)
3. [Workflows](#workflows)
4. [main.py скрипт](#mainpy-скрипт)
5. [Управление и мониторинг](#управление-и-мониторинг)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## 🏢 ОБЗОР

### Что это?

Полная автоматизация обновления VPN конфигов через GitHub Actions.

Система **автоматически**:
- ⏰ Запускается по расписанию (cron-задачи)
- 📥 Скачивает конфиги из 25+ источников
- 🔄 Обрабатывает и очищает данные
- 🚫 Удаляет дубликаты
- 🛡️ Добавляет SNI white-list конфигурации
- 📄 Сохраняет результат в githubmirror/all.txt
- 📤 Коммитит изменения в GitHub
- 🔔 Отправляет логи (опционально)

### Как это работает?

```
┌──────────────────────────────────────────────────────────────────────┐
│         GitHub Actions (Scheduler)              │
│  Запускает workflow по расписанию (cron)        │
└─────────────────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│      main.py (Python скрипт)                    │
│  ├── Скачивает конфиги из источников            │
│  ├── Фильтрует и обрабатывает данные            │
│  ├── Удаляет дубликаты                          │
│  └── Добавляет SNI конфиги                      │
└─────────────────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│    githubmirror/all.txt (Результат)            │
│    Финальный файл со всеми конфигами           │
└─────────────────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│    GitHub Commit                                │
│    Автоматический коммит результатов           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ АРХИТЕКТУРА

### Файловая структура

```
goida-vpn-configs/
├── .github/
│   └── workflows/
│       ├── frequent_update.yml          ← Workflow 1
│       ├── goida.yml                    ← Workflow 2
│       └── update-configs.yml           ← Workflow 3
│
├── main.py                              ← Основной скрипт
├── requirements.txt                     ← Зависимости Python
├── .gitignore                           ← Git исключения
│
├── githubmirror/                        ← Папка с конфигами
│   ├── all.txt                          ← ГЛАВНЫЙ ФАЙЛ
│   ├── 1.txt, 2.txt, ..., 26.txt       ← Отдельные конфиги
│   └── [other files]
│
├── qr-codes/                            ← QR-коды для конфигов
├── source/                              ← Исходные материалы
├── README.md                            ← Основная документация
└── LICENSE                              ← Лицензия
```

### Зависимости

```
requests          - Скачивание конфигов по HTTP
urllib            - URL обработка
json              - Работа с JSON
re                - Regular expressions
os, sys           - Системные операции
```

---

## ⚙️ WORKFLOWS

### Workflow 1: frequent_update.yml

**Назначение:** Частые обновления конфигов

**Расписание:** Определено в файле (обычно 6-12 часов)

**Действие:**
```yaml
name: Frequent Update
on:
  schedule:
    - cron: '0 */6 * * *'    # Каждые 6 часов

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python main.py
      - uses: actions/upload-artifact@v2
        if: failure()
        with:
          name: logs
          path: *.log
```

### Workflow 2: goida.yml

**Назначение:** Основной workflow обновления

**Расписание:** Определено в файле

**Действие:** Запускает основную логику обработки конфигов

### Workflow 3: update-configs.yml

**Назначение:** Дополнительное обновление конфигов

**Расписание:** Определено в файле

**Действие:** Специализированная обработка

---

## 🐍 main.py скрипт

### Что он делает?

#### Шаг 1: Инициализация
```python
# Импорт библиотек
import requests
import json
import re
import os
```

#### Шаг 2: Скачивание конфигов
```python
# Список источников (25+)
sources = [
    'https://github.com/...',
    'https://github.com/...',
    # ... и т.д.
]

# Скачивание каждого источника
for source in sources:
    response = requests.get(source)
    data = response.text
    # Обработка данных
```

#### Шаг 3: Обработка данных
```python
# Удаление дубликатов
configs = set(configs)

# Фильтрация (опционально)
configs = [c for c in configs if is_valid(c)]

# Добавление SNI white-list конфигов
sni_configs = generate_sni_configs(configs)
all_configs = configs + sni_configs
```

#### Шаг 4: Сохранение результата
```python
# Сохранение в файл
with open('githubmirror/all.txt', 'w') as f:
    for config in all_configs:
        f.write(config + '\n')
```

#### Шаг 5: Коммит в GitHub
```bash
# Git команды (внутри workflow)
git config user.name "Auto Update"
git config user.email "bot@github.com"
git add githubmirror/all.txt
git commit -m "Auto-update: $(date)"
git push
```

---

## 👀 УПРАВЛЕНИЕ И МОНИТОРИНГ

### Просмотр статуса

**Способ 1: GitHub Actions UI**
```
GitHub → Repo → Actions → [Workflow Name] → [Latest Run]
```

**Способ 2: API**
```bash
curl -s https://api.github.com/repos/SEDiK-Bes/goida-vpn-configs/actions/runs \
  | jq '.workflow_runs | .[0]'
```

### Проверка логов

1. **Через GitHub UI:**
   - Actions → Workflow → Latest run → Logs

2. **Через CLI:**
   ```bash
   gh run view [run-id] --log
   ```

### Управление расписанием

**Изменить расписание:**
1. Открой `.github/workflows/[name].yml`
2. Найди `schedule:` → `cron:`
3. Отредактируй cron выражение

**Cron синтаксис:**
```
┌─────────────────── минута (0-59)
│ ┌─────────────────── час (0-23)
│ │ ┌─────────────────── день месяца (1-31)
│ │ │ ┌─────────────────── месяц (1-12)
│ │ │ │ ┌─────────────────── день недели (0-7, 0=воскресенье)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

**Примеры:**
```
0 0 * * *     # Каждый день в 00:00
0 * * * *     # Каждый час
0 */6 * * *   # Каждые 6 часов
0 0 * * 0     # Каждый понедельник
*/30 * * * *  # Каждые 30 минут
```

---

## 🐛 TROUBLESHOOTING

### Ошибка 1: Workflow не запускается

**Симптомы:** Нет новых запусков в Actions

**Причины:**
- [ ] GitHub Actions отключены
- [ ] Неправильное расписание
- [ ] Синтаксическая ошибка в .yml

**Решение:**
```bash
# Проверь что Actions включены
Settings → Actions → General → Allow all actions

# Проверь синтаксис YAML
# Используй YAML validator: https://www.yamllint.com/

# Проверь расписание (cron)
# Используй cron validator: https://crontab.guru/
```

### Ошибка 2: Workflow выполняется, но падает

**Симптомы:** Красный крест ❌ в Actions

**Решение:**
1. Посмотри логи workflow
2. Прочитай сообщение об ошибке
3. Исправь проблему в коде
4. Коммитни изменения
5. GitHub Actions подхватит новую версию при следующем запуске

**Частые ошибки:**

```
ModuleNotFoundError: No module named 'X'
→ Добавь в requirements.txt: pip install X

ConnectionError: Failed to fetch URL
→ Проверь доступность источников

PermissionError: Cannot commit
→ Проверь GitHub token в Settings → Secrets
```

### Ошибка 3: Файл all.txt не обновляется

**Проверь:**
- Когда был последний запуск workflow?
- Может быть расписание очень редкое?
- Может быть скрипт падает с ошибкой?

**Решение:**
1. Посмотри размер файла all.txt (не должен быть 0)
2. Посмотри дату последнего обновления
3. Запусти workflow вручную (кнопка "Run workflow")
4. Посмотри логи
5. Если файл совсем пустой → проверь доступность источников
6. Если файл очень маленький → может быть фильтр слишком жёсткий

### Ошибка 4: GitHub token проблема

**Ошибка:**
```
fatal: could not read Username for 'https://github.com':
```

**Решение:**
```yaml
# В workflow файле используй:
- run: git config --global credential.helper store
- run: echo "https://${{ secrets.GITHUB_TOKEN }}@github.com" > ~/.git-credentials
```

---

## ❓ FAQ

### Q: Зачем нужны 3 workflow, если они делают одно и то же?

**A:** Они могут работать с разными расписаниями или проверять разные источники.

### Q: Как часто обновляются конфиги?

**A:** Зависит от `schedule:` в каждом .yml файле. Обычно каждые 6-12 часов.

### Q: Можно ли отключить автоматизацию?

**A:** Да:
1. Удали файлы из `.github/workflows/`
2. ИЛИ измени `on: []` в workflow файле

### Q: Где хранятся логи?

**A:**
- GitHub Actions: Actions → [Workflow] → [Run] → Logs
- Артефакты: Actions → [Run] → Artifacts

### Q: Можно ли запустить workflow вручную?

**A:** Да, если в workflow добавлен триггер `workflow_dispatch`:
```yaml
on:
  schedule:
    - cron: '0 0 * * *'
  workflow_dispatch:  # Добавить эту строку
```

Тогда появится кнопка "Run workflow" в Actions.

### Q: Как добавить новый источник конфигов?

**A:**
1. Открой main.py
2. Найди список источников
3. Добавь новый URL
4. Коммитни

### Q: Что делать если источник перестал работать?

**A:**
1. Проверь есть ли доступ к URL
2. Если источник удалён — удали из main.py
3. Найди новый источник
4. Добавь в список

---

## 📞 ПОДДЕРЖКА

Если что-то не работает:

1. **Посмотри логи** → GitHub Actions → Logs
2. **Прочитай ошибку** → обычно там всё ясно написано
3. **Загугли** → скопируй ошибку в Google
4. **Спроси** → напиши конкретный вопрос

---

**Версия документации:** 1.0  
**Дата обновления:** 10.01.2026 23:49 MSK  
**Статус:** ✅ Актуально