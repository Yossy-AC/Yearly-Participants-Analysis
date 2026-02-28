import difflib
import json
from pathlib import Path

import pandas as pd

DEFAULT_ALIAS_PATH = Path(__file__).parent.parent / "data" / "course_aliases.json"


def load_aliases(path: Path = DEFAULT_ALIAS_PATH) -> dict[str, str]:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_aliases(aliases: dict[str, str], path: Path = DEFAULT_ALIAS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(aliases, f, ensure_ascii=False, indent=2)


def apply_aliases(df: pd.DataFrame, aliases: dict[str, str]) -> pd.DataFrame:
    if not aliases:
        return df
    df = df.copy()
    df["course_name"] = df["course_name"].map(lambda x: aliases.get(str(x), x))
    return df


def detect_similar_groups(
    names: list[str], threshold: float = 0.80
) -> list[list[str]]:
    """類似度がthreshold以上の名前をグループにまとめて返す。"""
    visited = set()
    groups = []

    for name in names:
        if name in visited:
            continue
        similar = [
            other
            for other in names
            if other != name
            and other not in visited
            and difflib.SequenceMatcher(None, name, other).ratio() >= threshold
        ]
        if similar:
            group = [name] + similar
            groups.append(group)
            visited.update(group)

    return groups
