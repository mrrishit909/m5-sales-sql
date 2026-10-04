"""Step 1: the M5 Forecasting dataset (Walmart unit sales, Makridakis Open Forecasting Center), from its Zenodo record.

    ./venv/bin/python download.py   -> data/*.csv (unzipped), results/pull.json

Source: https://zenodo.org/records/12636070 (DOI 10.5281/zenodo.12636070), licence CC BY 4.0 (checked on the record's API).
Citation: Makridakis, Spiliotis, Assimakopoulos (2022), "The M5 competition: Background, organization, and implementation", Int. J. Forecasting 38(4).
Not committed: data/ (the 48 MB zip and the CSVs). Only small aggregate tables in results/ are committed.
"""
import hashlib
import json
import ssl
import time
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

import certifi

HERE = Path(__file__).parent
DATA = HERE / "data"
URL = "https://zenodo.org/api/records/12636070/files/m5-forecasting-accuracy.zip/content"
MD5 = "86f57416a314197f40a17cc6fc60cbb4"                  # from the record's file listing
CTX = ssl.create_default_context(cafile=certifi.where())


def fetch(dest):
    for attempt in range(4):
        try:
            req = urllib.request.Request(URL, headers={"User-Agent": "research-portfolio (Rishit Raj Mathur)"})
            with urllib.request.urlopen(req, context=CTX, timeout=120) as r, open(dest, "wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            return
        except Exception as e:
            print("retry", attempt, e)
            time.sleep(5 * (attempt + 1))
    raise SystemExit("download failed")


def main():
    DATA.mkdir(exist_ok=True)
    (HERE / "results").mkdir(exist_ok=True)
    z = DATA / "m5-forecasting-accuracy.zip"
    if not z.exists():
        fetch(z)
    md5 = hashlib.md5(z.read_bytes()).hexdigest()
    assert md5 == MD5, f"md5 mismatch {md5}"
    with zipfile.ZipFile(z) as zf:
        zf.extractall(DATA)
    files = {}
    for p in sorted(DATA.glob("*.csv")):
        files[p.name] = {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    info = {"pulled": date.today().isoformat(), "url": URL, "zip_md5": md5, "zip_bytes": z.stat().st_size, "files": files}
    (HERE / "results" / "pull.json").write_text(json.dumps(info, indent=2) + "\n")
    print({k: v["bytes"] for k, v in files.items()})


if __name__ == "__main__":
    main()
