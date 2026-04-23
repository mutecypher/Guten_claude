#!/usr/bin/env python3
"""
Build final curated index list:
- Canonical books (manually downloaded)
- Shakespeare complete works (explicitly listed by ID)
- 5000 random non-periodical books
"""
import re
import random
from pathlib import Path

BOOKS_DIR   = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_books")
OUTPUT_LIST = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/index_filelist.txt")

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

# ── Explicit canonical list (manually downloaded) ──────────────────────────
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

# ── Explicit Shakespeare list (only actual plays and poems) ────────────────
SHAKESPEARE = [
    # Tragedies
    "01524_HAMLET.txt",
    "01532_KING_LEAR.txt",
    "01533_MACBETH.txt",
    "01531_OTHELLO.txt",
    "01530_ROMEO_AND_JULIET.txt",
    "01529_JULIUS_CAESAR.txt",
    "01528_ANTONY_AND_CLEOPATRA.txt",
    "01527_CORIOLANUS.txt",
    "01526_TITUS_ANDRONICUS.txt",
    "01525_TIMON_OF_ATHENS.txt",
    "22996_TROILUS_AND_CRESSIDA.txt",
    "01484_PERICLES.txt",
    # Comedies
    "01514_A_MIDSUMMER_NIGHTS_DREAM.txt",
    "01515_THE_MERCHANT_OF_VENICE.txt",
    "01516_AS_YOU_LIKE_IT.txt",
    "01517_THE_TAMING_OF_THE_SHREW.txt",
    "01518_TWELFTH_NIGHT.txt",
    "01519_MUCH_ADO_ABOUT_NOTHING.txt",
    "01520_ALL_S_WELL_THAT_ENDS_WELL.txt",
    "01521_MEASURE_FOR_MEASURE.txt",
    "01522_THE_MERRY_WIVES_OF_WINDSOR.txt",
    "01523_THE_COMEDY_OF_ERRORS.txt",
    "23042_LOVES_LABOURS_LOST.txt",
    "23043_THE_TWO_GENTLEMEN_OF_VERONA.txt",
    "23044_THE_WINTERS_TALE.txt",
    "01539_CYMBELINE.txt",
    "01540_THE_TEMPEST.txt",
    # Histories
    "01507_RICHARD_II.txt",
    "01508_HENRY_IV_PART_1.txt",
    "01509_HENRY_IV_PART_2.txt",
    "01510_HENRY_V.txt",
    "01511_HENRY_VI_PART_1.txt",
    "01512_HENRY_VI_PART_2.txt",
    "01513_HENRY_VI_PART_3.txt",
    "02251_RICHARD_III.txt",
    "01541_HENRY_VIII.txt",
    "01542_KING_JOHN.txt",
    # Poems
    "01041_THE_SONNETS.txt",
    "01062_VENUS_AND_ADONIS.txt",
    "01590_THE_RAPE_OF_LUCRECE.txt",
]

def main():
    all_files = {f.name: f for f in BOOKS_DIR.glob("*.txt")}
    selected = set()

    # ── Step 1: Canonical ──────────────────────────────────────────────────
    canonical_found, canonical_missing = [], []
    for name in CANONICAL:
        if name in all_files:
            selected.add(name)
            canonical_found.append(name)
        else:
            canonical_missing.append(name)

    print(f"Canonical: {len(canonical_found)} found, "
          f"{len(canonical_missing)} missing")
    for m in canonical_missing:
        print(f"  MISSING: {m}")

    # ── Step 2: Shakespeare ────────────────────────────────────────────────
    shakespeare_found, shakespeare_missing = [], []
    for name in SHAKESPEARE:
        if name in all_files:
            selected.add(name)
            shakespeare_found.append(name)
        else:
            shakespeare_missing.append(name)

    print(f"Shakespeare: {len(shakespeare_found)} found, "
          f"{len(shakespeare_missing)} missing")
    for m in shakespeare_missing:
        print(f"  MISSING: {m}")

    # ── Step 3: Random non-periodical ─────────────────────────────────────
    pool = [
        name for name, path in all_files.items()
        if name not in selected and not is_periodical(path)
    ]
    random.seed(42)
    n_random = min(5000, len(pool))
    for name in random.sample(pool, n_random):
        selected.add(name)

    print(f"Random non-periodical: {n_random} (pool of {len(pool):,})")

    # ── Summary ────────────────────────────────────────────────────────────
    total = len(selected)
    chunks_estimate = total * 230
    hours = int(chunks_estimate / 60 / 3600)
    minutes = int((chunks_estimate / 60 % 3600) / 60)

    print(f"\nTotal: {total:,} files")
    print(f"  Canonical:   {len(canonical_found)}")
    print(f"  Shakespeare: {len(shakespeare_found)}")
    print(f"  Random:      {n_random}")
    print(f"  Estimated indexing time: ~{hours}h {minutes}m")

    with open(OUTPUT_LIST, "w") as f:
        for name in sorted(selected):
            f.write(str(BOOKS_DIR / name) + "\n")

    print(f"\nFile list written to: {OUTPUT_LIST}")

if __name__ == "__main__":
    main()