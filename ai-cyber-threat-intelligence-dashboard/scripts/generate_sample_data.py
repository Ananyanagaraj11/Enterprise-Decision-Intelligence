"""Generate a small sample CSV for testing training (no real dataset needed)."""
import csv
import random
from pathlib import Path

ROWS = 3000
OUT = Path(__file__).resolve().parent.parent / "data" / "sample_data.csv"
LABELS = ["Normal", "Normal", "Normal", "Attack", "Attack"]  # slight imbalance

OUT.parent.mkdir(parents=True, exist_ok=True)
random.seed(42)

with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow([f"f{i}" for i in range(1, 21)] + ["label"])
    for _ in range(ROWS):
        row = [round(random.gauss(0, 1), 4) for _ in range(20)]
        row.append(random.choice(LABELS))
        w.writerow(row)

print(f"Wrote {ROWS} rows to {OUT}")
