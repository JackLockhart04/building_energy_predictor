#!/usr/bin/env python3
"""Split a combined Open-Meteo CSV into metadata and weather data files.

Input format expected:
1) Metadata table (header + rows)
2) Blank line separator
3) Weather observations table (header + rows)
"""

from __future__ import annotations

import csv
from pathlib import Path


def split_sections(lines: list[str]) -> tuple[list[str], list[str]]:
    """Split file lines into the first and second CSV sections."""
    separator_index = None
    for i, line in enumerate(lines):
        if line.strip() == "":
            separator_index = i
            break

    if separator_index is None:
        raise ValueError("No blank line separator found between metadata and weather data sections.")

    metadata_lines = [line for line in lines[:separator_index] if line.strip() != ""]
    weather_lines = [line for line in lines[separator_index + 1 :] if line.strip() != ""]

    if not metadata_lines:
        raise ValueError("Metadata section is empty.")
    if not weather_lines:
        raise ValueError("Weather data section is empty.")

    return metadata_lines, weather_lines


def write_deduped_weather_metadata(
    metadata_lines: list[str],
    output_path: Path,
) -> dict[str, str]:
    """Write deduplicated weather metadata and return the original id map."""
    reader = csv.DictReader(metadata_lines)
    fieldnames = reader.fieldnames or []

    required = {"location_id", "latitude", "longitude"}
    if not required.issubset(set(fieldnames)):
        raise ValueError(
            f"weather metadata must contain columns: {', '.join(sorted(required))}"
        )

    unique_rows: list[dict[str, str]] = []
    location_id_map: dict[str, str] = {}
    seen_coordinates: dict[tuple[str, str], str] = {}

    for row in reader:
        original_location_id = (row.get("location_id") or "").strip()
        latitude = (row.get("latitude") or "").strip()
        longitude = (row.get("longitude") or "").strip()

        if not original_location_id:
            continue
        if not latitude or not longitude:
            continue

        coordinate_key = (latitude, longitude)
        deduped_location_id = seen_coordinates.get(coordinate_key)
        if deduped_location_id is None:
            deduped_location_id = str(len(unique_rows))
            seen_coordinates[coordinate_key] = deduped_location_id

            deduped_row = dict(row)
            deduped_row["location_id"] = deduped_location_id
            unique_rows.append(deduped_row)

        location_id_map[original_location_id] = deduped_location_id

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in unique_rows:
            writer.writerow(row)

    return location_id_map


def write_deduped_weather_data(
    weather_lines: list[str],
    output_path: Path,
    location_id_map: dict[str, str],
) -> None:
    """Write weather observations with location IDs remapped and unique location/time pairs."""
    reader = csv.DictReader(weather_lines)
    fieldnames = reader.fieldnames or []

    if "location_id" not in fieldnames:
        raise ValueError("weather data must contain a location_id column")
    if "time" not in fieldnames:
        raise ValueError("weather data must contain a time column")

    output_fieldnames = [
        "temperature_f" if name == "temperature_2m (°F)" else
        "apparent_temperature_f" if name == "apparent_temperature (°F)" else
        name
        for name in fieldnames
    ]
    rename_map = {
        "temperature_2m (°F)": "temperature_f",
        "apparent_temperature (°F)": "apparent_temperature_f",
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_fieldnames)
        writer.writeheader()
        seen_observations: set[tuple[str, str]] = set()

        for row in reader:
            original_location_id = (row.get("location_id") or "").strip()
            if original_location_id not in location_id_map:
                continue

            deduped_location_id = location_id_map[original_location_id]
            time_value = (row.get("time") or "").strip()
            observation_key = (deduped_location_id, time_value)
            if observation_key in seen_observations:
                continue

            seen_observations.add(observation_key)
            row["location_id"] = deduped_location_id
            writer.writerow(
                {
                    rename_map.get(name, name): value
                    for name, value in row.items()
                    if name in fieldnames
                }
            )

def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    input_file = project_root / "data" / "open-meteo-unix.csv"
    metadata_output = project_root / "data" / "weather_metadata.csv"
    weather_output = project_root / "data" / "weather_data.csv"

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    with input_file.open("r", encoding="utf-8", newline="") as f:
        lines = f.read().splitlines()

    metadata_lines, weather_lines = split_sections(lines)

    location_id_map = write_deduped_weather_metadata(metadata_lines, metadata_output)
    write_deduped_weather_data(weather_lines, weather_output, location_id_map)

    print(f"Deduplicated metadata written to: {metadata_output}")
    print(f"Weather data written to: {weather_output}")


if __name__ == "__main__":
    main()
