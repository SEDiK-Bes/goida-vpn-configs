#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GOIDA VPN Aggregator v8.0 - CLEAN API VERSION
Работает только через requests + GitHub REST API.
Создаёт githubmirror/1-26.txt + all.txt и заливает на GitHub.
"""

import os
import sys
import time
import json
import re
import base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import requests

# =============== КОНФИГ ===============
TOKEN = os.environ.get("MY_TOKEN", "").strip()
REPO_FULL = os.environ.get("REPO_NAME", "SEDiK-Bes/goida-vpn-configs").strip()

if not TOKEN or not TOKEN.startswith("ghp_"):
    print("❌ MY_TOKEN не задан или неправильный формат (должен начинаться с ghp_)")
    sys.exit(1)

try:
    OWNER, REPO = REPO_FULL.split("/", 1)
except ValueError:
    print("❌ REPO_NAME должен быть вида 'USER/REPO', сейчас:", REPO_FULL)
    sys.exit(1)

GITHUB_API = "https://api.github.com"


def gh_headers():
    return {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github+json",
    }


# =============== ИСТОЧНИКИ ===============
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


# =============== ВСПОМОГАТЕЛЬНЫЕ ===============
def is_valid(line: str) -> bool:
    if not line or len(line) < 10:
        return False
    if line.startswith(("vmess://", "vless://", "trojan://", "ss://", "ssr://")):
        return True
    if re.search(r"([a-z0-9\.-]+):(\d{2,5})", line, re.I):
        return True
    return False


def http_get(url: str, timeout: int = 15) -> str:
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.text
        else:
            print(f"⚠️  {url} -> HTTP {r.status_code}")
            return ""
    except Exception as e:
        print(f"⚠️  {url} -> {e}")
        return ""


def gh_get_file_sha(path: str):
    url = f"{GITHUB_API}/repos/{OWNER}/{REPO}/contents/{path}"
    r = requests.get(url, headers=gh_headers())
    if r.status_code == 200:
        return r.json()["sha"]
    elif r.status_code == 404:
        return None
    else:
        print(f"❌ get_contents {path}: {r.status_code} {r.text}")
        return None


def gh_put_file(path: str, content: str, message: str):
    url = f"{GITHUB_API}/repos/{OWNER}/{REPO}/contents/{path}"
    sha = gh_get_file_sha(path)
    data = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
    }
    if sha:
        data["sha"] = sha

    r = requests.put(url, headers=gh_headers(), data=json.dumps(data))
    if r.status_code in (200, 201):
        print(f"✅ GITHUB {path} ({'update' if sha else 'create'})")
        return True
    else:
        print(f"❌ GITHUB {path}: {r.status_code} {r.text}")
        return False


def gh_verify_all_txt() -> bool:
    url = f"{GITHUB_API}/repos/{OWNER}/{REPO}/contents/githubmirror/all.txt"
    r = requests.get(url, headers=gh_headers())
    if r.status_code == 200:
        j = r.json()
        size = j.get("size", 0)
        decoded = base64.b64decode(j["content"])
        lines = decoded.count(b"\n") + 1 if decoded else 0
        print(f"🎉 VERIFIED all.txt на GitHub: size={size} bytes, ~{lines} строк")
        print(f"🔗 https://github.com/{OWNER}/{REPO}/blob/main/githubmirror/all.txt")
        return True
    else:
        print(f"❌ VERIFY all.txt: {r.status_code} {r.text}")
        return False


# =============== MAIN ===============
def main():
    print("=" * 70)
    print("🚀 GOIDA VPN v8.0 – CLEAN GITHUB API")
    print("=" * 70)
    print(f"Repo: {OWNER}/{REPO}")
    print()

    Path("githubmirror").mkdir(exist_ok=True)

    all_configs = set()

    print("⬇️  Загрузка обычных источников...")
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(http_get, url) for url in SOURCES]
        for idx, fut in enumerate(futures, start=1):
            data = fut.result()
            if not data:
                continue
            lines = [l.strip() for l in data.splitlines() if l.strip()]
            valids = [l for l in lines if is_valid(l)]
            if not valids:
                continue
            valids = valids[:150]
            all_configs.update(valids)
            local_path = Path("githubmirror") / f"{idx}.txt"
            local_path.write_text("\n".join(valids), encoding="utf-8")
            print(f"📁 {local_path} -> {len(valids)} строк")

    print("\n🛡️  Загрузка SNI источников (26.txt)...")
    sni_all = []
    for url in SNI_SOURCES:
        data = http_get(url)
        if not data:
            continue
        sni_all.extend([l.strip() for l in data.splitlines() if l.strip()])
    sni_valids = [l for l in sni_all if is_valid(l)][:150]
    if sni_valids:
        Path("githubmirror/26.txt").write_text("\n".join(sni_valids), encoding="utf-8")
        all_configs.update(sni_valids)
        print(f"📁 githubmirror/26.txt -> {len(sni_valids)} строк")

    print("\n🔗 Формирование all.txt...")
    all_list = sorted(all_configs)
    all_content = "\n".join(all_list)
    Path("githubmirror/all.txt").write_text(all_content, encoding="utf-8")
    print(f"✨ all.txt локально: {len(all_list)} строк")

    print("\n📤 Заливка на GitHub...")
    # 1-26
    for i in range(1, 27):
        p = Path("githubmirror") / f"{i}.txt"
        if p.exists():
            text = p.read_text(encoding="utf-8")
            gh_put_file(f"githubmirror/{i}.txt", text, f"update {i}.txt")

    # all.txt
    gh_put_file("githubmirror/all.txt", all_content, "update all.txt")

    print("\n🔍 Проверка all.txt на GitHub...")
    ok = gh_verify_all_txt()
    if not ok:
        print("❌ КРИТИЧЕСКО: all.txt НЕ ПРОШЁЛ ПРОВЕРКУ!")
        sys.exit(1)

    print("\n✅ ГОТОВО. all.txt СУЩЕСТВУЕТ НА GITHUB.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⛔ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ НЕОБРАБОТАННАЯ ОШИБКА: {e}")
        sys.exit(1)
