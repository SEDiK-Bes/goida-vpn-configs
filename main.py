#!/usr/bin/env python3
"""GOIDA VPN v4.2 - EC (от-10) + RU (обязательный) + Мир (все регионы)

Дополнено:
- генерация ссылок для HAPP через Yandex Cloud Function (прокси)
- получение зашифрованных ссылок happ://crypt3/... через HAPP Crypto API

Настройка:
- переменная окружения YANDEX_PROXY_URL (пример: https://<id>.serverless.yandexcloud.net)

Важно:
- если YANDEX_PROXY_URL не задан, скрипт просто сгенерирует файлы githubmirror/*.txt как раньше.
"""

import os
import sys
import base64
import re
import time
import socket
import html
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

import requests

TOKEN = os.environ.get('MY_TOKEN', '').strip()
if not TOKEN or not TOKEN.startswith('ghp_'):
    print('ERROR: Invalid MY_TOKEN')
    sys.exit(1)

# --- HAPP / Yandex integration (optional) ---
YANDEX_PROXY_URL = os.environ.get('YANDEX_PROXY_URL', '').strip().rstrip('/')
HAPP_CRYPTO_API = os.environ.get(
    'HAPP_CRYPTO_API', 'https://crypto.happ.su/api.php'
).strip()
ENABLE_HAPP_LINKS = os.environ.get('ENABLE_HAPP_LINKS', '1').strip() not in (
    '0', 'false', 'False'
)

START = time.time()
print('\n' + '=' * 70)
print('🚳 GOIDA VPN v4.2 - EC (от-10) | RU (обязательный) | Мир (остальные)')
print('=' * 70 + '\n')

# === CONSTANTS ===
MAX_PING_MS = 300
CONNECTION_TIMEOUT = 2.0
MAX_CONFIGS_PER_FILE = 100
HTTP_TIMEOUT = 8
THREAD_TIMEOUT = 15

EC_COUNTRIES = {
    'NL', 'DE', 'FR', 'GB', 'UK', 'SE', 'NO', 'FI', 'PL', 'IT', 'ES', 'CH',
    'AT', 'BE', 'CZ', 'DK', 'IE', 'RO', 'PT', 'GR', 'HR', 'HU', 'SK', 'SI',
    'BG', 'LT', 'LV', 'EE', 'IS'
}

RU_COUNTRIES = {'RU', 'KZ', 'BY', 'UZ'}

WORLD_COUNTRIES = {
    'US', 'CA', 'MX', 'BR', 'AR', 'JP', 'KR', 'CN', 'IN', 'AU', 'NZ', 'TR',
    'CY', 'GE', 'AM', 'AZ', 'TH', 'SG', 'MY', 'ID', 'VN', 'PH', 'AE', 'SA',
    'IL', 'IR', 'EG', 'ZA', 'NG', 'HK', 'MO', 'TW', 'PK', 'BD', 'LK', 'NP',
    'TJ', 'TM', 'KG', 'KW', 'QA', 'BH', 'OM', 'IQ', 'JO', 'PS', 'YE', 'SY', 'LB'
}

