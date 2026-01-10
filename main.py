#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GOIDA VPN Config Aggregator v6.0 ULTIMATE
🚀 Супер-версия с гарантией all.txt на GitHub
Объединяет HAPP.py + HAPP-VPN-Manager + Двойная проверка
Автор: SEDiK-Bes
Дата: 2026-01-10
"""

import os
import sys
import json
import time
import base64
import socket
import threading
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Установка зависимостей
try:
    import requests
    from github import Github, Auth, GithubException
except ImportError:
    print("📦 Установка требуемых библиотек...")
    os.system("pip install requests PyGithub --upgrade -q")
    import requests
    from github import Github, Auth, GithubException

# ======================== КОНФИГУРАЦИЯ ========================
GITHUB_TOKEN = os.environ.get("MY_TOKEN", "").strip()
REPO_NAME = os.environ.get("REPO_NAME", "SEDiK-Bes/goida-vpn-configs").strip()

# Параметры фильтрации
MAX_PING_MS = 300
MAX_CONFIGS = 150
TCP_WORKERS = 25
ENABLE_TCP = True
ENABLE_ICMP = False  # Опционально
REMOVE_DUPES = True

# Проверка токена
if not GITHUB_TOKEN or GITHUB_TOKEN == "ghp_":
    print("❌ ОШИБКА: MY_TOKEN не установлен!")
    print("Выполни: $env:MY_TOKEN = 'ghp_твой_токен'")
    sys.exit(1)

if "ghp_" not in GITHUB_TOKEN:
    print("❌ ОШИБКА: Неверный формат токена")
    sys.exit(1)

# ======================== ИСТОЧНИКИ ========================
URLS = [
    "https://raw.githubusercontent.com/sakha1370/OpenRay/refs/heads/main/output/all_valid_proxies.txt",
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
    "https://raw.githubusercontent.com/STR97/STRUGOV/refs/heads/main/STR.BYPASS",
    "https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/refs/heads/main/Config/vless.txt",
]

SNI_URLS = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Cable.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    "https://raw.githubusercontent.com/zieng2/wl/main/vless.txt",
]

SNI_DOMAINS = [
    "avito.ru", "avito.st", "ok.ru", "vk.com", "vk.ru", "mail.ru", "yandex.ru",
    "gosuslugi.ru", "sberbank.ru", "alfabank.ru", "tbank.ru", "ozon.ru",
    "wildberries.ru", "2gis.com", "hh.ru", "drom.ru", "kinopoisk.ru",
]

# ======================== ЛОГИРОВАНИЕ ========================
logs = defaultdict(list)
lock = threading.Lock()

def log(msg, idx=0):
    """Логировать сообщение"""
    with lock:
        ts = datetime.now().strftime("%H:%M:%S")
        logs[idx].append(f"[{ts}] {msg}")
        print(msg)

# ======================== HTTP СЕССИЯ ========================
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})

def fetch(url, timeout=15, retries=3):
    """Скачать URL с retry"""
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=timeout, verify=(attempt < 2))
            r.raise_for_status()
            return r.text
        except Exception as e:
            if attempt == retries - 1:
                return ""
            time.sleep(1)
    return ""

# ======================== ПАРСИНГ ========================
def parse_config(line):
    """Извлечь host:port из конфига"""
    if not line:
        return None
    
    # Vmess - база64
    if line.startswith("vmess://"):
        try:
            payload = line[8:]
            if len(payload) % 4:
                payload += "=" * (4 - len(payload) % 4)
            data = json.loads(base64.b64decode(payload).decode('utf-8', errors='ignore'))
            host = data.get('add') or data.get('host') or data.get('ip')
            port = data.get('port')
            if host and port:
                return (str(host), int(port))
        except:
            pass
    
    # Вless, trojan, ss - регекс
    m = re.search(r'(?:@|//)([a-zA-Z0-9\.\-]+):(\d{1,5})', line)
    if m:
        return (m.group(1), int(m.group(2)))
    
    return None

def tcp_check(host, port, timeout=2):
    """Быстрая TCP проверка"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        start = time.time()
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            return int((time.time() - start) * 1000)
    except:
        pass
    return -1

def is_insecure(config):
    """Проверить на allowinsecure=true"""
    pattern = r'(?:[?&;]|3%[Bb])(allowinsecure|allow_insecure|insecure)=(?:1|true|yes)'
    return bool(re.search(pattern, config, re.IGNORECASE))

# ======================== ФИЛЬТРАЦИЯ ========================
def filter_and_sort(configs, file_idx):
    """Фильтр + TCP проверка + сортировка"""
    
    # Удалить небезопасные
    configs = [c for c in configs if not is_insecure(c)]
    log(f"🔍 TCP проверка {len(configs)} конфигов...", file_idx)
    
    if not ENABLE_TCP or not configs:
        return configs[:MAX_CONFIGS]
    
    import concurrent.futures
    
    def test_config(cfg):
        parts = parse_config(cfg)
        if not parts:
            return (cfg, -1)
        host, port = parts
        ping = tcp_check(host, port)
        return (cfg, ping)
    
    # Параллельная проверка
    tested = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(TCP_WORKERS, len(configs))) as ex:
        tested = list(ex.map(test_config, configs))
    
    # Отсортировать по пингу
    good = sorted([c for c, p in tested if 0 < p <= MAX_PING_MS], 
                  key=lambda c: next(p for cc, p in tested if cc == c))[:MAX_CONFIGS]
    
    if good:
        pings = [next(p for c, p in tested if c == cfg) for cfg in good]
        log(f"✅ {len(good)} конфигов (пинг {min(pings)}-{max(pings)}ms)", file_idx)
    
    return good

