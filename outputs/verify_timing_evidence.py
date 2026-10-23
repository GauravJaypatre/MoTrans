"""Script to verify that every timing evidence quote exists verbatim in its saved file."""

from pathlib import Path
import csv
import hashlib

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_CSV = ROOT / "outputs" / "timing_evidence.csv"


def verify_timing_evidence() -> None:
    assert EVIDENCE_CSV.exists(), f"Missing {EVIDENCE_CSV}"
    with open(EVIDENCE_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            saved_path = ROOT / row["saved_path"]
            assert saved_path.exists(), f"Row {i}: File not found: {saved_path}"
            
            raw_bytes = saved_path.read_bytes()
            actual_sha = hashlib.sha256(raw_bytes).hexdigest()
            assert actual_sha == row["sha256"], (
                f"Row {i} ({row['regime']}): SHA256 mismatch!\nExpected: {row['sha256']}\nActual:   {actual_sha}"
            )
            
            quote_bytes = row["quote"].encode("utf-8")
            expected_offset = int(row["byte_offset"])
            actual_offset = raw_bytes.find(quote_bytes)
            assert actual_offset != -1, f"Row {i} ({row['regime']}): Quote not found in {row['saved_path']}!"
            assert actual_offset == expected_offset, (
                f"Row {i} ({row['regime']}): Offset mismatch! Expected {expected_offset}, found at {actual_offset}"
            )
            print(f"Row {i}: {row['regime']} ({row['period']}) verified at offset {actual_offset} (SHA256: {actual_sha[:12]}...)")

    print("\nAll timing evidence quotes verified verbatim!")


if __name__ == "__main__":
    verify_timing_evidence()
