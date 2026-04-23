#!/usr/bin/env python3
"""
Download Shakespeare's complete works as individual plays from Gutenberg,
then rebuild the curated file list.
"""
import re
import time
import random
import urllib.request
from pathlib import Path

BOOKS_DIR   = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_books")
OUTPUT_LIST = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/index_filelist.txt")

# All major Shakespeare works with known Gutenberg IDs
SHAKESPEARE_PLAYS = [
    # Tragedies
    (1524,  "01524_HAMLET.txt"),
    (1532,  "01532_KING_LEAR.txt"),
    (1533,  "01533_MACBETH.txt"),
    (1531,  "01531_OTHELLO.txt"),
    (1530,  "01530_ROMEO_AND_JULIET.txt"),
    (1529,  "01529_JULIUS_CAESAR.txt"),
    (1528,  "01528_ANTONY_AND_CLEOPATRA.txt"),
    (1527,  "01527_CORIOLANUS.txt"),
    (1526,  "01526_TITUS_ANDRONICUS.txt"),
    (1525,  "01525_TIMON_OF_ATHENS.txt"),
    (22996, "22996_TROILUS_AND_CRESSIDA.txt"),
    (1484,  "01484_PERICLES.txt"),

    # Comedies
    (1514,  "01514_A_MIDSUMMER_NIGHTS_DREAM.txt"),
    (1515,  "01515_THE_MERCHANT_OF_VENICE.txt"),
    (1516,  "01516_AS_YOU_LIKE_IT.txt"),
    (1517,  "01517_THE_TAMING_OF_THE_SHREW.txt"),
    (1518,  "01518_TWELFTH_NIGHT.txt"),
    (1519,  "01519_MUCH_ADO_ABOUT_NOTHING.txt"),
    (1520,  "01520_ALL_S_WELL_THAT_ENDS_WELL.txt"),
    (1521,  "01521_MEASURE_FOR_MEASURE.txt"),
    (1522,  "01522_THE_MERRY_WIVES_OF_WINDSOR.txt"),
    (1523,  "01523_THE_COMEDY_OF_ERRORS.txt"),
    (23042, "23042_LOVES_LABOURS_LOST.txt"),
    (23043, "23043_THE_TWO_GENTLEMEN_OF_VERONA.txt"),
    (23044, "23044_THE_WINTERS_TALE.txt"),
    (1539,  "01539_CYMBELINE.txt"),
    (1540,  "01540_THE_TEMPEST.txt"),

    # Histories
    (1507,  "01507_RICHARD_II.txt"),
    (1508,  "01508_HENRY_IV_PART_1.txt"),
    (1509,  "01509_HENRY_IV_PART_2.txt"),
    (1510,  "01510_HENRY_V.txt"),
    (1511,  "01511_HENRY_VI_PART_1.txt"),
    (1512,  "01512_HENRY_VI_PART_2.txt"),
    (1513,  "01513_HENRY_VI_PART_3.txt"),
    (2251,  "02251_RICHARD_III.txt"),
    (1541,  "01541_HENRY_VIII.txt"),
    (1542,  "01542_KING_JOHN.txt"),

    # Poems
    (1041,  "01041_THE_SONNETS.txt"),
    (1062,  "01062_VENUS_AND_ADONIS.txt"),
    (1590,  "01590_THE_RAPE_OF_LUCRECE.txt"),
]

# ── Periodical detection ───────────────────────────────────────────────────
PERIODICAL_PATTERNS = [
    r"scientific.?american", r"harper.?s", r"atlantic.?monthly",
    r"blackwood", r"punch", r"strand.?magazine", r"cornhill",
    r"chambers", r"scribner", r"century.?magazine", r"galaxy.?magazine",
    r"lippincott", r"godey", r"littell", r"living.?age",
    r"all.?the.?year.?round", r"household.?words", r"once.?a.?week",
    r"magazine", r"journal", r"review", r"quarterly", r"bulletin",
    r"proceedings", r"transactions", r"digest", r"weekly", r"monthly",
    r"annual", r"almanac", r"gazette", r"chronicle", r"newsletter",
]
PERIODICAL_RE = re.compile("|".join(PERIODICAL_PATTERNS), re.IGNORECASE)

