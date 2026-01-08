# МОДИФИЦИРОВАННАЯ ВЕРСИЯ main.py С АВТОМАТИЧЕСКОЙ ПРОВЕРКОЙ ПИНГА
# Добавлен функционал проверки доступности серверов и фильтрации по времени отклика
# Автор модификации: для использования с Happ VPN

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

# ================== ПАРАМЕТРЫ ФИЛЬТРАЦИИ (НАСТРОЙТЕ ПОД СЕБЯ) ==================
ENABLE_PING_CHECK = True  # Включить проверку доступности серверов
MAX_PING_MS = 300  # Максимальное время отклика в миллисекундах (300ms = 0.3 сек)
CONNECTION_TIMEOUT = 2  # Таймаут подключения к серверу (в секундах)
MAX_CONFIGS_PER_FILE = 100  # Максимальное количество конфигов в файле (топ-N лучших)
PING_WORKERS = 20  # Количество потоков для проверки пинга

# ================== ОРИГИНАЛЬНЫЙ КОД ==================
LOGS_BY_FILE: dict[int, list[str]] = defaultdict(list)
_LOG_LOCK = threading.Lock()
_UPDATED_FILES_LOCK = threading.Lock()

_GITHUBMIRROR_INDEX_RE = re.compile(r"githubmirror/(\d+)\.txt")
updated_files = set()

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

zone = zoneinfo.ZoneInfo("Europe/Moscow")
thistime = datetime.now(zone)
offset = thistime.strftime("%H:%M | %d.%m.%Y")

GITHUB_TOKEN = os.environ.get("MY_TOKEN")
REPO_NAME = "SEDiK-Bes/goida-vpn-configs"  # <-- ОБЯЗАТЕЛЬНО ИЗМЕНИТЕ НА ВАШЕ ИМЯ РЕПОЗИТОРИЯ!
REPO_NAME
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

DEFAULT_MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "16"))

def _build_session(max_pool_size: int) -> requests.Session:
    session = requests.Session()
    adapter = HTTPAdapter(
        pool_connections=max_pool_size,
        pool_maxsize=max_pool_size,
        max_retries=Retry(
            total=1,
            backoff_factor=0.2,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("HEAD", "GET", "OPTIONS"),
        ),
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": CHROME_UA})
    return session

REQUESTS_SESSION = _build_session(max_pool_size=max(DEFAULT_MAX_WORKERS, len(URLS))) if 'URLS' in globals() else _build_session(DEFAULT_MAX_WORKERS)

def fetch_data(url: str, timeout: int = 10, max_attempts: int = 3, session: requests.Session | None = None) -> str:
    sess = session or REQUESTS_SESSION
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
            response = sess.get(modified_url, timeout=timeout, verify=verify)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as exc:
            last_exc = exc
            if attempt < max_attempts:
                continue
            raise last_exc

def save_to_local_file(path, content):
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)
    log(f"📁 Данные сохранены локально в {path}")

