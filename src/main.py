"""
Command line runner for the Music Recommender Simulation.

Runs the Phase 4 experiments: three listener profiles scored with the
default mode, then one profile compared across every scoring mode.

Run from the project root with either:
    python -m src.main
    python src/main.py
"""

import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

try:
    from .recommender import DEFAULT_MODE, WEIGHT_STRATEGIES, load_songs, recommend_songs
except ImportError:
    from recommender import DEFAULT_MODE, WEIGHT_STRATEGIES, load_songs, recommend_songs

SONGS_CSV = Path(__file__).resolve().parent.parent / "data" / "songs.csv"
TOP_K = 5
REASON_SEPARATOR = "; "
TABLE_HEADERS = ("Rank", "Song Title", "Artist", "Genre", "Score", "Reasons")
# Columns right-aligned in the table (Rank and Score).
NUMERIC_COLUMNS = {0, 4}

PROFILES: Tuple[Tuple[str, Dict], ...] = (
    (
        "High-Energy Hip-Hop / Workout Listener",
        {
            "genre": "hip-hop",
            "mood": "energetic",
            "detailed_mood_tag": "aggressive",
            "energy": 0.85,
            "danceability": 0.8,
        },
    ),
    (
        "Chill Lofi / Late-Night Study Listener",
        {
            "genre": ["lofi", "acoustic"],
            "mood": "chill",
            "detailed_mood_tag": "focused",
            "energy": 0.25,
            "acousticness": 0.85,
        },
    ),
    (
        "Upbeat Indie / Nostalgic Roadtrip Listener",
        {
            "genre": ["indie rock", "indie pop", "pop"],
            "mood": "happy",
            "detailed_mood_tag": "nostalgic",
            "energy": 0.70,
            "release_decade": "2010s",
        },
    ),
)
MODE_DEMO_PROFILE_INDEX = 0


def _table_rows(recommendations: List[Tuple[Dict, float, str]]) -> List[List[List[str]]]:
    """Turn recommendations into table rows where each cell is a list of text lines."""
    return [
        [
            [str(rank)],
            [song["title"]],
            [song["artist"]],
            [song["genre"]],
            [f"{score:.2f}"],
            explanation.split(REASON_SEPARATOR) if explanation else ["(no matches)"],
        ]
        for rank, (song, score, explanation) in enumerate(recommendations, start=1)
    ]


def _column_widths(rows: List[List[List[str]]]) -> List[int]:
    """Return the widest line in each column, including the header."""
    return [
        max([len(header)] + [len(line) for row in rows for line in row[index]])
        for index, header in enumerate(TABLE_HEADERS)
    ]


def _render_line(cells: Sequence[str], widths: Sequence[int]) -> str:
    """Render one physical table line with padded, aligned cells."""
    padded = [
        cell.rjust(width) if index in NUMERIC_COLUMNS else cell.ljust(width)
        for index, (cell, width) in enumerate(zip(cells, widths))
    ]
    return "| " + " | ".join(padded) + " |"


def _render_row(row: List[List[str]], widths: Sequence[int]) -> List[str]:
    """Render one table row, spreading multi-line cells (like reasons) across lines."""
    height = max(len(cell) for cell in row)
    return [
        _render_line([cell[line] if line < len(cell) else "" for cell in row], widths)
        for line in range(height)
    ]


def format_table(recommendations: List[Tuple[Dict, float, str]]) -> str:
    """Format recommendations as an ASCII table with one reason per line."""
    rows = _table_rows(recommendations)
    widths = _column_widths(rows)
    border = "+" + "+".join("-" * (width + 2) for width in widths) + "+"
    lines = [border, _render_line(TABLE_HEADERS, widths), border.replace("-", "=")]
    for row in rows:
        lines.extend(_render_row(row, widths))
        lines.append(border)
    return "\n".join(lines)


def _describe_prefs(prefs: Dict) -> str:
    """Return a one-line summary of a profile's preferences."""
    parts = []
    for key, value in prefs.items():
        shown = "/".join(value) if isinstance(value, (list, tuple)) else value
        parts.append(f"{key}={shown}")
    return ", ".join(parts)


def print_section(title: str, prefs: Dict, songs: List[Dict], mode: str) -> None:
    """Print a heading, the profile, and its top recommendations for one mode."""
    print(f"\n=== {title} | mode: {mode} ===")
    print(f"Profile: {_describe_prefs(prefs)}")
    print(format_table(recommend_songs(prefs, songs, k=TOP_K, mode=mode)))


def run_profile_experiments(songs: List[Dict]) -> None:
    """Run every listener profile with the default scoring mode."""
    print(f"\n##### Experiment 1: {len(PROFILES)} listener profiles ({DEFAULT_MODE} mode) #####")
    for name, prefs in PROFILES:
        print_section(name, prefs, songs, DEFAULT_MODE)


def run_mode_comparison(songs: List[Dict]) -> None:
    """Run one profile under every scoring mode to show how weights change the ranking."""
    name, prefs = PROFILES[MODE_DEMO_PROFILE_INDEX]
    print(f"\n##### Experiment 2: scoring modes compared for '{name}' #####")
    for mode in WEIGHT_STRATEGIES:
        print_section(name, prefs, songs, mode)


def main() -> None:
    """Load the catalog and run all Phase 4 experiments."""
    try:
        songs = load_songs(str(SONGS_CSV))
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: could not load songs. {error}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded songs: {len(songs)}")
    run_profile_experiments(songs)
    run_mode_comparison(songs)


if __name__ == "__main__":
    main()
