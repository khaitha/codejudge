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


