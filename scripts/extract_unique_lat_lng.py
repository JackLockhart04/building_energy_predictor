import csv
from pathlib import Path
from typing import Iterable


def _sorted_pairs(pairs: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    """Sort coordinate pairs numerically when possible."""

    def sort_key(pair: tuple[str, str]) -> tuple[float, float]:
        return float(pair[0]), float(pair[1])

    try:
        return sorted(pairs, key=sort_key)
    except ValueError:
        return sorted(pairs)


def extract_unique_lat_lng(
    electricity_path: Path = Path("data/electricity.csv"),
    metadata_path: Path = Path("data/metadata.csv"),
    output_path: Path = Path("data/unique_lat_lng.csv"),
) -> tuple[int, int]:
    """Write unique lat/lng pairs for buildings present in electricity.csv."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with electricity_path.open("r", newline="", encoding="utf-8") as f:
        header = next(csv.reader(f), None)

    if not header:
        raise ValueError(f"No header found in {electricity_path}")

    electricity_buildings = {name for name in header if name and name != "timestamp"}

    unique_pairs: set[tuple[str, str]] = set()
    with metadata_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        required = {"building_id", "lat", "lng"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                f"metadata.csv must contain columns: {', '.join(sorted(required))}"
            )

        for row in reader:
            building_id = (row.get("building_id") or "").strip()
            if building_id not in electricity_buildings:
                continue

            lat = (row.get("lat") or "").strip()
            lng = (row.get("lng") or "").strip()
            if not lat or not lng:
                continue

            unique_pairs.add((lat, lng))

    sorted_pairs = _sorted_pairs(unique_pairs)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["lat", "lng"])
        writer.writerows(sorted_pairs)

    return len(electricity_buildings), len(sorted_pairs)


def main() -> None:
    building_count, pair_count = extract_unique_lat_lng()
    print(
        "Saved "
        f"{pair_count} unique lat/lng pairs for {building_count} buildings "
        "to data/unique_lat_lng.csv"
    )


if __name__ == "__main__":
    main()