def extract_source_name(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        path_parts = parsed.path.split('/')
        if len(path_parts) > 2:
            return f"{path_parts[1]}/{path_parts[2]}"
        return parsed.netloc
    except:
        return "Источник"

# ================== НОВЫЙ ФУНКЦИОНАЛ: ИЗВЛЕЧЕНИЕ IP И ПОРТА ==================
def extract_host_port_from_config(config_line: str):
    """Извлекает хост и порт из конфигурационной строки"""
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
        match = re.search(r'(?:@|//)([\w\.-]+):(\d{1,5})', config_line)
        if match:
            return match.group(1), int(match.group(2))

    except:
        pass

    return None, None

# ================== НОВЫЙ ФУНКЦИОНАЛ: ПРОВЕРКА ПИНГА ==================
def check_server_availability(host: str, port: int, timeout: float = CONNECTION_TIMEOUT) -> int:
    """
    Проверяет доступность сервера и возвращает время отклика в мс
    Возвращает -1 если сервер недоступен
    """
    try:
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            elapsed = (time.time() - start_time) * 1000  # в миллисекундах
            return int(elapsed)
        else:
            return -1
    except:
        return -1

def test_single_config(config_line: str) -> tuple:
    """
    Тестирует один конфиг и возвращает (config_line, ping_ms)
    """
    host, port = extract_host_port_from_config(config_line)

    if not host or not port:
        return (config_line, -1)

    ping_ms = check_server_availability(host, port)
    return (config_line, ping_ms)

# ================== НОВЫЙ ФУНКЦИОНАЛ: ФИЛЬТРАЦИЯ ЛУЧШИХ КОНФИГОВ ==================
def filter_and_sort_best_configs(configs: list, local_path: str) -> list:
    """
    Фильтрует конфиги, оставляя только быстрые и доступные сервера
    Возвращает отсортированный список лучших конфигов
    """
    if not ENABLE_PING_CHECK:
        return configs

    log(f"🔍 Проверка доступности {len(configs)} конфигов для {local_path}...")

    # Проверяем пинг всех конфигов параллельно
    tested_configs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=PING_WORKERS) as executor:
        futures = [executor.submit(test_single_config, cfg) for cfg in configs]
        for future in concurrent.futures.as_completed(futures):
            tested_configs.append(future.result())

    # Фильтруем недоступные и медленные
    available = [(cfg, ping) for cfg, ping in tested_configs if 0 < ping <= MAX_PING_MS]

    # Сортируем по пингу (от лучших к худшим)
    available.sort(key=lambda x: x[1])

    # Ограничиваем количество
    best_configs = [cfg for cfg, ping in available[:MAX_CONFIGS_PER_FILE]]

    filtered_count = len(configs) - len(best_configs)
    if filtered_count > 0:
        log(f"✅ Отобрано {len(best_configs)} лучших конфигов (отфильтровано {filtered_count}) для {local_path}")
        if best_configs and available:
            avg_ping = sum(ping for _, ping in available[:len(best_configs)]) / len(best_configs)
            min_ping = available[0][1] if available else 0
            max_ping = available[min(len(available)-1, len(best_configs)-1)][1] if available else 0
            log(f"📊 Пинг серверов: мин={min_ping}ms, макс={max_ping}ms, средний={int(avg_ping)}ms")
    else:
        log(f"⚠️ Все конфиги недоступны или слишком медленные для {local_path}")

    return best_configs

INSECURE_PATTERN = re.compile(
    r'(?:[?&;]|3%[Bb])(allowinsecure|allow_insecure|insecure)=(?:1|true|yes)(?:[&;#]|$|(?=\s|$))',
    re.IGNORECASE
)

def filter_insecure_configs(local_path, data, log_enabled=True):
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

    if filtered_count > 0 and log_enabled:
        log(f"ℹ️ Отфильтровано {filtered_count} небезопасных конфигов для {local_path}")

    return "\n".join(result), filtered_count

