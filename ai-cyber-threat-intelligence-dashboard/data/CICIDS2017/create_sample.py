"""Create a 5000-row sample from a CICIDS2017 CSV. Run from repo root: python data/CICIDS2017/create_sample.py"""
import pandas as pd
from pathlib import Path

# Same directory as this script
folder = Path(__file__).resolve().parent
source = folder / "Tuesday-WorkingHours.pcap_ISCX.csv"
out = folder / "Tuesday-WorkingHours_sample.csv"

df = pd.read_csv(source)
n = min(5000, len(df))
sampled = df.sample(n=n, random_state=42)
sampled.to_csv(out, index=False)
print(f"Saved {len(sampled)} rows to {out}")
