#!/usr/bin/env python3

# -*- coding: utf-8 -*-


"""

GOIDA VPN Config Aggregator & Filter v4.0

Объединённый скрипт: агрегация + TCP/ICMP пинг + автообновление GitHub

Автор: для goida-vpn-configs

"""

from requests.adapters import HTTPAdapter

from urllib3.util.retry import Retry

from collections import defaultdict

from github import GithubException

from github import Github, Auth

from datetime import datetime

import concurrent.futures

import urllib.parse

import threading

import zoneinfo

import requests

import urllib3

import socket

import base64

import html

import json

import time

import re

import os

# ==================== НАСТРОЙКИ ====================

# GitHub настройки

GITHUB_TOKEN = os.environ.get("MY_TOKEN")

REPO_NAME = os.environ.get("REPO_NAME", "SEDiK-Bes/goida-vpn-configs")

# Параметры фильтрации

ENABLE_TCP_CHECK = True # TCP-пинг (обязательно для качества)

ENABLE_ICMP_CHECK = False # ICMP-пинг (опционально, требует icmplib)

MAX_PING_MS = 300 # Максимальный TCP-пинг в мс

ICMP_THRESHOLD_MS = 200 # Максимальный ICMP-пинг в мс

CONNECTION_TIMEOUT = 2 # Таймаут TCP-подключения

MAX_CONFIGS_PER_FILE = 150 # Топ-N конфигов в каждом файле

# Параллелизм

TCP_WORKERS = 25 # Потоки для TCP-пинга

ICMP_WORKERS = 20 # Потоки для ICMP-пинга

HTTP_WORKERS = 8 # Потоки для скачивания

# Опции

REMOVE_DUPLICATES = True # Удалять дубликаты по host:port

ENABLE_SNI_FILTER = True # Включить SNI-фильтр для 26.txt

VERBOSE_LOGGING = True # Подробное логирование

# ==================== ИСТОЧНИКИ КОНФИГОВ ====================

URLS = [

"https://github.com/sakha1370/OpenRay/raw/refs/heads/main/output/all_valid_proxies.txt",

"https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/protocols/vl.txt",

"https://raw.githubusercontent.com/yitong2333/proxy-minging/refs/heads/main/v2ray.txt",

"https://raw.githubusercontent.com/acymz/AutoVPN/refs/heads/main/data/V2.txt",

"https://raw.githubusercontent.com/miladtahanian/V2RayCFGDumper/refs/heads/main/config.txt",

"https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_RAW.txt",

"https://github.com/Epodonios/v2ray-configs/raw/main/Splitted-By-Protocol/trojan.txt",

"https://raw.githubusercontent.com/YasserDivaR/pr0xy/refs/heads/main/ShadowSocks2021.txt",

"https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/refs/heads/main/category/vless.txt",

"https://raw.githubusercontent.com/mheidari98/.proxy/refs/heads/main/vless",

"https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_iran.txt",

"https://raw.githubusercontent.com/mheidari98/.proxy/refs/heads/main/all",

"https://github.com/Kwinshadow/TelegramV2rayCollector/raw/refs/heads/main/sublinks/mix.txt",

"https://github.com/LalatinaHub/Mineral/raw/refs/heads/master/result/nodes",

"https://raw.githubusercontent.com/miladtahanian/multi-proxy-config-fetcher/refs/heads/main/configs/proxy_configs.txt",

"https://raw.githubusercontent.com/Pawdroid/Free-servers/refs/heads/main/sub",

"https://github.com/MhdiTaheri/V2rayCollector_Py/raw/refs/heads/main/sub/Mix/mix.txt",

"https://github.com/Epodonios/v2ray-configs/raw/main/Splitted-By-Protocol/vmess.txt",

"https://github.com/MhdiTaheri/V2rayCollector/raw/refs/heads/main/sub/mix",

"https://github.com/Argh94/Proxy-List/raw/refs/heads/main/All_Config.txt",

"https://raw.githubusercontent.com/shabane/kamaji/master/hub/merged.txt",

"https://raw.githubusercontent.com/wuqb2i4f/xray-config-toolkit/main/output/base64/mix-uri",

"https://raw.githubusercontent.com/AzadNetCH/Clash/refs/heads/main/AzadNet.txt",

"https://raw.githubusercontent.com/STR97/STRUGOV/refs/heads/main/STR.BYPASS#STR.BYPASS%F0%9F%91%BE",

"https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/refs/heads/main/Config/vless.txt",



# Дополнительные источники для 26.txt (SNI whitelist bypass)

]

