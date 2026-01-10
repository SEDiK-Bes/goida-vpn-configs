#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, base64, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import requests

TOKEN = os.environ.get('MY_TOKEN', '').strip()
REPO_FULL = os.environ.get('REPO_NAME', 'SEDiK-Bes/goida-vpn-configs').strip()

print('\n' + '='*70)
print('[INIT] Starting GOIDA VPN v10.1 DEBUG')
print('='*70)

print(f'\n[DEBUG] Token check:')
if not TOKEN:
    print('  ERROR: MY_TOKEN is EMPTY!')
    sys.exit(1)
else:
    print(f'  OK: Token present, length={len(TOKEN)}, starts_with_ghp={TOKEN.startswith("ghp_")}')
    print(f'  Token first 20 chars: {TOKEN[:20]}...')
    if not TOKEN.startswith('ghp_'):
        print('  ERROR: Token does not start with ghp_!')
        sys.exit(1)

print(f'\n[DEBUG] Repo check:')
print(f'  REPO_NAME: {REPO_FULL}')
try:
    OWNER, REPO = REPO_FULL.split('/', 1)
    print(f'  OWNER: {OWNER}, REPO: {REPO}')
except:
    print('  ERROR: Invalid REPO_NAME format')
    sys.exit(1)

GITHUB_API = 'https://api.github.com'
START_TIME = time.time()

def log_time(msg, level='INFO'):
    elapsed = time.time() - START_TIME
    print(f'[{elapsed:7.2f}s] [{level:5}] {msg}')

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
    if re.search(r'^([0-9]{1,3}\\.){3}[0-9]{1,3}:[0-9]{2,5}$', line): return True
    if re.search(r'^([a-z0-9.-]+):([0-9]{2,5})$', line, re.IGNORECASE): return True
    return False

def http_download(url, idx, timeout=8, retries=2):
    for attempt in range(retries):
        try:
            start = time.time()
            r = requests.get(url, timeout=timeout)
            elapsed = time.time() - start
            if r.status_code == 200:
                return (idx, r.text, elapsed, True, None)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                return (idx, '', 0, False, str(e))
    return (idx, '', 0, False, 'Unknown error')

def gh_get_sha(path):
    try:
        r = requests.get(f'{GITHUB_API}/repos/{OWNER}/{REPO}/contents/{path}', headers=gh_headers(), timeout=5)
        if r.status_code == 200: return r.json()['sha']
    except: pass
    return None

def gh_push_file(path, content, message):
    try:
        url = f'{GITHUB_API}/repos/{OWNER}/{REPO}/contents/{path}'
        sha = gh_get_sha(path)
        data = {'message': message, 'content': base64.b64encode(content.encode('utf-8')).decode('ascii')}
        if sha: data['sha'] = sha
        r = requests.put(url, headers=gh_headers(), json=data, timeout=10)
        success = r.status_code in (200, 201)
        return (success, r.status_code, None if success else r.text[:200])
    except Exception as e:
        return (False, 0, str(e))

