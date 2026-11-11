"""Download the source reports listed in config/sources.yaml.

PDFs go to data/raw/ (git-ignored). A manifest records the URL, date and SHA-256
of each file so results can be tied to the exact document that produced them.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
from pathlib import Path

import requests
import yaml

USER_AGENT = "fund-report-extractor/0.1 (portfolio research project)"


def load_sources(config_path: str | Path) -> list[dict]:
    with open(config_path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}
    return [s for s in cfg.get("reports", []) if s.get("url") and "TODO" not in str(s.get("url"))]


def download_all(config_path: str | Path, raw_dir: str | Path = "data/raw", force: bool = False) -> list[Path]:
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest = raw_dir / "manifest.csv"
    new_manifest = not manifest.exists()
    saved = []
    with open(manifest, "a", newline="", encoding="utf-8") as mf:
        writer = csv.writer(mf)
        if new_manifest:
            writer.writerow(["report_id", "url", "downloaded_utc", "sha256", "bytes"])
        for src in load_sources(config_path):
            out = raw_dir / f"{src['id']}.pdf"
            if out.exists() and not force:
                print(f"skip  {out.name} (exists)")
                saved.append(out)
                continue
            resp = requests.get(src["url"], headers={"User-Agent": USER_AGENT}, timeout=60)
            resp.raise_for_status()
            out.write_bytes(resp.content)
            digest = hashlib.sha256(resp.content).hexdigest()
            writer.writerow([src["id"], src["url"], dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), digest, len(resp.content)])
            print(f"saved {out.name} ({len(resp.content):,} bytes)")
            saved.append(out)
    if not saved:
        print("No reports configured yet: add URLs to config/sources.yaml.")
    return saved
