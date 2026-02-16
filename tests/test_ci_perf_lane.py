from pathlib import Path

from scripts import ci_perf_lane


def test_parse_scenarios_rejects_empty() -> None:
    try:
        _ = ci_perf_lane._parse_scenarios(" , ")
    except ValueError as exc:
        assert "at least one scenario" in str(exc)
    else:
        raise AssertionError("ValueError expected")


def test_parse_scenarios_accepts_csv() -> None:
    scenarios = ci_perf_lane._parse_scenarios("P9E-S06, P9E-S05, P9E-S02")
    assert scenarios == ["P9E-S06", "P9E-S05", "P9E-S02"]


def test_run_lane_monitor_normalizes_failure(monkeypatch, tmp_path: Path) -> None:
    called = {}

    def fake_measure(args: list[str]) -> int:
        called["args"] = args
        return 3

    monkeypatch.setattr(ci_perf_lane.measure_phase9e, "main", fake_measure)
    result = ci_perf_lane.run_lane(
        mode="monitor",
        base_dir=tmp_path,
        output_dir=None,
        scenarios=["P9E-S01"],
        warmup=0,
        samples=1,
    )
    assert result == 1
    assert "--scenario" in called["args"]


def test_run_lane_enforce_sets_env(monkeypatch, tmp_path: Path) -> None:
    observed = {}

    def fake_measure(_args: list[str]) -> int:
        observed["enforce"] = ci_perf_lane.os.getenv(ci_perf_lane.measure_phase9e.ENV_PERF_ENFORCE)
        return 0

    monkeypatch.setattr(ci_perf_lane.measure_phase9e, "main", fake_measure)
    result = ci_perf_lane.run_lane(
        mode="enforce",
        base_dir=tmp_path,
        output_dir=None,
        scenarios=["P9E-S02"],
        warmup=0,
        samples=1,
    )
    assert result == 0
    assert observed["enforce"] == "1"


def test_main_invalid_scenarios_returns_2(monkeypatch) -> None:
    monkeypatch.setattr(ci_perf_lane, "_parse_scenarios", lambda _raw: (_ for _ in ()).throw(ValueError("boom")))
    result = ci_perf_lane.main(["--mode", "monitor"])
    assert result == 2