EXTRA_URLS_FOR_26 = [

"https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Cable.txt",

"https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",

"https://raw.githubusercontent.com/zieng2/wl/main/vless.txt",

"https://raw.githubusercontent.com/zieng2/wl/refs/heads/main/vless_universal.txt",

"https://raw.githubusercontent.com/zieng2/wl/main/vless_lite.txt",

"https://raw.githubusercontent.com/zieng2/wl/refs/heads/main/vless_nolite.txt",

"https://raw.githubusercontent.com/EtoNeYaProject/etoneyaproject.github.io/refs/heads/main/2",

"https://s3c3.001.gpucloud.ru/dixsm/htxml",

]

# SNI домены для white-list фильтра (26.txt)

SNI_WHITELIST_DOMAINS = [

"avito.ru", "avito.st", "ok.ru", "vk.com", "vk.ru", "mail.ru", "yandex.ru", "yandex.com",

"gosuslugi.ru", "sberbank.ru", "alfabank.ru", "tbank.ru", "ozon.ru", "wildberries.ru",

"2gis.com", "2gis.ru", "hh.ru", "drom.ru", "kinopoisk.ru", "rutube.ru", "dzen.ru",

]

# ==================== СЛУЖЕБНЫЕ ПЕРЕМЕННЫЕ ====================

LOGS_BY_FILE = defaultdict(list)

_LOG_LOCK = threading.Lock()

_UPDATED_FILES_LOCK = threading.Lock()

_GITHUBMIRROR_INDEX_RE = re.compile(r"githubmirror/(\d+)\.txt")

updated_files = set()

REMOTE_PATHS = [f"githubmirror/{i+1}.txt" for i in range(len(URLS))]

LOCAL_PATHS = [f"githubmirror/{i+1}.txt" for i in range(len(URLS))]

REMOTE_PATHS.append("githubmirror/26.txt")

LOCAL_PATHS.append("githubmirror/26.txt")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CHROME_UA = (

"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "

"AppleWebKit/537.36 (KHTML, like Gecko) "

"Chrome/138.0.0.0 Safari/537.36"

)

INSECURE_PATTERN = re.compile(

r'(?:[?&;]|3%[Bb])(allowinsecure|allow_insecure|insecure)=(?:1|true|yes)(?:[&;#]|$|(?=\s|$))',

re.IGNORECASE

)

# ==================== ЛОГИРОВАНИЕ ====================

def _extract_index(msg: str) -> int:

m = _GITHUBMIRROR_INDEX_RE.search(msg)

if m:

try:

return int(m.group(1))

except ValueError:

pass

return 0

def log(message: str):

idx = _extract_index(message)

with _LOG_LOCK:

LOGS_BY_FILE[idx].append(message)

# ==================== GITHUB ПОДКЛЮЧЕНИЕ ====================

zone = zoneinfo.ZoneInfo("Europe/Moscow")

thistime = datetime.now(zone)

offset = thistime.strftime("%H:%M | %d.%m.%Y")

if GITHUB_TOKEN:

g = Github(auth=Auth.Token(GITHUB_TOKEN))

else:

g = Github()

REPO = g.get_repo(REPO_NAME)

try:

remaining, limit = g.rate_limiting

if remaining < 100:

log(f"⚠️ Внимание: осталось {remaining}/{limit} запросов к GitHub API")

else:

log(f"ℹ️ Доступно запросов к GitHub API: {remaining}/{limit}")

except Exception as e:

log(f"⚠️ Не удалось проверить лимиты GitHub API: {e}")

if not os.path.exists("githubmirror"):

os.mkdir("githubmirror")

# ==================== HTTP СЕССИЯ ====================

def _build_session(max_pool_size: int) -> requests.Session:

session = requests.Session()

adapter = HTTPAdapter(

pool_connections=max_pool_size,

pool_maxsize=max_pool_size,

max_retries=Retry(

total=2,

backoff_factor=0.3,

status_forcelist=(429, 500, 502, 503, 504),

allowed_methods=("HEAD", "GET", "OPTIONS"),

),

)

session.mount("http://", adapter)

session.mount("https://", adapter)

session.headers.update({"User-Agent": CHROME_UA})

return session

REQUESTS_SESSION = _build_session(max_pool_size=max(HTTP_WORKERS, len(URLS)))

# ==================== СКАЧИВАНИЕ ====================