def update_readme_table():
    try:
        try:
            readme_file = REPO.get_contents("README.md")
            old_content = readme_file.decoded_content.decode("utf-8")
        except GithubException as e:
            if e.status == 404:
                log("❌ README.md не найден в репозитории")
                return
            else:
                log(f"⚠️ Ошибка при получении README.md: {e}")
                return

        time_part, date_part = offset.split(" | ")

        table_header = "| № | Файл | Источник | Время | Дата |\n|--|--|--|--|--|"
        table_rows = []

        for i, (remote_path, url) in enumerate(zip(REMOTE_PATHS, URLS + [""]), 1):
            filename = f"{i}.txt"
            raw_file_url = f"https://github.com/{REPO_NAME}/raw/refs/heads/main/githubmirror/{i}.txt"

            if i <= 25:
                source_name = extract_source_name(url)
                source_column = f"[{source_name}]({url})"
            else:
                source_name = "Обход SNI/CIDR белых списков"
                source_column = f"[{source_name}]({raw_file_url})"

            if i in updated_files:
                update_time = time_part
                update_date = date_part
            else:
                pattern = rf"\|\s*{i}\s*\|\s*\[`{filename}`\].*?\|.*?\|\s*(.*?)\s*\|\s*(.*?)\s*\|"
                match = re.search(pattern, old_content)
                if match:
                    update_time = match.group(1).strip() if match.group(1).strip() else "Никогда"
                    update_date = match.group(2).strip() if match.group(2).strip() else "Никогда"
                else:
                    update_time = "Никогда"
                    update_date = "Никогда"

            table_rows.append(f"| {i} | [`{filename}`]({raw_file_url}) | {source_column} | {update_time} | {update_date} |")

        new_table = table_header + "\n" + "\n".join(table_rows)

        table_pattern = r"\| № \| Файл \| Источник \| Время \| Дата \|[\s\S]*?\|--\|--\|--\|--\|--\|[\s\S]*?(\n\n## |$)"
        new_content = re.sub(table_pattern, new_table + r"\1", old_content)

        if new_content != old_content:
            REPO.update_file(
                path="README.md",
                message="📝 Обновление таблицы в README.md",
                content=new_content,
                sha=readme_file.sha
            )
            log("📝 Таблица в README.md обновлена")
        else:
            log("📝 Таблица в README.md не требует изменений")

    except Exception as e:
        log(f"⚠️ Ошибка при обновлении README.md: {e}")

def upload_to_github(local_path, remote_path):
    if not os.path.exists(local_path):
        log(f"❌ Файл {local_path} не найден.")
        return

    repo = REPO

    with open(local_path, "r", encoding="utf-8") as file:
        content = file.read()

    max_retries = 5

    for attempt in range(1, max_retries + 1):
        try:
            try:
                file_in_repo = repo.get_contents(remote_path)
                current_sha = file_in_repo.sha
            except GithubException as e_get:
                if getattr(e_get, "status", None) == 404:
                    basename = os.path.basename(remote_path)
                    repo.create_file(
                        path=remote_path,
                        message=f"🆕 Первый коммит {basename} по часовому поясу Европа/Москва: {offset}",
                        content=content,
                    )
                    log(f"🆕 Файл {remote_path} создан.")
                    file_index = int(remote_path.split('/')[1].split('.')[0])
                    with _UPDATED_FILES_LOCK:
                        updated_files.add(file_index)
                    return
                else:
                    msg = e_get.data.get("message", str(e_get))
                    log(f"⚠️ Ошибка при получении {remote_path}: {msg}")
                    return

            try:
                remote_content = file_in_repo.decoded_content.decode("utf-8", errors="replace")
                if remote_content == content:
                    log(f"🔄 Изменений для {remote_path} нет.")
                    return
            except Exception:
                pass

            basename = os.path.basename(remote_path)
            try:
                repo.update_file(
                    path=remote_path,
                    message=f"🚀 Обновление {basename} по часовому поясу Европа/Москва: {offset}",
                    content=content,
                    sha=current_sha,
                )
                log(f"🚀 Файл {remote_path} обновлён в репозитории.")
                file_index = int(remote_path.split('/')[1].split('.')[0])
                with _UPDATED_FILES_LOCK:
                    updated_files.add(file_index)
                return
            except GithubException as e_upd:
                if getattr(e_upd, "status", None) == 409:
                    if attempt < max_retries:
                        wait_time = 0.5 * (2 ** (attempt - 1))
                        log(f"⚠️ Конфликт SHA для {remote_path}, попытка {attempt}/{max_retries}, ждем {wait_time} сек")
                        time.sleep(wait_time)
                        continue
                    else:
                        log(f"❌ Не удалось обновить {remote_path} после {max_retries} попыток")
                        return
                else:
                    msg = e_upd.data.get("message", str(e_upd))
                    log(f"⚠️ Ошибка при загрузке {remote_path}: {msg}")
                    return

        except Exception as e_general:
            short_msg = str(e_general)
            if len(short_msg) > 200:
                short_msg = short_msg[:200] + "…"
            log(f"⚠️ Непредвиденная ошибка при обновлении {remote_path}: {short_msg}")
            return

    log(f"❌ Не удалось обновить {remote_path} после {max_retries} попыток")