# ======================== ОБРАБОТКА ========================
def process_url(url, idx):
    """Скачать источник"""
    log(f"⬇️  [{idx+1}/{len(URLS)}] {url[:60]}...")
    
    data = fetch(url)
    if not data:
        log(f"❌ Ошибка", idx)
        return []
    
    configs = [c.strip() for c in data.strip().split('\n') if c.strip()]
    log(f"📥 {len(configs)} конфигов", idx)
    
    # Дедупа
    if REMOVE_DUPES:
        configs = list(dict.fromkeys(configs))
    
    # Фильтр
    return filter_and_sort(configs, idx)

def save_file(path, content):
    """Сохранить файл"""
    Path(path).parent.mkdir(exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def build_all_txt():
    """ГАРАНТИРОВАННОЕ all.txt"""
    log("🔗 Создание all.txt...")
    
    all_lines = set()
    
    # Из 1-25
    for i in range(1, 26):
        path = f"githubmirror/{i}.txt"
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            all_lines.add(line)
            except:
                pass
    
    # Из 26
    if os.path.exists("githubmirror/26.txt"):
        try:
            with open("githubmirror/26.txt", 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        all_lines.add(line)
        except:
            pass
    
    # Сохранить
    content = '\n'.join(sorted(all_lines))
    save_file("githubmirror/all.txt", content)
    log(f"✨ all.txt: {len(all_lines)} конфигов")
    
    return len(all_lines) > 0

# ======================== GITHUB PUSH ========================
def push_github():
    """Загрузить на GitHub"""
    log("📤 GitHub push...")
    
    try:
        g = Github(auth=Auth.Token(GITHUB_TOKEN))
        repo = g.get_repo(REPO_NAME)
    except Exception as e:
        log(f"❌ GitHub: {e}")
        return False
    
    files = [f"githubmirror/{i}.txt" for i in range(1, 27)] + ["githubmirror/all.txt"]
    
    for fpath in files:
        if not os.path.exists(fpath):
            continue
        
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                obj = repo.get_contents(fpath)
                repo.update_file(fpath, f"🚀 {fpath}", content, obj.sha)
                log(f"✅ {fpath}")
            except GithubException as e:
                if e.status == 404:
                    repo.create_file(fpath, f"🆕 {fpath}", content)
                    log(f"✅ {fpath}")
        except Exception as e:
            log(f"⚠️  {fpath}: {e}")
    
    return True

# ======================== ГЛАВНАЯ ========================
def main():
    print("\n" + "="*70)
    print("🚀 GOIDA VPN v6.0 ULTIMATE")
    print("="*70 + "\n")
    
    log(f"🔐 Token: {GITHUB_TOKEN[:15]}...")
    log(f"📦 Repo: {REPO_NAME}")
    log(f"⚙️  TCP Check: {ENABLE_TCP}, Max Ping: {MAX_PING_MS}ms")
    
    Path("githubmirror").mkdir(exist_ok=True)
    
    # Обработать источники
    log("\n🌐 Загрузка источников...")
    import concurrent.futures
    
    configs_dict = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(process_url, url, i): i for i, url in enumerate(URLS)}
        
        for future in concurrent.futures.as_completed(futures):
            idx = futures[future]
            try:
                configs_dict[idx] = future.result()
            except Exception as e:
                log(f"❌ Ошибка {idx}: {e}")
    
    # Сохранить 1-25
    log("\n💾 Сохранение файлов...")
    for idx, configs in configs_dict.items():
        if configs:
            save_file(f"githubmirror/{idx+1}.txt", '\n'.join(configs))
            log(f"📁 githubmirror/{idx+1}.txt")
    
    # Обработать 26 (SNI)
    log("\n🛡️  SNI конфиги (26.txt)...")
    sni_configs = []
    for url in SNI_URLS:
        data = fetch(url)
        if data:
            sni_configs.extend([c.strip() for c in data.split('\n') if c.strip()])
    
    # Фильтр SNI
    sni_configs = list(dict.fromkeys(sni_configs))
    sni_configs = filter_and_sort(sni_configs, 26)
    
    if sni_configs:
        save_file("githubmirror/26.txt", '\n'.join(sni_configs))
        log(f"✅ 26.txt: {len(sni_configs)} конфигов")
    
    # ГЛАВНОЕ - all.txt!
    log("\n" + "="*70)
    all_ok = build_all_txt()
    log("="*70)
    
    if not all_ok:
        log("⚠️  Внимание: all.txt пустой!")
    
    # Push
    log("\n📡 Загрузка на GitHub...")
    push_github()
    
    # Итог
    print("\n" + "="*70)
    print("✅ ГОТОВО!")
    print("="*70)
    print(f"📁 Результат: githubmirror/")
    print(f"🌐 GitHub: https://github.com/{REPO_NAME}/tree/main/githubmirror")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⛔ Прервано")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
