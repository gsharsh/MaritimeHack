"""
Utilities: voyage time estimate (distance/speed), path helpers.
"""

from pathlib import Path

# Approximate distance Singapore to Australia West coast (e.g. Fremantle) in nautical miles
SINGAPORE_TO_AU_WEST_NM = 2100  # Adjust with actual route data if provided


def voyage_hours_from_nm_and_speed(distance_nm: float, speed_knots: float) -> float:
    """Voyage duration in hours. speed_knots = design speed Vref or actual."""
    if speed_knots <= 0:
        return 0.0
    return distance_nm / speed_knots


def project_root() -> Path:
    """Project root (parent of src)."""
    return Path(__file__).resolve().parent.parent


def data_path(*parts: str) -> Path:
    """Path under data/ from project root."""
    return project_root() / "data" / Path(*parts)


def outputs_path(*parts: str) -> Path:
    """Path under outputs/ from project root."""
    return project_root() / "outputs" / Path(*parts)
