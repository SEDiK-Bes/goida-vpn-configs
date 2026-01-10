#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GOIDA VPN Aggregator v9.0 - GITHUB NATIVE
✅ Только GitHub, никакой локальной папки
✅ Всё в памяти + прямо на GitHub
✅ 25 источников + SNI → githubmirror/all.txt
"""

import os
import sys
import base64
import re
from concurrent.futures import ThreadPoolExecutor

import requests

# =============== CONFIG ===============
TOKEN = os.environ.get("MY_TOKEN", "").strip()
REPO_FULL = os.environ.get("REPO_NAME", "SEDiK-Bes/goida-vpn-configs").strip()

print(f"🔐 Token: {TOKEN[:20]}... (must start with ghp_)")
print(f"📦 Repo: {REPO_FULL}")

if not TOKEN or not TOKEN.startswith("ghp_"):
    print("❌ ОШИБКА: MY_TOKEN не задан или неверный формат!")
    sys.exit(1)

try:
    OWNER, REPO = REPO_FULL.split("/", 1)
except ValueError:
    print(f"❌ ОШИБКА: REPO_NAME должен быть 'USER/REPO', сейчас: {REPO_FULL}")
    sys.exit(1)

GITHUB_API = "https://api.github.com"


def gh_headers():
    """GitHub API headers"""
    return {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


# =============== SOURCES ===============
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


# =============== HELPERS ===============
def is_valid_config(line: str) -> bool:
    """Проверить валидность конфига"""
    if not line or len(line) < 10:
        return False
    if line.startswith(("vmess://", "vless://", "trojan://", "ss://", "ssr://")):
        return True
    if re.search(r"([a-z0-9\.-]+):(\d{2,5})", line, re.IGNORECASE):
        return True
    return False


def http_download(url: str, timeout: int = 15) -> str:
    """Скачать URL"""
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return ""


def gh_get_sha(path: str):
    """Получить SHA файла на GitHub"""
    url = f"{GITHUB_API}/repos/{OWNER}/{REPO}/contents/{path}"
    try:
        r = requests.get(url, headers=gh_headers(), timeout=10)
        if r.status_code == 200:
            return r.json()["sha"]
    except:
        pass
    return None


def gh_push_file(path: str, content: str, message: str) -> bool:
    """Загрузить файл на GitHub"""
    url = f"{GITHUB_API}/repos/{OWNER}/{REPO}/contents/{path}"
    sha = gh_get_sha(path)
    
    data = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
    }
    if sha:
        data["sha"] = sha
    
    try:
        r = requests.put(url, headers=gh_headers(), json=data, timeout=15)
        if r.status_code in (200, 201):
            status = "UPDATE" if sha else "CREATE"
            print(f"✅ {path} ({status})")
            return True
        else:
            print(f"❌ {path}: HTTP {r.status_code}")
            if r.text:
                try:
                    err = r.json()
                    print(f"   {err.get('message', 'N/A')}")
                except:
                    print(f"   {r.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ {path}: {e}")
        return False


def gh_verify_all_txt() -> bool:
    """Проверить что all.txt существует на GitHub"""
    url = f"{GITHUB_API}/repos/{OWNER}/{REPO}/contents/githubmirror/all.txt"
    try:
        r = requests.get(url, headers=gh_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            size = data.get("size", 0)
            decoded = base64.b64decode(data["content"])
            lines = decoded.count(b"\n") + 1 if decoded else 0
            print(f"\n🎉 VERIFIED: all.txt EXISTS on GitHub!")
            print(f"   Size: {size} bytes")
            print(f"   Lines: {lines}")
            print(f"   URL: https://github.com/{OWNER}/{REPO}/blob/main/githubmirror/all.txt")
            return True
        else:
            print(f"\n❌ all.txt NOT FOUND: HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"\n❌ VERIFY ERROR: {e}")
        return False


# =============== MAIN ===============
def main():
    print("\n" + "="*70)
    print("🚀 GOIDA VPN v9.0 - GITHUB NATIVE")
    print("="*70 + "\n")
    
    all_configs = set()
    
    # Download all sources
    print("⬇️  Downloading all sources (1-25)...\n")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(http_download, url) for url in SOURCES]
        
        for idx, future in enumerate(futures, start=1):
            data = future.result()
            if not data:
                print(f"⚠️  Source {idx}: empty")
                continue
            
            lines = [l.strip() for l in data.splitlines() if l.strip()]
            valids = [l for l in lines if is_valid_config(l)]
            
            if not valids:
                print(f"⚠️  Source {idx}: no valid configs")
                continue
            
            valids = valids[:150]
            all_configs.update(valids)
            
            # Push directly to GitHub
            file_content = "\n".join(valids)
            gh_push_file(f"githubmirror/{idx}.txt", file_content, f"🚀 update {idx}.txt")
    
    # Process SNI sources (26.txt)
    print("\n🛡️  Processing SNI sources (26.txt)...\n")
    sni_all = []
    for url in SNI_SOURCES:
        data = http_download(url)
        if data:
            sni_all.extend([l.strip() for l in data.splitlines() if l.strip()])
    
    sni_valids = [l for l in sni_all if is_valid_config(l)][:150]
    if sni_valids:
        sni_content = "\n".join(sni_valids)
        gh_push_file("githubmirror/26.txt", sni_content, "🚀 update 26.txt (SNI)")
        all_configs.update(sni_valids)
        print(f"📁 26.txt: {len(sni_valids)} configs")
    
    # Create all.txt (в памяти, потом на GitHub)
    print("\n🔗 Creating all.txt...\n")
    all_list = sorted(all_configs)
    all_content = "\n".join(all_list)
    print(f"✨ all.txt (memory): {len(all_list)} configs")
    
    # Push all.txt to GitHub
    print("\n📤 Pushing all.txt to GitHub...\n")
    gh_push_file("githubmirror/all.txt", all_content, "🚀 update all.txt (AGGREGATED)")
    
    # Verify
    print("\n🔍 Verifying all.txt on GitHub...\n")
    if gh_verify_all_txt():
        print("\n" + "="*70)
        print("✅ SUCCESS! all.txt IS ON GITHUB")
        print("="*70 + "\n")
        return True
    else:
        print("\n" + "="*70)
        print("❌ FAILED: all.txt verification failed")
        print("="*70 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⛔ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