def fetch_data(url: str, timeout: int = 15, max_attempts: int = 3) -> str:

for attempt in range(1, max_attempts + 1):

try:

modified_url = url

verify = True

if attempt == 2:

verify = False

elif attempt == 3:

parsed = urllib.parse.urlparse(url)

if parsed.scheme == "https":

modified_url = parsed._replace(scheme="http").geturl()

verify = False

response = REQUESTS_SESSION.get(modified_url, timeout=timeout, verify=verify)

response.raise_for_status()

return response.text

except requests.exceptions.RequestException as exc:

if attempt < max_attempts:

continue

raise exc

# ==================== ПАРСИНГ HOST:PORT ====================

def extract_host_port_from_config(config_line: str):

"""Извлекает host и port из конфига"""

try:

config_line = config_line.strip()

# VMess (JSON в base64)

if config_line.startswith('vmess://'):

try:

payload = config_line[8:]

rem = len(payload) % 4

if rem:

payload += '=' * (4 - rem)

decoded = base64.b64decode(payload).decode('utf-8', errors='ignore')

if decoded.startswith('{'):

j = json.loads(decoded)

host = j.get('add') or j.get('host') or j.get('ip')

port = j.get('port')

if host and port:

return str(host), int(port)

except:

pass

# VLESS, Trojan, SS - формат: protocol://[user@]host:port[params]

match = re.search(r'(?:@|//)([\\w\\.-]+):(\\d{1,5})', config_line)

if match:

return match.group(1), int(match.group(2))

except:

pass

return None, None

# ==================== TCP ПИНГ ====================

def check_tcp_availability(host: str, port: int, timeout: float = CONNECTION_TIMEOUT) -> int:

"""TCP-пинг: возвращает время отклика в мс или -1"""

try:

start_time = time.time()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.settimeout(timeout)

result = sock.connect_ex((host, port))

sock.close()

if result == 0:

elapsed = (time.time() - start_time) * 1000

return int(elapsed)

else:

return -1

except:

return -1

def test_single_config_tcp(config_line: str) -> tuple:

"""Тестирует конфиг через TCP"""

host, port = extract_host_port_from_config(config_line)

if not host or not port:

return (config_line, -1, None, None)

ping_ms = check_tcp_availability(host, port)

return (config_line, ping_ms, host, port)

# ==================== ICMP ПИНГ (ОПЦИОНАЛЬНО) ====================

if ENABLE_ICMP_CHECK:

try:

from icmplib import ping as icmp_ping_sync

ICMP_AVAILABLE = True

except ImportError:

log("⚠️ icmplib не установлен. ICMP-пинг отключён. Установите: pip install icmplib")

ICMP_AVAILABLE = False

ENABLE_ICMP_CHECK = False

else:

ICMP_AVAILABLE = False

def check_icmp_ping(host: str) -> float:

"""ICMP-пинг: возвращает средний RTT в мс или 9999.0"""

if not ICMP_AVAILABLE:

return 0.0

try:

result = icmp_ping_sync(host, count=2, timeout=1.5, privileged=False)

if not result.is_alive:

return 9999.0

return float(result.avg_rtt)

except:

return 9999.0

# ==================== ФИЛЬТРАЦИЯ И СОРТИРОВКА ====================

def filter_insecure_configs(data: str) -> tuple:

"""Удаляет конфиги с allowinsecure=true"""

result = []

splitted = data.splitlines()

for line in splitted:

original_line = line

processed = line.strip()

processed = urllib.parse.unquote(html.unescape(processed))

if INSECURE_PATTERN.search(processed):

continue

result.append(original_line)

filtered_count = len(splitted) - len(result)

return "\\n".join(result), filtered_count

def filter_and_sort_best_configs(configs: list, local_path: str) -> list:

"""Фильтрует и сортирует конфиги по TCP-пингу"""

if not ENABLE_TCP_CHECK or not configs:

return configs

log(f"🔍 TCP-проверка {len(configs)} конфигов для {local_path}...")

# TCP-тест параллельно

tested_configs = []

with concurrent.futures.ThreadPoolExecutor(max_workers=TCP_WORKERS) as executor:

futures = [executor.submit(test_single_config_tcp, cfg) for cfg in configs]

for future in concurrent.futures.as_completed(futures):

tested_configs.append(future.result())

# Фильтруем: только доступные и быстрые

available = [(cfg, ping, host, port) for cfg, ping, host, port in tested_configs

if 0 < ping <= MAX_PING_MS]

