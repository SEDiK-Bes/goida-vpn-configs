#!/usr/bin/env python3
"""GOIDA VPN v14.1 - Generate all.txt + s-happ.txt (Europe by ping)"""
import os, sys, base64, re, time, socket, html, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import requests

TOKEN = os.environ.get('MY_TOKEN', '').strip()
if not TOKEN or not TOKEN.startswith('ghp_'):
    print('ERROR: Invalid MY_TOKEN'); sys.exit(1)

START = time.time()
print('\n' + '='*70)
print('🚳 GOIDA VPN v14.1 - WITH S-HAPP EUROPEAN RANKING')
print('='*70 + '\n')

def log_t(msg):
    print(f'[{time.time()-START:6.2f}s] {msg}')

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

# European country codes
EUROPEAN_COUNTRIES = {
    'NL', 'DE', 'FR', 'GB', 'UK', 'SE', 'NO', 'FI', 'PL', 'IT', 'ES', 'CH', 'AT', 'BE', 'CZ', 'DK', 'IE', 'RO', 'PT', 'GR',
    'HR', 'HU', 'SK', 'SI', 'BG', 'LT', 'LV', 'EE', 'IS'
}

MAX_PING_MS = 300
CONNECTION_TIMEOUT = 2.0
MAX_CONFIGS_PER_FILE = 100

def is_valid(line):
    if not line or len(line) < 10 or len(line) > 5000: return False
    line = line.strip()
    if line.startswith(('vmess://', 'vless://', 'trojan://', 'ss://', 'ssr://')): return True
    if re.match(r'^[A-Za-z0-9+/]{20,}$', line) and len(line) < 2000:
        try: base64.b64decode(line, validate=True); return True
        except: pass
    if re.search(r'^([0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{2,5}$', line): return True
    if re.search(r'^([a-z0-9.-]+):([0-9]{2,5})$', line, re.IGNORECASE): return True
    return False

def http_get(url, idx):
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            lines = [l.strip() for l in r.text.splitlines() if l.strip()]
            return (idx, lines, True)
    except: pass
    return (idx, [], False)

def gh_push(path, content):
    try:
        headers = {'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github+json'}
        url = f'https://api.github.com/repos/SEDiK-Bes/goida-vpn-configs/contents/{path}'
        r = requests.get(url, headers=headers, timeout=5)
        sha = None
        if r.status_code == 200:
            sha = r.json()['sha']
        data = {'message': f'update {path}', 'content': base64.b64encode(content.encode('utf-8')).decode('ascii')}
        if sha: data['sha'] = sha
        r = requests.put(url, headers=headers, json=data, timeout=10)
        return r.status_code in (200, 201)
    except:
        return False

def extract_host_port(config_line):
    """Extract host:port from config string (vmess/vless/trojan/ss)"""
    try:
        config_line = config_line.strip()
        # vmess base64
        if config_line.startswith('vmess://'):
            try:
                payload = config_line[8:]
                rem = len(payload) % 4
                if rem:
                    payload += '=' * (4 - rem)
                decoded = base64.b64decode(payload).decode('utf-8', errors='ignore')
                if decoded.startswith('{'):
                    j = eval(decoded)
                    host = j.get('add') or j.get('host') or j.get('ip')
                    port = j.get('port')
                    if host and port:
                        return (str(host), int(port))
            except: pass
        # vless/trojan/ss pattern: proto://...@host:port
        match = re.search(r'@([^:/?]+):([0-9]{2,5})', config_line)
        if match:
            return (match.group(1), int(match.group(2)))
    except: pass
    return (None, None)

def extract_country(config_line):
    """Extract country code/name from config fragment (after #)"""
    try:
        if '#' in config_line:
            fragment = config_line.split('#', 1)[1]
            fragment = html.unescape(urllib.parse.unquote(fragment)).upper()
            # Look for 2-letter country code
            for cc in EUROPEAN_COUNTRIES:
                if cc in fragment:
                    return cc
    except: pass
    return None