SOURCES = [
    'https://raw.githubusercontent.com/sakha1370/OpenRay/refs/heads/main/output/all_valid_proxies.txt',
    'https://raw.githubusercontent.com/sevcator/5ubscrpt10n/main/protocols/vl.txt',
    'https://raw.githubusercontent.com/yitong2333/proxy-minging/refs/heads/main/v2ray.txt',
    'https://raw.githubusercontent.com/acymz/AutoVPN/refs/heads/main/data/V2.txt',
    'https://raw.githubusercontent.com/miladtahanian/V2RayCFGDumper/refs/heads/main/config.txt',
    'https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_RAW.txt',
    'https://github.com/Epodonios/v2ray-configs/raw/main/Splitted-By-Protocol/trojan.txt',
    'https://raw.githubusercontent.com/YasserDivaR/pr0xy/refs/heads/main/ShadowSocks2021.txt',
    'https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/refs/heads/main/category/vless.txt',
    'https://raw.githubusercontent.com/mheidari98/.proxy/refs/heads/main/vless',
    'https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_iran.txt',
    'https://raw.githubusercontent.com/mheidari98/.proxy/refs/heads/main/all',
    'https://github.com/Kwinshadow/TelegramV2rayCollector/raw/refs/heads/main/sublinks/mix.txt',
    'https://github.com/LalatinaHub/Mineral/raw/refs/heads/master/result/nodes',
    'https://raw.githubusercontent.com/miladtahanian/multi-proxy-config-fetcher/refs/heads/main/configs/proxy_configs.txt',
    'https://raw.githubusercontent.com/Pawdroid/Free-servers/refs/heads/main/sub',
    'https://github.com/MhdiTaheri/V2rayCollector_Py/raw/refs/heads/main/sub/Mix/mix.txt',
    'https://github.com/Epodonios/v2ray-configs/raw/main/Splitted-By-Protocol/vmess.txt',
    'https://github.com/MhdiTaheri/V2rayCollector/raw/refs/heads/main/sub/mix',
    'https://github.com/Argh94/Proxy-List/raw/refs/heads/main/All_Config.txt',
    'https://raw.githubusercontent.com/shabane/kamaji/master/hub/merged.txt',
    'https://raw.githubusercontent.com/wuqb2i4f/xray-config-toolkit/main/output/base64/mix-uri',
    'https://raw.githubusercontent.com/AzadNetCH/Clash/refs/heads/main/AzadNet.txt',
    'https://raw.githubusercontent.com/STR97/STRUGOV/refs/heads/main/STR.BYPASS',
    'https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/refs/heads/main/Config/vless.txt',
]

SNI_SOURCES = [
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Cable.txt',
    'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt',
    'https://raw.githubusercontent.com/zieng2/wl/main/vless.txt',
]


def log_t(msg):
    """Log with elapsed time."""
    print(f'[{time.time()-START:6.2f}s] {msg}')


def happ_encrypt_url(url_to_encrypt: str) -> str:
    """Encrypt URL via HAPP API."""
    try:
        r = requests.post(
            HAPP_CRYPTO_API,
            json={"url": url_to_encrypt},
            timeout=12,
            headers={"Accept": "application/json, text/plain, */*"},
        )
        if r.status_code != 200:
            return ''
        ct = (r.headers.get('content-type') or '').lower()
        if 'application/json' in ct:
            j = r.json() if r.text else {}
            return (j.get('url') or j.get('encrypted_url') or j.get('result') or '').strip()
        return (r.text or '').strip()
    except Exception:
        return ''


def maybe_print_happ_links():
    """Print HAPP links."""
    if not ENABLE_HAPP_LINKS:
        return
    if not YANDEX_PROXY_URL:
        log_t('HAPP LINKS: YANDEX_PROXY_URL not set')
        return
    mapping = {'EC': 'set_a', 'RU': 'set_b', 'WORLD': 'set_c'}
    out_lines = []
    log_t('PHASE 7: Generating HAPP crypt3 links...')
    for name, source_code in mapping.items():
        proxy_url = f"{YANDEX_PROXY_URL}?source={source_code}"
        enc = happ_encrypt_url(proxy_url)
        if enc and enc.startswith('happ://'):
            out_lines.append(f"{name}: {enc}")
            log_t(f"✓ HAPP {name}: {enc[:48]}...")
        else:
            out_lines.append(f"{name}: (FAILED) {proxy_url}")
            log_t(f"✗ HAPP {name}: failed")
    try:
        with open('happ_crypt3_links.txt', 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out_lines) + '\n')
        log_t('Saved: happ_crypt3_links.txt')
    except Exception:
        log_t('WARN: cannot write happ_crypt3_links.txt')


def is_valid(line):
    """Validate config format."""
    if not line or len(line) < 10 or len(line) > 5000:
        return False
    line = line.strip()
    if line.startswith(('vmess://', 'vless://', 'trojan://', 'ss://', 'ssr://')):
        return True
    if re.match(r'^[A-Za-z0-9+/]{20,}$', line) and len(line) < 2000:
        try:
            base64.b64decode(line, validate=True)
            return True
        except Exception:
            pass
    if re.search(r'^([0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{2,5}$', line):
        return True
    if re.search(r'^([a-z0-9.-]+):([0-9]{2,5})$', line, re.IGNORECASE):
        return True
    return False


