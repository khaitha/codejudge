import json
import os

from codejudge.cli import main

EXAMPLE = os.path.join(os.path.dirname(__file__), "..", "examples", "two_sum")


def test_cli_run_prints_leaderboard(capsys):
    code = main(["run", EXAMPLE, "--max-prefs", "3"])
    assert code == 0
    out = capsys.readouterr().out
    assert "Task: two-sum" in out
    assert "optimal_hashmap" in out
    assert "Pairwise preferences" in out


def test_cli_run_writes_json(tmp_path):
    out_path = tmp_path / "report.json"
    code = main(["run", EXAMPLE, "--json", str(out_path)])
    assert code == 0
    data = json.loads(out_path.read_text())
    assert data["task_id"] == "two-sum"
    assert len(data["reports"]) == 4
    assert data["reports"][0]["rank"] == 1


def test_cli_run_writes_markdown(tmp_path):
    out_path = tmp_path / "report.md"
    code = main(["run", EXAMPLE, "--markdown", str(out_path)])
    assert code == 0
    text = out_path.read_text()
    assert "# Evaluation report" in text
    assert "| Rank |" in text


def test_cli_show(capsys):
    code = main(["show", EXAMPLE])
    assert code == 0
    out = capsys.readouterr().out
    assert "two_sum()" in out
    assert "Candidates:" in out


def test_cli_bad_weights_returns_error(capsys):
    code = main(["run", EXAMPLE, "--weights", "1,2"])
    assert code == 2
    assert "weights" in capsys.readouterr().err


def test_cli_malformed_task_returns_error(capsys, tmp_path):
    (tmp_path / "task.yaml").write_text("prompt: missing keys\n")
    code = main(["run", str(tmp_path)])
    assert code == 2
    assert "error:" in capsys.readouterr().err
