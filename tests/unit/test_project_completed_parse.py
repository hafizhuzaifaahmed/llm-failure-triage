"""The D-61 re-projection command names the phase 'Tier 2 (E4, 1 rep as planned)', whose comma is part of the name:
--completed must split only on commas outside parentheses, or the pre-registered command cannot run."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("project_d59", ROOT / "scripts" / "local" / "project_d59.py")
proj = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proj)


def test_d61_command_phases_parse():
    assert proj.parse_completed("steps 0-5,Tier 1 (D1),Tier 2 (E4, 1 rep as planned)") == {
        "steps 0-5", "Tier 1 (D1)", "Tier 2 (E4, 1 rep as planned)"}


def test_plain_and_empty():
    assert proj.parse_completed("steps 0-5, D2 ") == {"steps 0-5", "D2"}
    assert proj.parse_completed("") == set()
