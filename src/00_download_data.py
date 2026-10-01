"""03-supplychain-retail — download UCI Online Retail II (public).

Source: https://archive.ics.uci.edu/dataset/502/online+retail+ii
~525k transactions (invoices) of a UK online retailer, Dec 2009 – Dec 2011.
"""
from pathlib import Path
import sys

_shared_root = Path(__file__).resolve().parent
while _shared_root != _shared_root.parent and not (_shared_root / "shared").is_dir():
    _shared_root = _shared_root.parent
sys.path.insert(0, str(_shared_root))  # callable from repo root or standalone checkout
from shared.utils import download, unzip   # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"


def main() -> None:
    raw = PROJECT / "data" / "raw"
    ziph = download(URL, raw / "online_retail_ii.zip", "UCI Online Retail II")
    unzip(ziph, raw)
    print("[done] unzipped:", [p.name for p in sorted(raw.glob('*.xlsx'))])


if __name__ == "__main__":
    main()