# ICMP-пинг (опционально)

if ENABLE_ICMP_CHECK and ICMP_AVAILABLE and available:

log(f"🌐 ICMP-проверка {len(available)} конфигов...")

def icmp_test(item):

cfg, tcp_ping, host, port = item

icmp_rtt = check_icmp_ping(host) if host else 9999.0

return (cfg, tcp_ping, icmp_rtt)

with concurrent.futures.ThreadPoolExecutor(max_workers=ICMP_WORKERS) as executor:

icmp_results = list(executor.map(icmp_test, available))

# Фильтруем по ICMP

available = [(cfg, tcp_ping, icmp_rtt) for cfg, tcp_ping, icmp_rtt in icmp_results

if icmp_rtt <= ICMP_THRESHOLD_MS]

# Сортируем по комбинированному пингу

available.sort(key=lambda x: (x[2], x[1])) # сначала ICMP, потом TCP

best_configs = [cfg for cfg, _, _ in available[:MAX_CONFIGS_PER_FILE]]

if available and VERBOSE_LOGGING:

avg_icmp = sum(x[2] for x in available[:len(best_configs)]) / len(best_configs)

log(f"📊 ICMP: средний={int(avg_icmp)}ms, отобрано={len(best_configs)}")

else:

# Сортируем только по TCP

available.sort(key=lambda x: x[1])

best_configs = [cfg for cfg, _, _, _ in available[:MAX_CONFIGS_PER_FILE]]

filtered_count = len(configs) - len(best_configs)

if filtered_count > 0 and VERBOSE_LOGGING:

log(f"✅ Отобрано {len(best_configs)} лучших (отфильтровано {filtered_count})")

if available:

pings = [x[1] for x in available[:len(best_configs)]]

log(f"📊 TCP пинг: мин={min(pings)}ms, макс={max(pings)}ms, средний={int(sum(pings)/len(pings))}ms")

else:

if not best_configs:

log(f"⚠️ Все конфиги недоступны или медленные для {local_path}")

return best_configs

def deduplicate_configs(configs: list) -> list:

"""Удаляет дубликаты по host:port и полной строке"""

if not REMOVE_DUPLICATES:

return configs

seen_full = set()

seen_hostport = set()

unique = []

for cfg in configs:

c = cfg.strip()

if not c or c in seen_full:

continue

seen_full.add(c)

host, port = extract_host_port_from_config(c)

if host and port:

key = f"{host.lower()}:{port}"

if key in seen_hostport:

continue

seen_hostport.add(key)

unique.append(c)

removed = len(configs) - len(unique)

if removed > 0 and VERBOSE_LOGGING:

log(f"🔄 Удалено {removed} дубликатов")

return unique

# ==================== РАБОТА С ФАЙЛАМИ ====================

def save_to_local_file(path, content):

with open(path, "w", encoding="utf-8") as file:

file.write(content)

log(f"📁 Сохранено локально: {path}")

def extract_source_name(url: str) -> str:

try:

parsed = urllib.parse.urlparse(url)

path_parts = parsed.path.split('/')

if len(path_parts) > 2:

return f"{path_parts[1]}/{path_parts[2]}"

return parsed.netloc

except:

return "Источник"

def process_url(url: str, output_path: str):

"""Скачивает, фильтрует и сохраняет конфиги"""

try:

log(f"⬇️ Скачиваю {extract_source_name(url)}...")

data = fetch_data(url)

filtered, removed = filter_insecure_configs(data)

configs = [c.strip() for c in filtered.splitlines() if c.strip()]

log(f"📥 Получено {len(configs)} конфигов (удалено {removed})")

configs = deduplicate_configs(configs)

configs = filter_and_sort_best_configs(configs, output_path)

save_to_local_file(output_path, "\\n".join(configs))

with _UPDATED_FILES_LOCK:

updated_files.add(output_path)

except Exception as e:

log(f"❌ Ошибка обработки {extract_source_name(url)}: {e}")

def process_all():

"""Обрабатывает все источники параллельно"""

log(f"🚀 Начало обработки {len(URLS)} источников в {offset}...")

with concurrent.futures.ThreadPoolExecutor(max_workers=HTTP_WORKERS) as executor:

futures = [executor.submit(process_url, URLS[i], LOCAL_PATHS[i]) for i in range(len(URLS))]

for future in concurrent.futures.as_completed(futures):

try:

future.result()

except Exception as e:

log(f"⚠️ Ошибка в потоке: {e}")

