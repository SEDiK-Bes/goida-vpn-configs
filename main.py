#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, base64, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import requests

TOKEN = os.environ.get('MY_TOKEN', '').strip()
REPO_FULL = os.environ.get('REPO_NAME', 'SEDiK-Bes/goida-vpn-configs').strip()
OWNER, REPO = REPO_FULL.split('/', 1)
GITHUB_API = 'https://api.github.com'
START_TIME = time.time()

def log_time(msg):
    elapsed = time.time() - START_TIME
    print(f'[{elapsed:6.2f}s] {msg}')

def gh_headers():
    return {
        'Authorization': f'token {TOKEN}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
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

def is_valid_config(line):
    if not line or len(line) < 10: return False
    line = line.strip()
    if line.startswith(('vmess://', 'vless://', 'trojan://', 'ss://', 'ssr://', 'socks5://')): return True
    if re.match(r'^[A-Za-z0-9+/]{20,}', line):
        try:
            base64.b64decode(line, validate=True)
            return True
        except: pass
    if re.search(r'^([0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{2,5}$', line): return True
    if re.search(r'^([a-z0-9.-]+):([0-9]{2,5})$', line, re.IGNORECASE): return True
    return False

def http_download(url, idx, timeout=8, retries=2):
    for attempt in range(retries):
        try:
            start = time.time()
            r = requests.get(url, timeout=timeout)
            elapsed = time.time() - start
            if r.status_code == 200: return (idx, r.text, elapsed, True)
        except:
            if attempt < retries - 1: time.sleep(1)
    return (idx, '', 0, False)

def gh_get_sha(path):
    try:
        r = requests.get(f'{GITHUB_API}/repos/{OWNER}/{REPO}/contents/{path}', headers=gh_headers(), timeout=5)
        if r.status_code == 200: return r.json()['sha']
    except: pass
    return None

def gh_push_file(path, content, message):
    url = f'{GITHUB_API}/repos/{OWNER}/{REPO}/contents/{path}'
    sha = gh_get_sha(path)
    data = {'message': message, 'content': base64.b64encode(content.encode('utf-8')).decode('ascii')}
    if sha: data['sha'] = sha
    try:
        r = requests.put(url, headers=gh_headers(), json=data, timeout=10)
        return r.status_code in (200, 201)
    except: return False

def gh_verify_all_txt():
    try:
        r = requests.get(f'{GITHUB_API}/repos/{OWNER}/{REPO}/contents/githubmirror/all.txt', headers=gh_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            decoded = base64.b64decode(data['content'])
            lines = decoded.count(b'\n') + 1 if decoded else 0
            log_time(f'✓ all.txt: {lines} configs, {data.get("size", 0)} bytes')
            return True
    except: pass
    return False

def main():
    print('\n' + '='*70)
    print('🚀 GOIDA VPN v10.0 - OPTIMIZED')
    print('='*70 + '\n')
    
    if not TOKEN or not TOKEN.startswith('ghp_'):
        print('❌ TOKEN ERROR'); sys.exit(1)
    
    all_configs = set()
    source_stats = defaultdict(int)
    
    log_time('⬇️  Downloading 25 sources in parallel...')
    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = {executor.submit(http_download, url, idx): idx for idx, url in enumerate(SOURCES, 1)}
        success_count = 0
        for future in as_completed(futures):
            idx, data, elapsed, success = future.result()
            if not success or not data: continue
            lines = [l.strip() for l in data.splitlines() if l.strip()]
            valids = [l for l in lines if is_valid_config(l)][:150]
            if not valids: continue
            all_configs.update(valids)
            source_stats[idx] = len(valids)
            success_count += 1
            log_time(f'  ✓ Source {idx}: {len(valids)} configs ({elapsed:.2f}s)')
    log_time(f'⬇️  Done: {success_count}/25')
    
    log_time('🛡️  Processing SNI sources...')
    sni_all = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(http_download, url, idx): idx for idx, url in enumerate(SNI_SOURCES, 26)}
        for future in as_completed(futures):
            idx, data, elapsed, success = future.result()
            if success and data: sni_all.extend([l.strip() for l in data.splitlines() if l.strip()])
    sni_valids = [l for l in sni_all if is_valid_config(l)][:150]
    if sni_valids:
        all_configs.update(sni_valids)
        source_stats[26] = len(sni_valids)
        log_time(f'🛡️  SNI: {len(sni_valids)} configs')
    
    log_time(f'📤 Parallel push {len(source_stats)} files...')
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {}
        config_list = list(all_configs)
        for idx, count in source_stats.items():
            content = '\n'.join(config_list[:count])
            futures[executor.submit(gh_push_file, f'githubmirror/{idx}.txt', content, f'🚀 {idx}.txt')] = idx
        push_success = sum(1 for f in as_completed(futures) if f.result())
    log_time(f'📤 Pushed: {push_success}/{len(source_stats)}')
    
    log_time(f'🔗 Creating all.txt ({len(all_configs)} configs)...')
    all_list = sorted(all_configs)
    all_content = '\n'.join(all_list)
    
    if gh_push_file('githubmirror/all.txt', all_content, '🚀 all.txt'):
        log_time('✓ all.txt pushed')
    else:
        sys.exit(1)
    
    if gh_verify_all_txt():
        elapsed = time.time() - START_TIME
        print('\n' + '='*70)
        print(f'✓ SUCCESS! Time: {elapsed:.2f}s')
        print('='*70 + '\n')
    else:
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'\n❌ {e}')
        sys.exit(1)