def check_ping(host, port):
    """Measure ping as TCP connect time in ms"""
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
    except: pass
    return -1

def test_config(config_line):
    """Test single config and return (config, ping_ms, country_code)"""
    host, port = extract_host_port(config_line)
    if not host or not port:
        return (config_line, -1, None)
    ping_ms = check_ping(host, port)
    country = extract_country(config_line)
    return (config_line, ping_ms, country)

def generate_s_happ(all_configs):
    """Generate s-happ.txt: rank European configs by ping, select top 10 countries"""
    log_t(f'PHASE 3B: Testing {len(all_configs)} configs for ping and country...')
    
    tested = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = [ex.submit(test_config, cfg) for cfg in all_configs]
        for f in as_completed(futures):
            tested.append(f.result())
    
    # Group by country
    by_country = defaultdict(list)
    for cfg, ping_ms, country in tested:
        if ping_ms > 0 and country:  # Only successful, country-detected configs
            by_country[country].append((cfg, ping_ms))
    
    log_t(f'Found {len(by_country)} European countries with live configs')
    
    # Sort within each country by ping
    for cc in by_country:
        by_country[cc].sort(key=lambda x: x[1])
    
    # Select top 10 countries by: count (>=3) + avg ping
    country_stats = []
    for cc in by_country:
        if len(by_country[cc]) >= 3:
            avg_ping = sum(p for _, p in by_country[cc][:5]) / len(by_country[cc][:5])
            country_stats.append((cc, len(by_country[cc]), avg_ping))
    
    country_stats.sort(key=lambda x: (x[2], -x[1]))  # Sort by avg ping, then by count
    top_10_countries = [cc for cc, _, _ in country_stats[:10]]
    
    log_t(f'Selected top 10 countries: {", ".join(sorted(top_10_countries))}')
    
    # Build output
    output_lines = []
    for country in sorted(top_10_countries):
        output_lines.append(f'# {country}')
        # Take top 3-5 per country
        for cfg, ping_ms in by_country[country][:5]:
            output_lines.append(cfg)
    
    return '\n'.join(output_lines)

# === DOWNLOAD ===
log_t('PHASE 1: Downloading sources...')
all_configs = []
with ThreadPoolExecutor(max_workers=25) as ex:
    futures = {ex.submit(http_get, url, i): i for i, url in enumerate(SOURCES, 1)}
    for f in as_completed(futures):
        idx, lines, success = f.result()
        if success:
            valids = [l for l in lines if is_valid(l)][:150]
            all_configs.extend(valids)

log_t(f'Downloaded: {len(all_configs)} total configs')

# === SNI ===
log_t('PHASE 2: SNI sources...')
sni = []
with ThreadPoolExecutor(max_workers=3) as ex:
    futures = {ex.submit(http_get, url, i): i for i, url in enumerate(SNI_SOURCES)}
    for f in as_completed(futures):
        idx, lines, success = f.result()
        if success: sni.extend(lines)

sni_valids = [l for l in sni if is_valid(l)][:150]
all_configs.extend(sni_valids)
log_t(f'SNI: {len(sni_valids)} configs')
log_t(f'TOTAL: {len(all_configs)} before dedup')

if not all_configs:
    log_t('ERROR: No configs'); sys.exit(1)

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
    log_t(f'✗ all.txt FAILED')

# === GENERATE & PUSH s-happ.txt ===
log_t('PHASE 5: Generating s-happ.txt...')
s_happ_content = generate_s_happ(unique)
if gh_push('githubmirror/s-happ.txt', s_happ_content):
    log_t(f'✓ s-happ.txt: {len(s_happ_content.encode("utf-8")):,} bytes')
else:
    log_t(f'✗ s-happ.txt FAILED')

elapsed = time.time() - START
print(f'\n✅ SUCCESS! Time: {elapsed:.1f}s')
print(f'📁 Files:')
print(f'   • all.txt: {len(unique)} configs')
print(f'   • s-happ.txt: European selection\n')