def is_periodical(path: Path) -> bool:
    title = "_".join(path.stem.split("_")[1:])
    return bool(PERIODICAL_RE.search(title))

CANONICAL = [
    "00076_ADVENTURES_OF_HUCKLEBERRY_FINN.txt",
    "00074_THE_ADVENTURES_OF_TOM_SAWYER.txt",
    "00086_A_CONNECTICUT_YANKEE_IN_KING_ARTHURS_COURT.txt",
    "01399_ANNA_KARENINA.txt",
    "28054_THE_BROTHERS_KARAMAZOV.txt",
    "01184_THE_COUNT_OF_MONTE_CRISTO.txt",
    "01257_THE_THREE_MUSKETEERS.txt",
    "02610_THE_HUNCHBACK_OF_NOTRE_DAME.txt",
    "00012_THROUGH_THE_LOOKING_GLASS.txt",
    "00013_THE_HUNTING_OF_THE_SNARK.txt",
    "01260_JANE_EYRE.txt",
    "00145_MIDDLEMARCH.txt",
    "00033_THE_SCARLET_LETTER.txt",
    "13650_THE_OWL_AND_THE_PUSSYCAT.txt",
    "00621_THE_VARIETIES_OF_RELIGIOUS_EXPERIENCE.txt",
]

START_RE = re.compile(
    r"\*{3}\s*START OF (?:THE |THIS )?PROJECT GUTENBERG EBOOK .+?\s*\*{3}",
    re.IGNORECASE,
)
END_RE = re.compile(
    r"\*{3}\s*END OF (?:THE |THIS )?PROJECT GUTENBERG EBOOK .+?\s*\*{3}",
    re.IGNORECASE,
)

def fetch_and_save(book_id: int, filename: str) -> bool:
    out_path = BOOKS_DIR / filename
    if out_path.exists():
        print(f"  [skip] {filename}")
        return True
    url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8", errors="replace")
        start_match = START_RE.search(raw)
        if not start_match:
            print(f"  [no markers] {filename}")
            return False
        body_start = start_match.end()
        end_match = END_RE.search(raw, body_start)
        body_end = end_match.start() if end_match else len(raw)
        body = raw[body_start:body_end].strip()
        out_path.write_text(body, encoding="utf-8")
        print(f"  [saved {out_path.stat().st_size//1024:,} KB] {filename}")
        return True
    except Exception as e:
        print(f"  [error] {filename}: {e}")
        return False

def main():
    # ── Step 1: Download Shakespeare plays ────────────────────────────────
    print(f"Downloading {len(SHAKESPEARE_PLAYS)} Shakespeare works...")
    shakespeare_files = []
    for book_id, filename in SHAKESPEARE_PLAYS:
        if fetch_and_save(book_id, filename):
            shakespeare_files.append(filename)
        time.sleep(1)

    print(f"\nShakespeare: {len(shakespeare_files)}/{len(SHAKESPEARE_PLAYS)} available")

    # ── Step 2: Build file list ────────────────────────────────────────────
    all_files = {f.name: f for f in BOOKS_DIR.glob("*.txt")}
    selected = set()

    # Canonical
    for name in CANONICAL:
        if name in all_files:
            selected.add(name)

    # Shakespeare
    for name in shakespeare_files:
        if name in all_files:
            selected.add(name)

    # Random non-periodical
    pool = [
        name for name, path in all_files.items()
        if name not in selected and not is_periodical(path)
    ]
    random.seed(42)
    n_random = min(5000, len(pool))
    for name in random.sample(pool, n_random):
        selected.add(name)

    total = len(selected)
    chunks_estimate = total * 230
    hours = int(chunks_estimate / 60 / 3600)
    minutes = int((chunks_estimate / 60 % 3600) / 60)

    print(f"\nTotal files selected: {total:,}")
    print(f"  Canonical:   {len(CANONICAL)}")
    print(f"  Shakespeare: {len(shakespeare_files)}")
    print(f"  Random:      {n_random}")
    print(f"  Estimated indexing time: ~{hours}h {minutes}m")

    with open(OUTPUT_LIST, "w") as f:
        for name in sorted(selected):
            f.write(str(BOOKS_DIR / name) + "\n")

    print(f"\nFile list written to: {OUTPUT_LIST}")

if __name__ == "__main__":
    main()