def gh_verify_all_txt():
    try:
        r = requests.get(f'{GITHUB_API}/repos/{OWNER}/{REPO}/contents/githubmirror/all.txt', headers=gh_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            decoded = base64.b64decode(data['content'])
            lines = decoded.count(b'\n') + 1 if decoded else 0
            return (True, lines, data.get('size', 0))
        else:
            return (False, 0, 0)
    except Exception as e:
        return (False, 0, 0)

def main():
    log_time('='*70, 'START')
    
    all_configs = set()
    source_stats = defaultdict(int)
    
    log_time('PHASE 1: Downloading 25 sources in parallel...', 'PHASE')
    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = {executor.submit(http_download, url, idx): idx for idx, url in enumerate(SOURCES, 1)}
        success_count = 0
        fail_count = 0
        
        for future in as_completed(futures):
            idx, data, elapsed, success, error = future.result()
            
            if not success:
                fail_count += 1
                log_time(f'Source {idx}: FAIL ({error})', 'ERROR')
                continue
            
            if not data:
                log_time(f'Source {idx}: empty ({elapsed:.2f}s)', 'WARN')
                continue
            
            lines = [l.strip() for l in data.splitlines() if l.strip()]
            log_time(f'Source {idx}: downloaded {len(lines)} lines ({elapsed:.2f}s)', 'DEBUG')
            
            valids = [l for l in lines if is_valid_config(l)]
            log_time(f'Source {idx}: {len(valids)} valid configs (filtered)', 'DEBUG')
            
            if not valids:
                log_time(f'Source {idx}: no valid configs', 'WARN')
                continue
            
            valids = valids[:150]
            all_configs.update(valids)
            source_stats[idx] = len(valids)
            success_count += 1
            log_time(f'Source {idx}: OK - {len(valids)} configs added', 'OK')
    
    log_time(f'Downloads complete: {success_count}/25 OK, {fail_count} FAILED', 'STAT')
    log_time(f'Total configs so far: {len(all_configs)}', 'STAT')
    
    log_time('PHASE 2: Processing SNI sources...', 'PHASE')
    sni_all = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(http_download, url, idx): idx for idx, url in enumerate(SNI_SOURCES, 26)}
        for future in as_completed(futures):
            idx, data, elapsed, success, error = future.result()
            if success and data:
                sni_all.extend([l.strip() for l in data.splitlines() if l.strip()])
    
    sni_valids = [l for l in sni_all if is_valid_config(l)][:150]
    if sni_valids:
        all_configs.update(sni_valids)
        source_stats[26] = len(sni_valids)
        log_time(f'SNI (26): {len(sni_valids)} configs', 'OK')
    
    log_time(f'Total after SNI: {len(all_configs)} configs', 'STAT')
    
    if len(all_configs) == 0:
        log_time('CRITICAL: No configs collected! all_configs is empty!', 'ERROR')
        log_time('This is why all.txt will be empty', 'ERROR')
        sys.exit(1)
    
    log_time(f'PHASE 3: Pushing {len(source_stats)} files to GitHub...', 'PHASE')
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {}
        config_list = list(all_configs)
        
        for idx, count in source_stats.items():
            content = '\n'.join(config_list[:count])
            futures[executor.submit(gh_push_file, f'githubmirror/{idx}.txt', content, f'update {idx}.txt')] = idx
        
        push_success = 0
        push_fail = 0
        for future in as_completed(futures):
            success, status, error = future.result()
            idx = futures.get(future, '?')
            if success:
                push_success += 1
                log_time(f'Pushed {idx}.txt: HTTP {status} OK', 'OK')
            else:
                push_fail += 1
                log_time(f'Pushed {idx}.txt: HTTP {status} FAIL - {error}', 'ERROR')
    
    log_time(f'Push complete: {push_success} OK, {push_fail} FAILED', 'STAT')
    
    log_time(f'PHASE 4: Creating all.txt with {len(all_configs)} configs...', 'PHASE')
    all_list = sorted(all_configs)
    all_content = '\n'.join(all_list)
    log_time(f'all.txt size: {len(all_list)} lines, {len(all_content)} bytes', 'STAT')
    
    if len(all_content) == 0:
        log_time('CRITICAL: all_content is EMPTY!', 'ERROR')
        sys.exit(1)
    
    success, status, error = gh_push_file('githubmirror/all.txt', all_content, 'update all.txt')
    if success:
        log_time(f'all.txt pushed: HTTP {status} OK', 'OK')
    else:
        log_time(f'all.txt push FAILED: HTTP {status} - {error}', 'ERROR')
        sys.exit(1)
    
    log_time('PHASE 5: Verifying all.txt on GitHub...', 'PHASE')
    success, lines, size = gh_verify_all_txt()
    if success:
        elapsed = time.time() - START_TIME
        log_time(f'VERIFIED: {lines} configs, {size} bytes', 'OK')
        print('\n' + '='*70)
        print(f'SUCCESS! Time: {elapsed:.2f}s')
        print('='*70 + '\n')
    else:
        log_time('VERIFICATION FAILED!', 'ERROR')
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log_time(f'EXCEPTION: {e}', 'ERROR')
        import traceback
        traceback.print_exc()
        sys.exit(1)
