import csv
from pathlib import Path


def extract_timestamps(
    input_path: Path = Path("data/electricity.csv"),
    output_path: Path = Path("data/timestamps.csv"),
) -> int:
    """Extract the timestamp column from a CSV and write it to a new CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", newline="", encoding="utf-8") as infile, output_path.open(
        "w", newline="", encoding="utf-8"
    ) as outfile:
        reader = csv.DictReader(infile)

        if "timestamp" not in (reader.fieldnames or []):
            raise ValueError(f"Column 'timestamp' not found in {input_path}")

        writer = csv.writer(outfile)
        writer.writerow(["timestamp"])

        count = 0
        for row in reader:
            writer.writerow([row["timestamp"]])
            count += 1

    return count


def main() -> None:
    rows_written = extract_timestamps()
    print(f"Saved {rows_written} timestamps to data/timestamps.csv")


if __name__ == "__main__":
    main()