def http_get(url, idx):
    """Download from URL."""
    try:
        r = requests.get(url, timeout=HTTP_TIMEOUT)
        if r.status_code == 200:
            lines = [l.strip() for l in r.text.splitlines() if l.strip()]
            return (idx, lines, True)
    except Exception:
        pass
    return (idx, [], False)


def gh_push(path, content):
    """Push to GitHub."""
    try:
        headers = {
            'Authorization': f'token {TOKEN}',
            'Accept': 'application/vnd.github+json'
        }
        url = f'https://api.github.com/repos/SEDiK-Bes/goida-vpn-configs/contents/{path}'
        r = requests.get(url, headers=headers, timeout=5)
        sha = None
        if r.status_code == 200:
            sha = r.json()['sha']
        data = {
            'message': f'update {path}',
            'content': base64.b64encode(content.encode('utf-8')).decode('ascii')
        }
        if sha:
            data['sha'] = sha
        r = requests.put(url, headers=headers, json=data, timeout=10)
        return r.status_code in (200, 201)
    except Exception:
        return False


def extract_host_port(config_line):
    """Extract host:port. 🔧 Fixed: json.loads + port validation."""
    try:
        config_line = config_line.strip()
        if config_line.startswith('vmess://'):
            try:
                payload = config_line[8:]
                rem = len(payload) % 4
                if rem:
                    payload += '=' * (4 - rem)
                decoded = base64.b64decode(payload).decode('utf-8', errors='ignore')
                if decoded.startswith('{'):
                    try:
                        # ✅ FIXED: json.loads instead of eval
                        j = json.loads(decoded)
                        host = j.get('add') or j.get('host') or j.get('ip')
                        port_raw = j.get('port')
                        if host and port_raw:
                            port = int(port_raw)
                            # ✅ FIXED: Port validation
                            if 1 <= port <= 65535:
                                return (str(host), port)
                    except (json.JSONDecodeError, ValueError, TypeError):
                        pass
            except Exception:
                pass
        match = re.search(r'@([^:/?]+):([0-9]{2,5})', config_line)
        if match:
            try:
                host = match.group(1)
                port = int(match.group(2))
                # ✅ FIXED: Port validation
                if 1 <= port <= 65535:
                    return (host, port)
            except ValueError:
                pass
    except Exception:
        pass
    return (None, None)


def _extract_remark_fragment(config_line: str):
    """Extract remark fragment."""
    if '#' not in config_line:
        return None
    fragment = config_line.split('#', 1)[1]
    fragment = html.unescape(urllib.parse.unquote(fragment)).upper()
    return fragment


def extract_country(config_line):
    """Extract country code. 🔧 Fixed: regex word boundaries."""
    try:
        fragment = _extract_remark_fragment(config_line)
        if not fragment:
            return 'UNKNOWN'
        all_countries = EC_COUNTRIES | RU_COUNTRIES | WORLD_COUNTRIES
        # ✅ FIXED: Check longer codes first, use word boundaries
        sorted_countries = sorted(all_countries, key=len, reverse=True)
        for cc in sorted_countries:
            # ✅ Word boundary prevents 'US' matching in 'AWESOME'
            if re.search(r'\b' + cc + r'\b', fragment):
                return cc
    except Exception:
        pass
    return 'UNKNOWN'


