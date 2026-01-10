#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GOIDA VPN Aggregator v11.0 - 3 file split"""
import os, sys, base64, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

TOKEN = os.environ.get('MY_TOKEN', '').strip()
REPO_FULL = os.environ.get('REPO_NAME', 'SEDiK-Bes/goida-vpn-configs').strip()
OWNER, REPO = REPO_FULL.split('/')
GITHUB_API = 'https://api.github.com'
START = time.time()

print('\n' + '='*70)
print('🚀 GOIDA VPN v11.0 - 3 FILE SPLIT')
print('='*70 + '\n')

if not TOKEN or not TOKEN.startswith('ghp_'):
    print('ERROR: Invalid MY_TOKEN'); sys.exit(1)

def log_t(msg, lv='OK'):
    print(f'[{time.time()-START:6.2f}s] [{lv:5}] {msg}')

def gh_headers():
    return {'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github+json'}

def gh_get_sha(path):
    try:
        r = requests.get(f'{GITHUB_API}/repos/{OWNER}/{REPO}/contents/{path}', headers=gh_headers(), timeout=5)
        if r.status_code == 200: return r.json()['sha']
    except: pass
    return None

def gh_push(path, content, msg):
    try:
        url = f'{GITHUB_API}/repos/{OWNER}/{REPO}/contents/{path}'
        sha = gh_get_sha(path)
        data = {'message': msg, 'content': base64.b64encode(content.encode('utf-8')).decode('ascii')}
        if sha: data['sha'] = sha
        r = requests.put(url, headers=gh_headers(), json=data, timeout=10)
        return (r.status_code in (200, 201), r.status_code)
    except: return (False, 0)

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
        start = time.time()
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            return (idx, [l.strip() for l in r.text.splitlines() if l.strip()], time.time()-start, True)
    except: pass
    return (idx, [], 0, False)

# === PHASE 1: Download ===
log_t('PHASE 1: Downloading 25 sources...', 'PHASE')
configs = set()
with ThreadPoolExecutor(max_workers=25) as ex:
    futures = {ex.submit(http_get, url, i): i for i, url in enumerate(SOURCES, 1)}
    ok = 0
    for f in as_completed(futures):
        idx, data, elapsed, success = f.result()
        if not success or not data: continue
        valids = [l for l in data if is_valid(l)][:150]
        if valids:
            configs.update(valids)
            ok += 1
            log_t(f'Source {idx}: {len(valids)} configs ({elapsed:.2f}s)', 'OK')

log_t(f'Downloaded: {ok}/25 sources, {len(configs)} total', 'STAT')

# === PHASE 2: SNI ===
log_t('PHASE 2: SNI sources...', 'PHASE')
sni = []
with ThreadPoolExecutor(max_workers=3) as ex:
    futures = {ex.submit(http_get, url, i): i for i, url in enumerate(SNI_SOURCES, 26)}
    for f in as_completed(futures):
        idx, data, _, success = f.result()
        if success and data: sni.extend(data)

sni_valids = [l for l in sni if is_valid(l)][:150]
configs.update(sni_valids)
log_t(f'SNI: {len(sni_valids)} configs', 'OK')
log_t(f'TOTAL: {len(configs)} configs', 'STAT')

if not configs:
    log_t('ERROR: No configs!', 'ERROR')
    sys.exit(1)

# === PHASE 3: Split into 3 files ===
log_t('PHASE 3: Splitting into 3 files...', 'PHASE')
all_list = sorted(list(configs))
chunk_size = len(all_list) // 3

parts = [
    all_list[:chunk_size],
    all_list[chunk_size:2*chunk_size],
    all_list[2*chunk_size:]
]

for i, part in enumerate(parts, 1):
    if part:
        size = len('\n'.join(part).encode('utf-8'))
        log_t(f'Part {i}: {len(part)} configs ({size:,} bytes)', 'INFO')

# === PHASE 4: Push ===
log_t('PHASE 4: Pushing to GitHub...', 'PHASE')
for i, part in enumerate(parts, 1):
    if not part: continue
    content = '\n'.join(part)
    path = f'githubmirror/all_{i:03d}.txt'
    success, status = gh_push(path, content, f'update all_{i:03d}.txt')
    if success:
        log_t(f'Pushed {path}: HTTP {status}', 'OK')
    else:
        log_t(f'FAILED {path}: HTTP {status}', 'ERROR')
    time.sleep(0.5)

# === PHASE 5: Combine into all.txt ===
log_t('PHASE 5: Creating combined all.txt...', 'PHASE')
all_content = '\n'.join(all_list)
success, status = gh_push('githubmirror/all.txt', all_content, 'update all.txt (combined)')
if success:
    log_t(f'all.txt: HTTP {status}', 'OK')
else:
    log_t(f'all.txt FAILED: HTTP {status}', 'ERROR')

elapsed = time.time() - START
print(f'\n✅ DONE! Time: {elapsed:.2f}s')
print(f'📊 Total: {len(all_list)} configs')
print(f'📁 Files: all.txt + all_001.txt, all_002.txt, all_003.txt\n')
