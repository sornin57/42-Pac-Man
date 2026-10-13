import pytest

from pacman.highscore import Highscore, add_score, load_scores, save_scores


def test_save_and_load_scores(tmp_path):
    path = tmp_path / "highscores.json"
    scores = [Highscore("Mathieu", 1200), Highscore("Nadia", 850)]

    save_scores(str(path), scores)

    assert load_scores(str(path)) == scores


def test_add_score_sorts_and_keeps_top_ten():
    scores = [Highscore(str(number), number) for number in range(10)]

    result = add_score(scores, Highscore("Best", 20))

    assert len(result) == 10
    assert result[0] == Highscore("Best", 20)
    assert result[-1] == Highscore("1", 1)
    assert scores[0] == Highscore("0", 0)


def test_missing_file_returns_empty_list(tmp_path):
    path = tmp_path / "missing.json"

    assert load_scores(str(path)) == []


def test_invalid_json_raises_clear_error(tmp_path):
    path = tmp_path / "highscores.json"
    path.write_text("not JSON", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid highscore JSON file"):
        load_scores(str(path))
