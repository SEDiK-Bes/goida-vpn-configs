#!/usr/bin/env python3
"""GOIDA VPN v12.0 FINAL - Split by SIZE, not by COUNT"""
import os, sys, base64, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

TOKEN = os.environ.get('MY_TOKEN', '').strip()
if not TOKEN or not TOKEN.startswith('ghp_'):
    print('ERROR: Invalid MY_TOKEN'); sys.exit(1)

START = time.time()
print('\n' + '='*70)
print('🔥 GOIDA VPN v12.0 FINAL - SPLIT BY SIZE')
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

def is_valid(line):
    if not line or len(line) < 10: return False
    line = line.strip()
    if line.startswith(('vmess://', 'vless://', 'trojan://', 'ss://', 'ssr://')): return True
    if re.match(r'^[A-Za-z0-9+/]{20,}', line):
        try: base64.b64decode(line, validate=True); return True
        except: pass
    if re.search(r'^([0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{2,5}$', line): return True
    if re.search(r'^([a-z0-9.-]+):([0-9]{2,5})$', line, re.IGNORECASE): return True
    return False

def http_get(url, idx):
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            return (idx, [l.strip() for l in r.text.splitlines() if l.strip()], True)
    except: pass
    return (idx, [], False)

def gh_headers():
    return {'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github+json'}

def gh_push(path, content):
    try:
        url = f'https://api.github.com/repos/SEDiK-Bes/goida-vpn-configs/contents/{path}'
        r = requests.get(url, headers=gh_headers(), timeout=5)
        sha = None
        if r.status_code == 200:
            sha = r.json()['sha']
        data = {'message': f'update {path}', 'content': base64.b64encode(content.encode('utf-8')).decode('ascii')}
        if sha: data['sha'] = sha
        r = requests.put(url, headers=gh_headers(), json=data, timeout=10)
        return r.status_code in (200, 201)
    except:
        return False

# === PHASE 1: Download ===
log_t('PHASE 1: Downloading sources...')
all_configs = []
with ThreadPoolExecutor(max_workers=25) as ex:
    futures = {ex.submit(http_get, url, i): i for i, url in enumerate(SOURCES, 1)}
    ok_count = 0
    for f in as_completed(futures):
        idx, data, success = f.result()
        if success and data:
            valids = [l for l in data if is_valid(l)][:150]
            if valids:
                all_configs.extend(valids)
                ok_count += 1
                log_t(f'✓ Source {idx}: {len(valids)} configs')

log_t(f'Downloaded: {ok_count}/25 sources, {len(all_configs)} total')

# === PHASE 2: SNI ===
log_t('PHASE 2: SNI sources...')
sni = []
with ThreadPoolExecutor(max_workers=3) as ex:
    futures = {ex.submit(http_get, url, i): i for i, url in enumerate(SNI_SOURCES)}
    for f in as_completed(futures):
        idx, data, success = f.result()
        if success and data: sni.extend(data)

sni_valids = [l for l in sni if is_valid(l)][:150]
all_configs.extend(sni_valids)
log_t(f'SNI: {len(sni_valids)} configs')
log_t(f'TOTAL before dedup: {len(all_configs)} configs')

if not all_configs:
    log_t('ERROR: No configs collected!'); sys.exit(1)

# === PHASE 3: Dedup & Sort ===
log_t('PHASE 3: Deduplicating...')
unique = sorted(list(set(all_configs)))
log_t(f'Unique: {len(unique)} configs')

# === PHASE 4: Split by SIZE (not count) ===
log_t('PHASE 4: Splitting by SIZE (2.5MB per file)...')
MAX_SIZE = 2500000  # 2.5MB max per file
parts = []
current = []
current_size = 0

for config in unique:
    config_bytes = len(config.encode('utf-8')) + 1  # +1 for newline
    if current_size + config_bytes > MAX_SIZE and current:
        parts.append(current)
        current = []
        current_size = 0
    current.append(config)
    current_size += config_bytes

if current:
    parts.append(current)

for i, p in enumerate(parts, 1):
    size = len('\n'.join(p).encode('utf-8'))
    log_t(f'Part {i}: {len(p)} configs ({size:,} bytes)')

# === PHASE 5: Push to GitHub ===
log_t('PHASE 5: Pushing to GitHub...')
push_ok = 0
for i, p in enumerate(parts, 1):
    path = f'githubmirror/all_{i:03d}.txt'
    content = '\n'.join(p)
    if gh_push(path, content):
        size = len(content.encode('utf-8'))
        log_t(f'✓ {path} ({size:,} bytes)')
        push_ok += 1
    else:
        log_t(f'✗ {path} FAILED')
    time.sleep(0.3)

# all.txt combined
log_t('PHASE 6: Creating all.txt...')
all_content = '\n'.join(unique)
if gh_push('githubmirror/all.txt', all_content):
    size = len(all_content.encode('utf-8'))
    log_t(f'✓ all.txt ({size:,} bytes)')
    push_ok += 1
else:
    log_t(f'✗ all.txt FAILED')

elapsed = time.time() - START
print(f'\n✅ SUCCESS! Time: {elapsed:.1f}s')
print(f'📊 Total: {len(unique)} unique configs')
print(f'📁 Files: {len(parts)} split files + all.txt')
print(f'✓ Pushed: {push_ok}/{len(parts)+1} files\n')
