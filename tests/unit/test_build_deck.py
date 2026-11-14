"""The defense deck regenerates from the numbers map: every deck number is a mapped key, and the build is complete."""
import csv
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "docs" / "paper" / "src" / "DEFENSE_DECK.src.md"
spec = importlib.util.spec_from_file_location("build_deck", ROOT / "scripts" / "paper" / "build_deck.py")
bd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bd)


def test_every_deck_key_is_in_the_numbers_map():
    keys = set(re.findall(r"\{\{([^{}]+)\}\}", SRC.read_text(encoding="utf-8")))
    mapped = {r["key"]: r for r in csv.DictReader(open(ROOT / "docs" / "paper" / "NUMBERS_MAP.csv", encoding="utf-8"))}
    assert keys and keys <= set(mapped)
    assert all("DEFENSE_DECK.src.md" in mapped[k]["used_in"] for k in keys)


def test_rendered_deck_source_has_no_placeholders_and_all_slides():
    sp = bd.parse_deck((ROOT / "docs" / "paper" / "DEFENSE_DECK.md").read_text(encoding="utf-8"))
    assert "{{" not in (ROOT / "docs" / "paper" / "DEFENSE_DECK.md").read_text(encoding="utf-8")
    for sid in ("title", "hook", "problem", "gap", "framework", "arms", "f1", "evidence", "debate", "ceiling", "cost",
                "kuu", "kuu_d2", "base", "threats", "contributions", "takeaways"):
        assert sid in sp and sp[sid]["notes"], sid


def test_chart_values_parse_and_match_categories():
    sp = bd.parse_deck((ROOT / "docs" / "paper" / "DEFENSE_DECK.md").read_text(encoding="utf-8"))
    for sid, s in sp.items():
        if "chart" in s:
            n = len(s["cats"][0].split(","))
            assert all(len(v) == n for _, v in bd._series(s)), sid


def test_build_writes_timing_and_notes(tmp_path, monkeypatch):
    out = tmp_path / "deck.pptx"
    monkeypatch.setattr(bd, "OUT", out)
    bd.build(render=False)
    from pptx import Presentation
    p = Presentation(out)
    qa = bd.parse_qa((ROOT / "docs" / "paper" / "DEFENSE_QA.md").read_text(encoding="utf-8"))
    n_main = len(bd.parse_deck((ROOT / "docs" / "paper" / "DEFENSE_DECK.md").read_text(encoding="utf-8")))
    assert len(p.slides) == n_main + 1 + len(qa)
    assert all(s.notes_slide.notes_text_frame.text.strip() for s in p.slides)
    timed = sum(1 for s in p.slides if s._element.find(bd.qn("p:timing")) is not None)
    assert timed >= 15
