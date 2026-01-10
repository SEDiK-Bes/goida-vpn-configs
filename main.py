#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GOIDA VPN Aggregator v7.0 - FINAL GUARANTEED
🔥 Creates all.txt AND VERIFIES it on GitHub
"""

import os, sys, time, json, re, base64, socket
import requests
from pathlib import Path
from github import Github, GithubException
from concurrent.futures import ThreadPoolExecutor

# ==================== CONFIG ====================
TOKEN = os.environ.get("MY_TOKEN", "").strip()
REPO = os.environ.get("REPO_NAME", "SEDiK-Bes/goida-vpn-configs").strip()

print(f"🔐 Token: {TOKEN[:20]}..." if TOKEN else "❌ NO TOKEN")
print(f"📦 Repo: {REPO}")

if "ghp_" not in TOKEN:
    print("❌ INVALID TOKEN")
    sys.exit(1)

# ==================== SOURCES ====================
SOURCES = [
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

SNI_SOURCES = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Cable.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    "https://raw.githubusercontent.com/zieng2/wl/main/vless.txt",
]

# ==================== FUNCTIONS ====================
def download(url, timeout=10):
    try:
        r = requests.get(url, timeout=timeout)
        return r.text if r.status_code == 200 else ""
    except:
        return ""

def is_valid_config(line):
    if not line or len(line) < 10:
        return False
    if line.startswith(("vmess://", "vless://", "trojan://", "ss://", "ssr://")):
        return True
    if re.search(r'([a-z0-9.-]+):(\d{2,5})', line):
        return True
    return False

def github_push(repo, path, content):
    try:
        try:
            file_obj = repo.get_contents(path)
            repo.update_file(path, f"🚀 {path}", content, file_obj.sha)
            print(f"✅ UPDATE {path}")
            return True
        except GithubException as e:
            if e.status == 404:
                repo.create_file(path, f"🆕 {path}", content)
                print(f"✅ CREATE {path}")
                return True
            else:
                print(f"❌ {path}: {e}")
                return False
    except Exception as e:
        print(f"❌ {path}: {e}")
        return False

# ==================== MAIN ====================
print("\n" + "="*60)
print("🔥 GOIDA VPN v7.0 - FINAL")
print("="*60 + "\n")

try:
    g = Github(TOKEN)
    repo = g.get_repo(REPO)
    print(f"✅ GitHub: {repo.full_name}\n")
except Exception as e:
    print(f"❌ GitHub: {e}")
    sys.exit(1)

Path("githubmirror").mkdir(exist_ok=True)

print("⬇️  Downloading sources...\n")
all_configs = set()

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(download, url) for url in SOURCES]
    
    for i, future in enumerate(futures):
        data = future.result()
        if data:
            configs = [line.strip() for line in data.split('\n') if line.strip()]
            valid = [c for c in configs if is_valid_config(c)]
            
            if valid:
                content = '\n'.join(valid[:150])
                with open(f"githubmirror/{i+1}.txt", 'w') as f:
                    f.write(content)
                github_push(repo, f"githubmirror/{i+1}.txt", content)
                all_configs.update(valid[:150])
                print(f"📁 {i+1}.txt: {len(valid)} configs")
        
        time.sleep(0.1)

print("\n🛡️  SNI configs...")
sni_configs = []
for url in SNI_SOURCES:
    data = download(url)
    if data:
        sni_configs.extend([line.strip() for line in data.split('\n') if line.strip()])

sni_valid = [c for c in sni_configs if is_valid_config(c)][:150]
if sni_valid:
    sni_content = '\n'.join(sni_valid)
    with open("githubmirror/26.txt", 'w') as f:
        f.write(sni_content)
    github_push(repo, "githubmirror/26.txt", sni_content)
    all_configs.update(sni_valid)
    print(f"✅ 26.txt: {len(sni_valid)} configs")

print("\n" + "="*60)
print("🔗 Creating all.txt...")
all_content = '\n'.join(sorted(all_configs))
with open("githubmirror/all.txt", 'w') as f:
    f.write(all_content)
print(f"✨ all.txt: {len(all_configs)} configs (local)")
print("="*60)

print("\n📤 Pushing all.txt to GitHub...")
github_push(repo, "githubmirror/all.txt", all_content)

print("\n🔍 VERIFYING all.txt on GitHub...")
time.sleep(2)

try:
    file_obj = repo.get_contents("githubmirror/all.txt")
    file_size = len(file_obj.decoded_content)
    config_count = file_obj.decoded_content.count(b'\n') + 1
    
    print(f"\n✅ VERIFIED: all.txt EXISTS on GitHub!")
    print(f"   Size: {file_size} bytes")
    print(f"   Configs: {config_count}")
    
    print("\n" + "="*60)
    print("🎉 SUCCESS! all.txt IS ON GITHUB!")
    print("="*60)
    print(f"📂 https://github.com/{REPO}/tree/main/githubmirror\n")
    
except GithubException as e:
    print(f"\n❌ CRITICAL: all.txt NOT FOUND!")
    print(f"Error: {e}")
    sys.exit(1)
