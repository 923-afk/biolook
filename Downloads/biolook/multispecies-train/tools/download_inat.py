#!/usr/bin/env python3
"""
download_inat.py
從 iNaturalist public API 下載影像，並按 label 存放成 data/train/<label>/... 和 data/val/<label>/...
用法：
  python tools/download_inat.py --taxa-file taxa_list.txt --out data --per-species 500 --val-split 0.2
taxa_list.txt 格式：每行一個關鍵詞或 taxon_id（若是數字會被視為 taxon_id）
"""
import os, sys, argparse, requests, time, math
from pathlib import Path
from tqdm import tqdm
import shutil
import random

API_URL = "https://api.inaturalist.org/v1/observations"

def fetch_observations(q=None, taxon_id=None, page=1, per_page=80):
    params = {
        "page": page,
        "per_page": per_page,
        "photo_license": "cc-by,cc-by-sa",
        "quality_grade": "research",
        "order": "desc",
        "order_by": "created_at"
    }
    if q:
        params["q"] = q
    if taxon_id:
        params["taxon_id"] = taxon_id
    r = requests.get(API_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def download_url(url, dst_path):
    try:
        r = requests.get(url, stream=True, timeout=20)
        r.raise_for_status()
        with open(dst_path, "wb") as f:
            shutil.copyfileobj(r.raw, f)
        return True
    except Exception as e:
        return False

def ensure_dir(p):
    Path(p).mkdir(parents=True, exist_ok=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--taxa-file", required=True, help="每行一個 taxa 名稱或 taxon_id")
    parser.add_argument("--out", default="data", help="輸出資料夾")
    parser.add_argument("--per-species", type=int, default=300, help="每個 species 最多抓幾張")
    parser.add_argument("--val-split", type=float, default=0.2, help="驗證集比例")
    parser.add_argument("--max-pages", type=int, default=50, help="每個查詢最多頁數（每頁最多 80）")
    args = parser.parse_args()

    with open(args.taxa_file, "r", encoding="utf-8") as f:
        taxa = [line.strip() for line in f if line.strip()]

    for term in taxa:
        print(f"Processing: {term}")
        label = term.replace(" ", "_")
        train_dir = Path(args.out) / "train" / label
        val_dir = Path(args.out) / "val" / label
        ensure_dir(train_dir); ensure_dir(val_dir)

        downloaded = 0
        page = 1
        per_page = 80
        imgs = []

        while downloaded < args.per_species and page <= args.max_pages:
            try:
                if term.isdigit():
                    js = fetch_observations(taxon_id=int(term), page=page, per_page=per_page)
                else:
                    js = fetch_observations(q=term, page=page, per_page=per_page)
            except Exception as e:
                print("API error:", e)
                time.sleep(2)
                page += 1
                continue

            results = js.get("results", [])
            if not results:
                break

            for obs in results:
                if downloaded >= args.per_species:
                    break
                photos = obs.get("photos") or []
                for p in photos:
                    # try to get original size photo url
                    url = p.get("url")
                    if not url:
                        continue
                    # iNaturalist photo urls may have {size} tokens, replace with 'original' or 'medium'
                    url = url.replace("square", "original")
                    imgs.append(url)
                downloaded = len(imgs)
            page += 1
            time.sleep(0.3)  # friendly pause

        # dedupe
        imgs = list(dict.fromkeys(imgs))
        print(f"Found {len(imgs)} images for {term}")
        random.shuffle(imgs)
        imgs = imgs[:args.per_species]

        split_at = int(len(imgs) * (1 - args.val_split))
        for i, url in enumerate(tqdm(imgs, desc=label)):
            dst = train_dir if i < split_at else val_dir
            ext = ".jpg"
            fname = f"{i:06d}{ext}"
            dst_path = dst / fname
            success = download_url(url, dst_path)
            if not success and dst_path.exists():
                dst_path.unlink()

    print("Done.")
if __name__ == "__main__":
    main()


