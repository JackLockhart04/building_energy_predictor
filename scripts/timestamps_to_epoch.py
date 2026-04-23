import csv
from datetime import datetime, timezone
from pathlib import Path


def convert_timestamps_to_epoch(
    input_path: Path = Path("data/timestamps.csv"),
    output_path: Path = Path("data/timestamps_epoch.csv"),
) -> int:
    """Convert timestamps in 'YYYY-MM-DD HH:MM:SS' format to epoch seconds (UTC)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", newline="", encoding="utf-8") as infile, output_path.open(
        "w", newline="", encoding="utf-8"
    ) as outfile:
        reader = csv.DictReader(infile)

        if "timestamp" not in (reader.fieldnames or []):
            raise ValueError(f"Column 'timestamp' not found in {input_path}")

        writer = csv.writer(outfile)
        writer.writerow(["timestamp", "epoch_s"])

        count = 0
        for row in reader:
            ts = row["timestamp"].strip()
            dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            writer.writerow([ts, int(dt.timestamp())])
            count += 1

    return count


def main() -> None:
    rows_written = convert_timestamps_to_epoch()
    print(f"Saved {rows_written} rows to data/timestamps_epoch.csv")


if __name__ == "__main__":
    main()
