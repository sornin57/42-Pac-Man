import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Highscore:
    """Store a player's name and score."""

    name: str
    score: int


def load_scores(path: str) -> list[Highscore]:
    """Load saved scores, returning an empty list if the file is missing."""
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError("Invalid highscore JSON file") from error

    if not isinstance(data, list):
        raise ValueError("Highscore file must contain a list")

    scores = []
    for index, entry in enumerate(data):
        if not isinstance(entry, dict):
            logger.error("Highscore entry %d is not an object, skipped", index)
            continue

        name = entry.get("name")
        score = entry.get("score")
        if (
            not isinstance(name, str)
            or not name.strip()
            or len(name) > 10
            or any(not (char.isalnum() or char == " ") for char in name)
        ):
            logger.error(
                "Highscore entry %d has an invalid name, skipped", index
            )
            continue
        if type(score) is not int or score < 0:
            logger.error(
                "Highscore entry %d has an invalid score, skipped", index
            )
            continue

        scores.append(Highscore(name, score))

    return scores


def add_score(
    scores: list[Highscore],
    new_score: Highscore,
) -> list[Highscore]:
    """Add a score and return the ten highest scores in descending order."""
    result = scores + [new_score]
    result.sort(key=lambda item: item.score, reverse=True)
    return result[:10]


def save_scores(path: str, scores: list[Highscore]) -> None:
    """Write scores to a JSON file."""
    data = [{"name": item.name, "score": item.score} for item in scores]
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