# Файл 26 (SNI-фильтр для Русских белых листов)

if ENABLE_SNI_FILTER:

try:

log("🛡️ Обработка 26.txt (SNI white-list bypass)...")

sni_configs = []

for url in EXTRA_URLS_FOR_26:

try:

data = fetch_data(url)

filtered, _ = filter_insecure_configs(data)

sni_configs.extend([c.strip() for c in filtered.splitlines() if c.strip()])

except Exception as e:

log(f"⚠️ Ошибка при скачивании SNI-источника: {e}")

sni_configs = deduplicate_configs(sni_configs)

sni_configs = filter_and_sort_best_configs(sni_configs, "githubmirror/26.txt")

save_to_local_file("githubmirror/26.txt", "\\n".join(sni_configs))

with _UPDATED_FILES_LOCK:

updated_files.add("githubmirror/26.txt")

log(f"✅ 26.txt готов ({len(sni_configs)} конфигов)")

except Exception as e:

log(f"❌ Ошибка при обработке 26.txt: {e}")

# ==================== СОЗДАНИЕ СВОДНОГО ALL.TXT ====================

def build_all_txt():

"""Объединяет все txt из githubmirror в один all.txt"""

try:

base_dir = "githubmirror"

all_path = os.path.join(base_dir, "all.txt")

if not os.path.exists(base_dir):

log(f"⚠️ Папка {base_dir} не найдена, all.txt не создан")

return

all_lines = []

# Берём все txt файлы (1.txt, 2.txt, ..., 26.txt), кроме all.txt

for filename in sorted(os.listdir(base_dir)):

if filename.lower() == "all.txt" or not filename.endswith(".txt"):

continue

txt_path = os.path.join(base_dir, filename)

try:

with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:

for line in f:

line = line.strip()

# Берём только строки с ссылками

if line and (line.startswith("vmess://")

or line.startswith("vless://")

or line.startswith("trojan://")

or line.startswith("ss://")

or line.startswith("ssr://")

or line.startswith("http")

or line.startswith("socks")):

all_lines.append(line)

except Exception as e:

log(f"⚠️ Не удалось прочитать {filename}: {e}")

# Удаляем дубли, сохраняем порядок

seen = set()

unique_lines = []

for line in all_lines:

if line not in seen:

seen.add(line)

unique_lines.append(line)

# Сохраняем all.txt

with open(all_path, "w", encoding="utf-8") as f:

for line in unique_lines:

f.write(line + "\\n")

log(f"✨ Сформирован {all_path} с {len(unique_lines)} уникальными ссылками")

with _UPDATED_FILES_LOCK:

updated_files.add(all_path)

except Exception as e:

log(f"❌ Ошибка при создании all.txt: {e}")

# ==================== ЗАГРУЗКА НА GITHUB ====================

def push_to_github():

"""Загружает обновлённые файлы на GitHub"""

log("📤 Подготовка к загрузке на GitHub...")

try:

for local_path in updated_files:

try:

with open(local_path, "r", encoding="utf-8") as f:

content = f.read()

try:

file_obj = REPO.get_contents(local_path)

REPO.update_file(local_path, f"Обновление {local_path}", content, file_obj.sha)

log(f"✅ Обновлён {local_path}")

except GithubException as e:

if e.status == 404:

REPO.create_file(local_path, f"Создание {local_path}", content)

log(f"✅ Создан {local_path}")

else:

raise

except Exception as e:

log(f"❌ Ошибка загрузки {local_path}: {e}")

except Exception as e:

log(f"❌ Ошибка при загрузке на GitHub: {e}")

# ==================== ЛОГИРОВАНИЕ РЕЗУЛЬТАТОВ ====================

def save_logs():

"""Сохраняет логи по файлам"""

try:

for idx, messages in LOGS_BY_FILE.items():

filename = f"githubmirror/{idx}.txt" if idx > 0 else "all"

with _LOG_LOCK:

print(f"\\n{'='*60}")

print(f"📊 {filename}:")

print('='*60)

for msg in messages:

print(msg)

except Exception as e:

print(f"❌ Ошибка сохранения логов: {e}")

# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================

def main():

"""Главная функция"""

try:

process_all()

build_all_txt()  # ← ВСТАВЛЯЕМ СОЗДАНИЕ СВОДНОГО ФАЙЛА

push_to_github()

except Exception as e:

log(f"❌ Критическая ошибка: {e}")

finally:

save_logs()

if __name__ == "__main__":

main()