def download_and_save(idx):
    url = URLS[idx]
    local_path = LOCAL_PATHS[idx]
    try:
        data = fetch_data(url)
        data, _ = filter_insecure_configs(local_path, data)

        # Разбиваем на строки и фильтруем лучшие конфиги
        configs = [line.strip() for line in data.splitlines() if line.strip()]
        configs = filter_and_sort_best_configs(configs, local_path)
        data = "\n".join(configs)

        if os.path.exists(local_path):
            try:
                with open(local_path, "r", encoding="utf-8") as f_old:
                    old_data = f_old.read()
                if old_data == data:
                    log(f"🔄 Изменений для {local_path} нет (локально). Пропуск загрузки в GitHub.")
                    return None
            except Exception:
                pass

        save_to_local_file(local_path, data)
        return local_path, REMOTE_PATHS[idx]
    except Exception as e:
        short_msg = str(e)
        if len(short_msg) > 200:
            short_msg = short_msg[:200] + "…"
        log(f"⚠️ Ошибка при скачивании {url}: {short_msg}")
        return None

def create_filtered_configs():
    """Создает 26-й файл с конфигами для белых списков"""
    sni_domains = [
        "avito.ru", "avito.st", "ok.ru", "vk.com", "vk.ru", "mail.ru", "yandex.ru", "yandex.com",
        "gosuslugi.ru", "sberbank.ru", "alfabank.ru", "tbank.ru", "ozon.ru", "wildberries.ru",
        "2gis.com", "2gis.ru", "hh.ru", "drom.ru", "kinopoisk.ru", "rutube.ru", "dzen.ru",
    ]

    try:
        pattern_str = r"(?:" + "|".join(re.escape(d) for d in sni_domains) + r")"
        sni_regex = re.compile(pattern_str)
    except Exception as e:
        log(f"❌ Ошибка компиляции Regex: {e}")
        return None

    def _extract_host_port(line: str):
        if not line: return None
        if line.startswith("vmess://"):
            try:
                payload = line[8:]
                rem = len(payload) % 4
                if rem: payload += '=' * (4 - rem)
                decoded = base64.b64decode(payload).decode('utf-8', errors='ignore')
                if decoded.startswith('{'):
                    j = json.loads(decoded)
                    host = j.get('add') or j.get('host') or j.get('ip')
                    port = j.get('port')
                    if host and port: return str(host), str(port)
            except Exception: pass
            return None
        m = re.search(r'(?:@|//)([\w\.-]+):(\d{1,5})', line)
        if m: return m.group(1), m.group(2)
        return None

    def _process_file_filtering(file_idx):
        local_path = f"githubmirror/{file_idx}.txt"
        filtered_lines = []
        if not os.path.exists(local_path):
            return filtered_lines
        try:
            with open(local_path, "r", encoding="utf-8") as file:
                content = file.read()
            content = re.sub(r'(vmess|vless|trojan|ss|ssr|tuic|hysteria|hysteria2)://', r'\n\1://', content)
            lines = content.splitlines()
            for line in lines:
                line = line.strip()
                if not line: continue
                if sni_regex.search(line):
                    filtered_lines.append(line)
        except Exception:
            pass
        return filtered_lines

    all_configs = []

    max_workers = min(16, os.cpu_count() + 4)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_process_file_filtering, i) for i in range(1, 26)]
        for future in concurrent.futures.as_completed(futures):
            all_configs.extend(future.result())

    def _load_extra_configs(url):
        count_removed = 0
        configs = []
        try:
            data = fetch_data(url)
            data, count = filter_insecure_configs("githubmirror/26.txt", data, log_enabled=False)
            count_removed = count

            data = re.sub(r'(vmess|vless|trojan|ss|ssr|tuic|hysteria|hysteria2)://', r'\n\1://', data)
            lines = data.splitlines()
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    configs.append(line)
        except Exception as e:
            short_msg = str(e)
            if len(short_msg) > 200:
                short_msg = short_msg[:200] + "…"
            log(f"⚠️ Ошибка при загрузке {url}: {short_msg}")

        return configs, count_removed

    extra_configs = []
    total_insecure_filtered_26 = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(EXTRA_URLS_FOR_26))) as executor:
        futures = [executor.submit(_load_extra_configs, url) for url in EXTRA_URLS_FOR_26]
        for future in concurrent.futures.as_completed(futures):
            res_configs, res_count = future.result()
            extra_configs.extend(res_configs)
            total_insecure_filtered_26 += res_count

    if total_insecure_filtered_26 > 0:
        log(f"ℹ️  Отфильтровано {total_insecure_filtered_26} небезопасных конфигов для githubmirror/26.txt")

    all_configs.extend(extra_configs)

    # Применяем фильтрацию по пингу и для 26-го файла
    all_configs = filter_and_sort_best_configs(all_configs, "githubmirror/26.txt")

    # Дедупликация
    seen_full = set()
    seen_hostport = set()
    unique_configs = []

    for cfg in all_configs:
        c = cfg.strip()
        if not c or c in seen_full: continue
        seen_full.add(c)
        hostport = _extract_host_port(c)
        if hostport:
            key = f"{hostport[0].lower()}:{hostport[1]}"
            if key in seen_hostport: continue
            seen_hostport.add(key)
        unique_configs.append(c)

    local_path_26 = "githubmirror/26.txt"
    try:
        with open(local_path_26, "w", encoding="utf-8") as file:
            file.write("\n".join(unique_configs))
        log(f"📁 Создан файл {local_path_26} с {len(unique_configs)} конфигами")
    except Exception as e:
        log(f"⚠️ Ошибка при сохранении {local_path_26}: {e}")

    return local_path_26

