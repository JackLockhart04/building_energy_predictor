#!/usr/bin/env python3
"""Combine all CSV files in the buildings directory into one CSV.

The script reads every CSV in ../buildings, merges them on shared key columns
(typically building_name), and writes a single combined CSV with original
column names preserved.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


# Easy-to-edit paths.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "buildings"
OUTPUT_FILE = PROJECT_ROOT / "buildings" / "buildings_combined.csv"


def get_csv_files(input_dir: Path, output_file: Path) -> list[Path]:
    csv_files = sorted(
        csv_file for csv_file in input_dir.glob("*.csv") if csv_file.resolve() != output_file
    )
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in: {input_dir}")
    return csv_files


def load_dataframes(csv_files: list[Path]) -> list[pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        if df.empty:
            raise ValueError(f"CSV is empty: {csv_file}")
        frames.append(df)
    return frames


def merge_frames(frames: list[pd.DataFrame], sources: list[Path]) -> pd.DataFrame:
    merged = frames[0]
    merged_source = sources[0]

    for i in range(1, len(frames)):
        current = frames[i]
        current_source = sources[i]
        shared_columns = [col for col in merged.columns if col in current.columns]
        if not shared_columns:
            raise ValueError(
                "No shared columns found to merge CSVs: "
                f"{merged_source} and {current_source}"
            )

        merged = merged.merge(current, on=shared_columns, how="outer")

    return merged


def main() -> None:
    input_dir = INPUT_DIR.resolve()
    output_file = OUTPUT_FILE.resolve()

    csv_files = get_csv_files(input_dir, output_file)
    frames = load_dataframes(csv_files)
    combined = merge_frames(frames, csv_files)

    if "building_name" in combined.columns:
        combined = combined.sort_values("building_name")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_file, index=False)

    print(f"Combined {len(csv_files)} files into: {output_file}")
    print(f"Rows: {len(combined)} | Columns: {len(combined.columns)}")


if __name__ == "__main__":
    main()
