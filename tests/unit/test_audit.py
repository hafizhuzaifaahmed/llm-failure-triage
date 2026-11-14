"""Audit sheets: stratification, blinding, scoring. Synthetic inputs only."""
import csv

from triage import audit, config


def _inst(i):
    return {"instance_id": i, "focal_class": "org.x.Foo", "focal_method_name": "bar",
            "test": {"method_source": "@Test void t(){}"},
            "failure": {"outcome_type": "exception", "exception_class": "E", "message": "m",
                        "failing_test_line_text": "x", "rendered_trace": "at ..."}}


def test_label_audit_is_stratified_blinded_and_scorable(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "GT_STORE", tmp_path / "gt")
    labels = [{"instance_id": f"i{k}", "label": "PF" if k < 70 else "TF", "split": "dev", "project": "Cli",
               "bug_name": "Cli_1"} for k in range(200)]
    insts = {l["instance_id"]: _inst(l["instance_id"]) for l in labels}
    info = audit.make_label_audit(labels, insts, {"Cli_1": "diff"}, tmp_path / "out")
    assert info["n"] == 100 and info["by_label"] == {"PF": 50, "TF": 50}
    rows = list(csv.DictReader(open(tmp_path / "out" / "label_audit_rater_A.csv", encoding="utf-8-sig")))
    assert "auto_label" not in rows[0] and "PF" not in {r.get("decision") for r in rows}
    # identical copies for both raters
    assert open(tmp_path / "out" / "label_audit_rater_A.csv").read() == open(tmp_path / "out" / "label_audit_rater_B.csv").read()
    # fill: rater A agrees with key, rater B agrees except on 10 rows
    key = {r["audit_id"]: r["auto_label"] for r in csv.DictReader(open(tmp_path / "gt" / "audit" / "label_audit_key.csv", encoding="utf-8-sig"))}
    for rater, flip in (("A", 0), ("B", 10)):
        out = []
        for j, r in enumerate(rows):
            lab = key[r["audit_id"]]
            dec = "ATTRIBUTABLE_TO_FAULT" if lab == "PF" else "NOT_ATTRIBUTABLE"
            if j < flip:
                dec = "NOT_ATTRIBUTABLE" if dec == "ATTRIBUTABLE_TO_FAULT" else "ATTRIBUTABLE_TO_FAULT"
            out.append({**r, "decision": dec})
        audit._write_csv(tmp_path / f"{rater}.csv", out)
    s = audit.score_label_audit(tmp_path / "A.csv", tmp_path / "B.csv", tmp_path / "gt" / "audit" / "label_audit_key.csv")
    assert s["rater_A"]["agreement_with_auto_label"] == 1.0 and s["rater_B"]["agreement_with_auto_label"] == 0.9
    assert 0.75 < s["cohen_kappa_raters"] < 0.85 and len(s["rater_disagreements"]) == 10


def test_incomplete_sheet_is_not_scored(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "GT_STORE", tmp_path / "gt")
    labels = [{"instance_id": f"i{k}", "label": "PF" if k % 2 else "TF", "split": "dev", "project": "Cli",
               "bug_name": "Cli_1"} for k in range(20)]
    audit.make_label_audit(labels, {l["instance_id"]: _inst(l["instance_id"]) for l in labels}, {}, tmp_path / "o",
                           n_pf=5, n_tf=5)
    s = audit.score_label_audit(tmp_path / "o" / "label_audit_rater_A.csv", tmp_path / "o" / "label_audit_rater_B.csv",
                                tmp_path / "gt" / "audit" / "label_audit_key.csv")
    assert s["status"] == "incomplete"


def test_spec_audit_quota_sums_to_n(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "GT_STORE", tmp_path / "gt")
    ctx, specs = {}, []
    for k in range(120):
        fid = f"f{k}"
        ctx[fid] = {"split": "test", "project": f"P{k % 7}", "bug_name": "Cli_1", "sig": {"focal_signature": "s"}}
        specs.append({"focal_id": fid, "valid": True, "spec": {"purpose": "p"}})
    info = audit.make_spec_audit(specs, ctx, {}, tmp_path / "o")
    assert info["n"] == 60 and sum(info["quotas"].values()) == 60