def main(dry_run: bool = False):
    max_workers_download = min(DEFAULT_MAX_WORKERS, max(1, len(URLS)))
    max_workers_upload = max(2, min(6, len(URLS)))

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers_download) as download_pool, \
         concurrent.futures.ThreadPoolExecutor(max_workers=max_workers_upload) as upload_pool:

        download_futures = [download_pool.submit(download_and_save, i) for i in range(len(URLS))]
        upload_futures: list[concurrent.futures.Future] = []

        for future in concurrent.futures.as_completed(download_futures):
            result = future.result()
            if result:
                local_path, remote_path = result
                if dry_run:
                    log(f"ℹ️ Dry-run: пропускаем загрузку {remote_path} (локальный путь {local_path})")
                else:
                    upload_futures.append(upload_pool.submit(upload_to_github, local_path, remote_path))

        for uf in concurrent.futures.as_completed(upload_futures):
            _ = uf.result()

    local_path_26 = create_filtered_configs()

    if not dry_run:
        upload_to_github(local_path_26, "githubmirror/26.txt")

    if not dry_run and updated_files:
        update_readme_table()

    ordered_keys = sorted(k for k in LOGS_BY_FILE.keys() if k != 0)
    output_lines: list[str] = []

    for k in ordered_keys:
        output_lines.append(f"----- {k}.txt -----")
        output_lines.extend(LOGS_BY_FILE[k])

    if LOGS_BY_FILE.get(0):
        output_lines.append("----- Общие сообщения -----")
        output_lines.extend(LOGS_BY_FILE[0])

    print("\n".join(output_lines))

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Скачивание конфигов и загрузка в GitHub")
    parser.add_argument("--dry-run", action="store_true", help="Только скачивать и сохранять локально, не загружать в GitHub")
    args = parser.parse_args()

    main(dry_run=args.dry_run)
