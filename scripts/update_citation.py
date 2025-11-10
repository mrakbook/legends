#!/usr/bin/env python3
import argparse, re, sys
from datetime import date
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--version", required=True)
ap.add_argument("--path", default="CITATION.cff")
args = ap.parse_args()

p = Path(args.path)
if not p.exists():
    sys.exit(0)

text = p.read_text(encoding="utf-8")
today = date.today().isoformat()

text = re.sub(r'(?m)^version:\s*".*"', f'version: "{args.version}"', text)
text = re.sub(r'(?m)^date-released:\s*".*"', f'date-released: "{today}"', text)

p.write_text(text, encoding="utf-8")
print(f"Updated {p} -> version={args.version}, date-released={today}")