def check_ping(host, port):
    """Check ping via TCP."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(CONNECTION_TIMEOUT)
        start = time.time()
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            elapsed_ms = int((time.time() - start) * 1000)
            if elapsed_ms <= MAX_PING_MS:
                return elapsed_ms
    except Exception:
        pass
    return -1


def test_config(config_line):
    """Test config."""
    host, port = extract_host_port(config_line)
    if not host or not port:
        return (config_line, -1, 'UNKNOWN')
    ping_ms = check_ping(host, port)
    country = extract_country(config_line) if ping_ms > 0 else 'UNKNOWN'
    return (config_line, ping_ms, country)


def main():
    """Main entry point. 🔧 Fixed: Now properly guarded."""
    # === DOWNLOAD ===
    log_t('PHASE 1: Downloading sources...')
    all_configs = []
    with ThreadPoolExecutor(max_workers=25) as ex:
        futures = {ex.submit(http_get, url, i): i for i, url in enumerate(SOURCES, 1)}
        # ✅ FIXED: Added timeout and exception handling
        for f in as_completed(futures, timeout=THREAD_TIMEOUT):
            try:
                idx, lines, success = f.result(timeout=10)
                if success:
                    valids = [l for l in lines if is_valid(l)][:150]
                    all_configs.extend(valids)
            except Exception as e:
                log_t(f'Warning: Future timeout/error: {e}')

    log_t(f'Downloaded: {len(all_configs)} total configs')

    # === SNI ===
    log_t('PHASE 2: SNI sources...')
    sni = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(http_get, url, i): i for i, url in enumerate(SNI_SOURCES)}
        for f in as_completed(futures, timeout=THREAD_TIMEOUT):
            try:
                idx, lines, success = f.result(timeout=10)
                if success:
                    sni.extend(lines)
            except Exception as e:
                log_t(f'Warning: SNI future error: {e}')

    sni_valids = [l for l in sni if is_valid(l)][:150]
    all_configs.extend(sni_valids)
    log_t(f'SNI: {len(sni_valids)} configs')
    log_t(f'TOTAL: {len(all_configs)} before dedup')

    if not all_configs:
        log_t('ERROR: No configs')
        sys.exit(1)

    # === DEDUP ===
    log_t('PHASE 3: Deduplicating...')
    unique = sorted(list(set(all_configs)))
    log_t(f'Unique: {len(unique)} configs')

    # === PUSH all.txt ===
    log_t('PHASE 4: Pushing all.txt...')
    content = '\n'.join(unique)
    if gh_push('githubmirror/all.txt', content):
        log_t(f'✓ all.txt: {len(unique)} configs ({len(content.encode("utf-8")):,} bytes)')
    else:
        log_t('✗ all.txt FAILED')

    # === REGIONAL FILTERING ===
    log_t('PHASE 5: Regional filtering (EC + RU + World)...')
    tested = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = [ex.submit(test_config, cfg) for cfg in unique]
        for f in as_completed(futures, timeout=THREAD_TIMEOUT):
            try:
                tested.append(f.result(timeout=10))
            except Exception as e:
                log_t(f'Warning: Test timeout/error: {e}')

    ec_configs = []
    ru_configs = []
    world_configs = []

    for cfg, ping_ms, country in tested:
        if ping_ms <= 0:
            continue
        if country in EC_COUNTRIES:
            ec_configs.append((cfg, ping_ms))
        elif country in RU_COUNTRIES:
            ru_configs.append((cfg, ping_ms))
        else:
            world_configs.append((cfg, ping_ms))

    ec_configs.sort(key=lambda x: x[1])
    ru_configs.sort(key=lambda x: x[1])
    world_configs.sort(key=lambda x: x[1])

    ec_lines = [cfg for cfg, _ in ec_configs[:MAX_CONFIGS_PER_FILE]]
    ru_lines = [cfg for cfg, _ in ru_configs[:MAX_CONFIGS_PER_FILE]]
    world_lines = [cfg for cfg, _ in world_configs[:MAX_CONFIGS_PER_FILE]]

    # === PUSH REGIONAL FILES ===
    log_t('PHASE 6: Pushing regional files...')
    if ec_lines:
        ec_content = '\n'.join(ec_lines)
        if gh_push('githubmirror/ec.txt', ec_content):
            log_t(f'✓ ec.txt: {len(ec_lines)} configs (ЕС, от-10)')
        else:
            log_t('✗ ec.txt FAILED')
    if ru_lines:
        ru_content = '\n'.join(ru_lines)
        if gh_push('githubmirror/ru.txt', ru_content):
            log_t(f'✓ ru.txt: {len(ru_lines)} configs (🔴 RU+KZ+BY+UZ)')
        else:
            log_t('✗ ru.txt FAILED')
    if world_lines:
        world_content = '\n'.join(world_lines)
        if gh_push('githubmirror/world.txt', world_content):
            log_t(f'✓ world.txt: {len(world_lines)} configs (rest of world)')
        else:
            log_t('✗ world.txt FAILED')

    maybe_print_happ_links()

    elapsed = time.time() - START
    print(f'\n✅ SUCCESS! Time: {elapsed:.1f}s')
    print(f'📁 Files: all.txt={len(unique)}, ec.txt={len(ec_lines)}, ru.txt={len(ru_lines)}, world.txt={len(world_lines)}\n')


# ✅ FIXED: Main guard added
if __name__ == '__main__':
    main()
