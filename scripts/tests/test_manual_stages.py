"""Tests for manual/stages.yaml and scripts/validate_stages.py.

A synthetic, fully passing release fixture is built in a temp directory; every one of the
13 gates must pass on it. Mutation tests then break one artefact at a time and assert that
the matching gate fails, which shows each gate is machine-checkable. The main fixture models a
third-party open-licence text source; a second fixture models first-party content.
Tests for the fail-closed memo flags, first-party content, report schemas, the recorded-decision check, the
legal-basis rule (no separate legal sign-off steps) and the bl-score hash pin follow the mutation tests. No network, no real data.
Run: PY -m pytest -q scripts/tests/test_manual_stages.py
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest
import yaml

HERE = Path(__file__).resolve().parent
ITEM = HERE.parent.parent
ML = ITEM.parent.parent
sys.path.insert(0, str(HERE.parent))
import validate_stages as vs  # noqa: E402

STAGES = ITEM / "manual" / "stages.yaml"
SCHEMA = ITEM / "manual" / "schemas" / "stages.schema.json"
SHA = "a" * 64
PIN = json.loads((ITEM / "manual" / "bl-score.pin.json").read_text(encoding="utf-8"))["tree_sha256"]
UA = "BayanatLabs-OpenData/1.0 (+https://bayanatlabs.com/open; hello@bayanatlabs.com)"


def write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix in (".yaml", ".yml"):
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    elif path.suffix == ".jsonl":
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in data), encoding="utf-8")
    elif path.suffix == ".json":
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    else:
        path.write_text(data if isinstance(data, str) else str(data), encoding="utf-8")


SCORE = {
    "candidate_id": "ZZ-999",
    "title": "Bayanat Labs Synthetic Fixture Corpus",
    "scores": {"impact": 3, "claim_strength": 2, "ease": 5, "legal_cleanliness": 5, "commercial_pull": 3},
    "legal_tier": "green",
    "effort": "S",
    "justifications": {"impact": "fixture", "claim_strength": "fixture", "ease": "fixture",
                       "legal_cleanliness": "fixture", "commercial_pull": "fixture"},
    "memo_ref": "scoping_memo.md",
    "scored_on": "2026-10-14",
}
SCORE_OUT = {"candidate_id": "ZZ-999", "weighted_score_0_100": 65.0, "legal_verdict": "tier1_eligible",
             "max_release_tier": 1, "suggested_priority": "P1", "warnings": [], "policy_version": "0.1"}

MEMO = {
    "schema_version": 1,
    "manual_version": "1.0.0",
    "candidate_id": "ZZ-999",
    "title": "Bayanat Labs Synthetic Fixture Corpus",
    "priority": "P2",
    "product_link": {"family": "Search", "page": None},
    "claim_to_make": {"wording": "No comparative claim", "comparative": False},
    "incumbents": [],
    "sources": [{"source_id": "SRC01", "url": "https://example.org/fixture", "licence_route": "IN-A02",
                 "release_tier": "tier1_open_content", "licence": "CC-BY-4.0",
                 "tos_basis": "gov-open-data", "terms_read_on": "2026-10-14", "decision_ref": None}],
    "release_tier": "tier1_open_content",
    "licence_plan": [{"config": "default", "licence": "cc-by-4.0", "content": "synthetic records"}],
    "profile": "P-TXT",
    "modalities": ["text"],
    "uses_video_host": False,
    "video_media_download": False,
    "media_download_decision_ref": None,
    "consented_audio": False,
    "has_images": False,
    "uses_llm_suggestions": False,
    "third_party_sources": True,
    "qa": {"sample_size": 1000, "sample_unit": "records", "agreement_metric": "kappa", "agreement_threshold": 0.65,
           "is_eval_set": False, "pii_audit_records": 3000,
           "native_reviewers": [{"name": None, "dialects": ["Najdi"]}]},
    "ranges": {"duplicate_rate_max": 0.05, "langid_min_share": 0.95, "expected_languages": ["ar"]},
    "budget": {"estimator": "manual/budget.py 0.1.0", "gpu_hours": 0, "human_qa_hours": 10},
    "owner": {"agent": "fixture-agent", "coordinator": "fixture-coordinator"},
    "dates": {"memo_date": "2026-10-14", "target_release": "2026-10-28"},
    "risks": [{"risk": "none", "likelihood": "L", "mitigation": "n/a", "stop_rule": "drop"}],
    "stop_conditions": ["legal tier turns red"],
    "decision": {"coordinator": {"name": "Fixture Coordinator", "date": "2026-10-14", "verdict": "approve"},
                 "legal_tier_assigned": True, "conflicts_noted": []},
    "score_tool_sha256": PIN,
}

SOURCE_ROW = {"source_id": "SRC01", "data_url": "https://example.org/fixture", "license_url": "https://creativecommons.org/licenses/by/4.0/",
              "retrieved_at": "2026-10-14T10:00:00Z", "acquisition_mechanism": "official_dump",
              "status": {"access": "allowed", "redistribution": "allowed"}, "licence_route": "IN-A02",
              "release_tier": "tier1_open_content",
              "recheck_by": "2027-01-14"}

PROV_ROW = {
    "item_id": "fx-0001", "release_version": "v0.1", "source_id": "SRC01", "source_platform": "gov_open_data",
    "source_item_id": "fx-0001", "source_url": "https://example.org/fixture", "acquisition_method": "official_dump",
    "retrieved_at": "2026-10-14T10:00:00Z", "raw_sha256": SHA, "license_detected": "CC-BY-4.0",
    "license_url": "https://creativecommons.org/licenses/by/4.0/",
    "license_evidence": {"quote": "fixture", "url": "https://example.org/fixture", "sha256": SHA, "checked_at": "2026-10-14T10:00:00Z"},
    "tos_basis": "gov-open-data", "licence_route": "IN-A02", "release_tier": "tier1_open_content",
    "release_form": "full_content", "transform_chain": [], "annotation_origin": "deterministic", "synthetic": False,
    "pii_flags": [], "opt_out_status": "none",
}

DIGEST_ROW = {
    "asset_id": "ZZ-999", "slug": "synthetic-fixture", "version": "v0.1", "month": "2026-11",
    "release_date": "2026-10-28", "days_since_release": 30, "collected_at": "2026-11-27T09:00:00Z",
    "collected_by": "coordinator",
    "hf": {"downloads_30d": None, "likes": None, "linked_models": None, "linked_spaces": None},
    "downloads_other": {"pypi_30d": None, "kaggle_views": None, "kaggle_downloads": None, "zenodo_views": None,
                        "zenodo_downloads": None, "github_stars": None},
    "search": {"nonbrand_impressions_en": None, "nonbrand_impressions_ar": None, "clicks_en": None, "clicks_ar": None},
    "reach": {"new_referring_domains": None, "press_mentions": None,
              "listings": {"masader": "draft_ready", "kaggle": "draft_ready", "google_dataset_search": "not_submitted"}},
    "scholarly": {"scholar_citations": None, "used_by_entries": None},
    "quality_ops": {"issues_opened": 0, "issues_closed": 0, "takedowns_received": 0, "takedown_sla_met": None},
    "commercial": {"product_clicks": None, "tagged_requests": {}},
    "ai_panel": {"run_date": None, "prompts": None, "method_mentions": None, "citations_of_url": None},
    "verdict_30d": "too_early",
}


LICENCE_OK = {"incompatible_items": 0, "sa_nc_obligations_propagated": True, "items_without_decision_ref": 0,
              "undecided_points_not_logged": 0, "blocked_tools_on_release_path": 0}


def build_fixture(base: Path) -> dict[str, Path]:
    job, hf, gh, prog = base / "job", base / "hf", base / "gh", base / "programme"
    write(job / "scoping_memo.md", "# Scoping memo: ZZ-999 · Bayanat Labs Synthetic Fixture Corpus\n")
    write(job / "scoping_memo.yaml", MEMO)
    write(job / "scoping_memo.score.yaml", SCORE)
    write(job / "scoping_memo.score.json", SCORE_OUT)
    write(job / "job.json", {"external_actions_authorized": False, "release": {"next_version_date": "2027-01-27"}})
    write(job / "sources.jsonl", [SOURCE_ROW])
    write(job / "PROVENANCE.jsonl", [PROV_ROW])
    write(job / "qa/reports/discovery.json", {"red_items_included": 0, "sources_without_tos_basis": 0,
                                               "sources_terms_not_reviewed": 0, "items_missing_rights_signals": 0,
                                               "probe_records": 100, "video_host": {}})
    write(job / "intake/manifest.parquet", "placeholder")
    write(job / "qa/reports/acquisition.json", {"items_total": 10, "items_with_sha256": 10, "items_with_retrieved_at": 10,
                                                 "user_agent": UA, "min_seconds_between_requests_per_host": 3.2,
                                                 "min_seconds_between_requests_government_or_small_hosts": 5.1,
                                                 "max_concurrency_per_host": 1, "access_denials_bypassed": 0,
                                                 "proxy_or_ip_rotation_used": False, "tier2_items_without_collection_basis": 0})
    write(job / "validation/schema_report.json", {"records_total": 10, "records_valid": 10, "normalisation_version": "bayanat-norm-v1",
                                                   "records_missing_raw_field": 0})
    write(job / "qa/reports/dedup.json", {"duplicate_rate": 0.02, "langid": {"expected_language_share": 0.99},
                                           "test_set_overlap_items": 0, "cross_dedup_targets_missing": 0})
    write(job / "qa/reports/pii_audit.json", {"n": 3000, "stratified": True, "hits": 0, "passed_before_any_upload": True,
                                               "cr_first_1000": {"n": 1000, "residual_rate": 0.0}})
    write(job / "qa/reports/reid.json", {"failed_tests": 0, "tests_not_completed_count": 0, "sensitive_category_fields": 0})
    write(job / "qa/reports/safety.json", {"identifiable_minor_items_remaining": 0, "flagged_items_without_human_decision": 0, "images": {}})
    write(job / "qa/reports/labels.json", {"label_distribution": {"Najdi": 10}, "min_spotcheck_fraction_per_dialect": 0.02,
                                            "spotchecks_by_non_dialect_speakers": 0, "labels_missing_annotation_origin": 0,
                                            "estimates_presented_as_fact": 0})
    write(job / "qa/reports/qa_report.json", {"kappa": 0.72, "sample_size": 1000, "calibration_batch": 50,
                                               "per_stratum_intervals_reported": True})
    write(job / "qa/reports/QA_REPORT.md", "# QA report\n")
    write(job / "qa/signoff.yaml", {"native_reviewer": {"name": "Fixture Reviewer", "date": "2026-10-20", "verdict": "approve",
                                                         "role": "native-reviewer"}, "dialects_without_native_checker": 0})
    write(job / "qa/reports/package.json", {"viewer_renders": True, "load_dataset_clean_env_ok": True, "card_lint_errors": 0,
                                             "croissant_valid": True, "checksum_mismatches": 0, "card_manual_version": "1.0.0",
                                             "synthetic_records_unlabelled": 0})
    write(job / "qa/reports/maintenance.json", {"index_only_review": {"reviewed_on": "2026-10-28", "policy": "policy/index-only-rules.yaml",
                                                                    "triggers_reviewed": ["IO-1", "IO-2", "IO-3", "IO-4", "IO-5"],
                                                                    "triggers_not_reviewed": 0}})
    write(job / "qa/reports/licence_check.json", LICENCE_OK)
    write(job / "qa/reports/gates.json", {"failed": 0})
    write(job / "qa/reports/release_checklist.json", {"unchecked_items": 0, "claims_reverified_on": "2026-10-28",
                                                       "page_card_archive_mismatches": 0,
                                                       "coordinator": {"name": "Fixture Coordinator", "date": "2026-10-27", "verdict": "approve"}})
    write(job / "signoffs/founder_go.yaml", {"founder": {"name": "Founder", "date": "2026-10-27", "verdict": "go"}})
    for f in ["README.md", "README.ar.md", "CLAIMS.md", "LICENSE", "LICENSES/LICENSE-sources.md", "CITATION.cff",
              "CHANGELOG.md", "MANIFEST.json", "SHA256SUMS", "croissant.json"]:
        write(hf / f, "{}" if f.endswith(".json") else "fixture\n")
    write(hf / "PROVENANCE.jsonl", [PROV_ROW])
    write(gh / "eval/results.json", {"headline_metric": {"name": "nDCG@10", "value": 0.41}, "script_sha256": SHA,
                                     "model_label": "reference baseline, not a product"})
    write(gh / "launch/chart.png", "png")
    write(gh / "qa/reports/numbers.json", {"rows": 10})
    for f in ["README.md", "LICENSE", "CITATION.cff", "CHANGELOG.md"]:
        write(gh / f, "fixture\n")
    write(gh / "job.json", {"external_actions_authorized": False})
    write(gh / "tests/fixtures/sample.jsonl", [{"id": 1}])  # small test fixture: allowed by S8.no_data_in_gh's exclude
    write(prog / "coordinator/metrics_digest.jsonl", [DIGEST_ROW])
    write(prog / "coordinator/release_calendar.jsonl", [{"item_id": "ZZ-999", "kind": "next_version", "date_end": "2027-01-27"}])
    lg = base / "legal_record" / "decisions.csv"  # the configured path of the legal record: its decisions table
    write(lg, "decision_id,answer,effective_date,source\n"
              "DEC-0001,,,\n")
    return {"job": job, "hf": hf, "gh": gh, "programme": prog, "legal_record": lg}


def run_eval(roots: dict[str, Path], stages: str | None = None) -> dict:
    doc = yaml.safe_load(STAGES.read_text(encoding="utf-8"))
    args = type("A", (), {})()
    args.job, args.hf, args.gh, args.programme = (str(roots[k]) for k in ("job", "hf", "gh", "programme"))
    args.legal_record = str(roots["legal_record"]) if roots.get("legal_record") else None
    args.search_root = [str(ITEM), str(ML)]
    args.stages_spec = stages
    return vs.evaluate(doc, args)


def stage_result(report: dict, sid: int) -> dict:
    return next(s for s in report["stages"] if s["id"] == sid)


# ----------------------------------------------------------------------------- tests
def test_stages_file_validates():
    rc = vs.main([str(STAGES), "--schema", str(SCHEMA), "--search-root", str(ITEM), "--search-root", str(ML)])
    assert rc == 0


def test_thirteen_stages_and_gate_coverage():
    doc = yaml.safe_load(STAGES.read_text(encoding="utf-8"))
    assert [s["id"] for s in doc["stages"]] == list(range(13))
    mapped = {g for s in doc["stages"] for g in s["cr_gates"]}
    assert mapped == {f"G{i}" for i in range(8)}
    for s in doc["stages"]:
        assert s["cr_gates"] or s.get("coordinator_check")
        assert s["blocking"] is True


def test_fixture_passes_every_gate(tmp_path):
    report = run_eval(build_fixture(tmp_path))
    failing = [(s["id"], c) for s in report["stages"] for c in s["checks"] if c["status"] not in ("pass", "n/a")]
    assert failing == []
    assert report["all_passed"] is True
    assert len(report["stages"]) == 13


@pytest.mark.parametrize("sid,mutate", [
    (0, lambda r: write(r["job"] / "scoping_memo.score.yaml", {**SCORE, "legal_tier": "red"})),
    (0, lambda r: write(r["job"] / "scoping_memo.score.json", {**SCORE_OUT, "legal_verdict": "excluded"})),
    (0, lambda r: write(r["job"] / "scoping_memo.score.yaml", {**SCORE, "notes_typo": "unknown field"})),
    (0, lambda r: write(r["job"] / "scoping_memo.yaml", {**MEMO, "decision": {"coordinator": {"name": "X", "date": "2026-10-14", "verdict": "revise"}}})),
    (1, lambda r: write(r["job"] / "qa/reports/discovery.json", {"red_items_included": 1, "sources_without_tos_basis": 0, "sources_terms_not_reviewed": 0, "items_missing_rights_signals": 0, "probe_records": 100})),
    (1, lambda r: (r["job"] / "sources.jsonl").unlink()),
    (2, lambda r: write(r["job"] / "qa/reports/acquisition.json", {"items_total": 10, "items_with_sha256": 9, "items_with_retrieved_at": 10, "user_agent": UA, "min_seconds_between_requests_per_host": 3, "min_seconds_between_requests_government_or_small_hosts": 5, "max_concurrency_per_host": 1, "access_denials_bypassed": 0, "proxy_or_ip_rotation_used": False, "tier2_items_without_collection_basis": 0})),
    (2, lambda r: write(r["job"] / "qa/reports/acquisition.json", {"items_total": 10, "items_with_sha256": 10, "items_with_retrieved_at": 10, "user_agent": UA, "min_seconds_between_requests_per_host": 1.0, "min_seconds_between_requests_government_or_small_hosts": 5, "max_concurrency_per_host": 1, "access_denials_bypassed": 0, "proxy_or_ip_rotation_used": False, "tier2_items_without_collection_basis": 0})),
    (3, lambda r: write(r["job"] / "validation/schema_report.json", {"records_total": 10, "records_valid": 9, "normalisation_version": "x", "records_missing_raw_field": 0})),
    (4, lambda r: write(r["job"] / "qa/reports/dedup.json", {"duplicate_rate": 0.02, "langid": {"expected_language_share": 0.99}, "test_set_overlap_items": 3, "cross_dedup_targets_missing": 0})),
    (4, lambda r: write(r["job"] / "qa/reports/dedup.json", {"duplicate_rate": 0.20, "langid": {"expected_language_share": 0.99}, "test_set_overlap_items": 0, "cross_dedup_targets_missing": 0})),
    (4, lambda r: write(r["job"] / "qa/reports/dedup.json", {"duplicate_rate": 0.02, "langid": {"expected_language_share": 0.80}, "test_set_overlap_items": 0, "cross_dedup_targets_missing": 0})),
    (5, lambda r: write(r["job"] / "qa/reports/reid.json", {"failed_tests": 0, "tests_not_completed_count": 1, "sensitive_category_fields": 0})),
    (5, lambda r: write(r["job"] / "qa/reports/pii_audit.json", {"n": 3000, "stratified": True, "hits": 1, "passed_before_any_upload": True, "cr_first_1000": {"residual_rate": 0.0}})),
    (5, lambda r: write(r["job"] / "qa/reports/pii_audit.json", {"n": 1000, "stratified": True, "hits": 0, "passed_before_any_upload": True, "cr_first_1000": {"residual_rate": 0.0}})),
    (6, lambda r: write(r["job"] / "qa/reports/labels.json", {"label_distribution": {}, "min_spotcheck_fraction_per_dialect": 0.005, "spotchecks_by_non_dialect_speakers": 0, "labels_missing_annotation_origin": 0, "estimates_presented_as_fact": 0})),
    (7, lambda r: write(r["job"] / "qa/reports/qa_report.json", {"kappa": 0.62, "sample_size": 1000, "calibration_batch": 50, "per_stratum_intervals_reported": True})),
    (7, lambda r: (r["job"] / "qa/signoff.yaml").unlink()),
    (8, lambda r: (r["hf"] / "README.ar.md").unlink()),
    (8, lambda r: write(r["hf"] / "PROVENANCE.jsonl", [{k: v for k, v in PROV_ROW.items() if k != "tos_basis"}])),
    (8, lambda r: write(r["gh"] / "data/default/train-00000-of-00001.parquet", "data")),
    (8, lambda r: write(r["gh"] / "v0.1/corpus.jsonl", [{"id": 1}])),
    (8, lambda r: (r["gh"] / "job.json").unlink()),
    (8, lambda r: write(r["job"] / "qa/reports/package.json", {"viewer_renders": True, "load_dataset_clean_env_ok": True, "card_lint_errors": 0, "croissant_valid": True, "checksum_mismatches": 0, "card_manual_version": "1.0.0", "synthetic_records_unlabelled": 3})),
    (9, lambda r: write(r["gh"] / "eval/results.json", {"headline_metric": {"value": None}, "script_sha256": SHA, "model_label": "reference baseline, not a product"})),
    (10, lambda r: (r["job"] / "signoffs/founder_go.yaml").unlink()),
    (11, lambda r: write(r["programme"] / "coordinator/metrics_digest.jsonl", [{**DIGEST_ROW, "asset_id": "ZZ-998"}])),
    (11, lambda r: write(r["programme"] / "coordinator/metrics_digest.jsonl", [{**DIGEST_ROW, "verdict_30d": "great"}])),
    (12, lambda r: write(r["job"] / "job.json", {"external_actions_authorized": False, "release": {"next_version_date": None}})),
    (12, lambda r: write(r["job"] / "qa/reports/maintenance.json", {"index_only_review": {"reviewed_on": "2026-10-28", "triggers_not_reviewed": 2}})),
    (12, lambda r: (r["job"] / "qa/reports/maintenance.json").unlink()),
    (0, lambda r: write(r["job"] / "scoping_memo.yaml", {**MEMO, "score_tool_sha256": "b" * 64})),
    (8, lambda r: write(r["job"] / "qa/reports/licence_check.json", {**LICENCE_OK, "items_without_decision_ref": 1})),
    (8, lambda r: write(r["job"] / "qa/reports/licence_check.json", {**LICENCE_OK, "undecided_points_not_logged": 1})),
])
def test_mutation_fails_matching_gate(tmp_path, sid, mutate):
    roots = build_fixture(tmp_path)
    mutate(roots)
    report = run_eval(roots)
    assert stage_result(report, sid)["gate_passed"] is False
    assert report["all_passed"] is False


def test_eval_set_raises_kappa_floor(tmp_path):
    roots = build_fixture(tmp_path)
    memo = copy.deepcopy(MEMO)
    memo["qa"]["is_eval_set"] = True
    memo["qa"]["agreement_threshold"] = 0.7
    write(roots["job"] / "scoping_memo.yaml", memo)
    write(roots["job"] / "qa/reports/qa_report.json", {"kappa": 0.68, "sample_size": 1000, "calibration_batch": 50, "per_stratum_intervals_reported": True})
    assert stage_result(run_eval(roots), 7)["gate_passed"] is False


def test_memo_schema_rejects_loose_threshold_without_approval():
    import jsonschema
    schema = json.loads((ITEM / "manual" / "schemas" / "scoping_memo_record.schema.json").read_text(encoding="utf-8"))
    memo = copy.deepcopy(MEMO)
    memo["deviations"] = [{"threshold_id": "T7.speech_sample", "default": "max(2%, 2 h)", "memo_value": "1 h", "direction": "looser"}]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(memo, schema)
    memo["deviations"][0]["founder_approval_ref"] = "founder email 2026-10-20"
    jsonschema.validate(memo, schema)
    bad = copy.deepcopy(MEMO)
    bad["qa"]["agreement_threshold"] = 0.5
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_validator_rejects_broken_files(tmp_path):
    doc = yaml.safe_load(STAGES.read_text(encoding="utf-8"))
    broken = copy.deepcopy(doc)
    broken["stages"] = broken["stages"][:12]
    p = tmp_path / "s.yaml"
    p.write_text(yaml.safe_dump(broken), encoding="utf-8")
    assert vs.main([str(p), "--schema", str(SCHEMA)]) == 1
    broken = copy.deepcopy(doc)
    for s in broken["stages"]:
        s["cr_gates"] = [g for g in s["cr_gates"] if g != "G3"]
    broken["cr_gates"]["G3"]["stages"] = []
    p.write_text(yaml.safe_dump(broken), encoding="utf-8")
    assert vs.main([str(p), "--schema", str(SCHEMA)]) == 1


def test_flat_export_has_the_flat_fields(tmp_path):
    out = tmp_path / "flat.json"
    assert vs.main([str(STAGES), "--schema", str(SCHEMA), "--emit-flat", str(out)]) == 0
    flat = json.loads(out.read_text(encoding="utf-8"))
    assert len(flat["stages"]) == 13
    for s in flat["stages"]:
        assert set(["id", "name", "actions", "tools", "gate_check", "threshold", "evidence_artifact", "cr_gate", "owner_role"]) <= set(s)
        assert s["gate_check"]


# ----------------------------------------------------------------------------- definition of done
DOD = ITEM / "manual" / "dod.yaml"


def add_rc_extras(roots: dict[str, Path]) -> None:
    rc = json.loads((roots["job"] / "qa/reports/release_checklist.json").read_text(encoding="utf-8"))
    rc.update({"doi_reserved": "10.5281/zenodo.0000000", "hub_page_draft_path": "outbox/hub_page.html",
               "hub_page_jsonld_valid": True, "hub_page_paid_family_link": True, "takedown_route_live": True})
    write(roots["job"] / "qa/reports/release_checklist.json", rc)
    pkg = json.loads((roots["job"] / "qa/reports/package.json").read_text(encoding="utf-8"))
    pkg["example_reproduced_clean_env"] = True
    write(roots["job"] / "qa/reports/package.json", pkg)
    for f in ["technical_post.md", "press.md", "thread.md", "partners.yaml"]:
        write(roots["job"] / "outbox/launch" / f, "draft_for_founder\n")
    write(roots["gh"] / "launch/masader_entry.json", {})
    write(roots["gh"] / "kaggle/dataset-metadata.json", {})
    (roots["programme"] / "coordinator").mkdir(parents=True, exist_ok=True)
    (roots["programme"] / "coordinator/metrics_digest_row.schema.json").write_text(
        (ITEM / "coordinator/metrics_digest_row.schema.json").read_text(encoding="utf-8"), encoding="utf-8")


def run_dod(roots: dict[str, Path], phase: str) -> dict:
    dod = yaml.safe_load(DOD.read_text(encoding="utf-8"))
    args = type("A", (), {})()
    args.job, args.hf, args.gh, args.programme = (str(roots[k]) for k in ("job", "hf", "gh", "programme"))
    args.search_root = [str(ITEM), str(ML)]
    return vs.evaluate_dod(dod, args, phase)


def test_dod_structure():
    doc = yaml.safe_load(STAGES.read_text(encoding="utf-8"))
    dod = yaml.safe_load(DOD.read_text(encoding="utf-8"))
    assert vs.validate_dod(dod, doc) == []
    assert len(dod["items"]) == 12


def test_dod_rc_passes_and_done_waits_for_founder(tmp_path):
    roots = build_fixture(tmp_path)
    add_rc_extras(roots)
    rc = run_dod(roots, "rc")
    assert rc["all_done"] is True, [c for i in rc["items"] for c in i["checks"] if c["status"] != "pass"]
    done = run_dod(roots, "done")
    assert done["all_done"] is False
    not_done = {i["id"] for i in done["items"] if not i["done"]}
    assert {"D06", "D07", "D09", "D10"} <= not_done
    write(roots["job"] / "release/published.yaml", {
        "doi_published": True, "hub_page_url": "https://bayanatlabs.com/open/synthetic-fixture",
        "listings": {"masader": "submitted", "kaggle": "not_applicable", "google_dataset_search": "submitted"},
        "launch_bundle_sent": {"name": "Founder", "date": "2026-10-28", "verdict": "sent"}})
    done = run_dod(roots, "done")
    assert done["all_done"] is True, [c for i in done["items"] for c in i["checks"] if c["status"] != "pass"]


def test_dod_rc_fails_without_outbox_drafts(tmp_path):
    roots = build_fixture(tmp_path)
    add_rc_extras(roots)
    (roots["job"] / "outbox/launch/press.md").unlink()
    rc = run_dod(roots, "rc")
    assert next(i for i in rc["items"] if i["id"] == "D10")["done"] is False


# ----------------------------------------------------------------------------- bl-score coupling
BL = ITEM / "tools" / "bl-score"  # bl-score ships in this repository (tools/bl-score)


@pytest.mark.skipif(not (BL / "src/bl_score/data/memo.schema.json").exists(), reason="bl-score not present")
def test_score_schema_mirrors_bl_score():
    ours = json.loads((ITEM / "manual" / "scoping_memo.schema.json").read_text(encoding="utf-8"))
    theirs = json.loads((BL / "src/bl_score/data/memo.schema.json").read_text(encoding="utf-8"))
    for key in ("type", "required", "additionalProperties", "properties", "$defs"):
        assert ours.get(key) == theirs.get(key), key


@pytest.mark.skipif(not (BL / "src/bl_score").exists(), reason="bl-score not present")
def test_fixture_score_file_runs_through_bl_score(tmp_path):
    import subprocess
    f = tmp_path / "scoping_memo.score.yaml"
    write(f, SCORE)
    env = {"PYTHONPATH": str(BL / "src"), "PATH": "/usr/bin:/bin"}
    res = subprocess.run([sys.executable, "-m", "bl_score", str(f)], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert res.returncode == 0, res.stderr
    out = json.loads(res.stdout)
    assert out["legal_verdict"] == "tier1_eligible"
    assert out["candidate_id"] == SCORE["candidate_id"]
    assert out["weighted_score_0_100"] == pytest.approx(SCORE_OUT["weighted_score_0_100"])
    assert out["suggested_priority"] == SCORE_OUT["suggested_priority"]


# ----------------------------------------------------------------------------- memo flags, first-party content, report schemas
def check_status(report: dict, cid: str) -> str:
    return next(c["status"] for s in report["stages"] for c in s["checks"] if c["id"] == cid)


def test_missing_applies_if_field_is_error_not_na(tmp_path):
    # A memo without has_images must not silently skip the image checks.
    roots = build_fixture(tmp_path)
    write(roots["job"] / "scoping_memo.yaml", {k: v for k, v in MEMO.items() if k != "has_images"})
    report = run_eval(roots, "5")
    assert check_status(report, "S5.faces_plates") == "error"
    assert report["all_passed"] is False


def test_sample_rate_applies_to_speech_only(tmp_path):
    # Text-only releases are n/a; non-consented speech above 16 kHz fails.
    roots = build_fixture(tmp_path)
    assert check_status(run_eval(roots, "3"), "S3.sample_rate") == "n/a"
    write(roots["job"] / "scoping_memo.yaml", {**MEMO, "modalities": ["text", "speech"]})
    write(roots["job"] / "validation/schema_report.json", {"records_total": 10, "records_valid": 10, "normalisation_version": "x",
                                                           "records_missing_raw_field": 0, "audio": {"max_release_sample_rate_hz": 48000}})
    assert check_status(run_eval(roots, "3"), "S3.sample_rate") == "fail"
    write(roots["job"] / "scoping_memo.yaml", {**MEMO, "modalities": ["speech"], "consented_audio": True})
    assert check_status(run_eval(roots, "3"), "S3.sample_rate") == "n/a"


def first_party(roots: dict[str, Path]) -> None:
    memo = copy.deepcopy(MEMO)
    memo["third_party_sources"] = False
    memo["sources"][0].update({"tos_basis": "synthetic", "licence_route": None})
    write(roots["job"] / "scoping_memo.yaml", memo)
    write(roots["job"] / "qa/reports/discovery.json", {"red_items_included": 0, "sources_without_tos_basis": 0,
                                                       "sources_terms_not_reviewed": 0, "video_host": {}})
    write(roots["job"] / "qa/reports/acquisition.json", {"items_total": 10, "items_with_sha256": 10, "items_with_retrieved_at": 10,
                                                         "max_concurrency_per_host": 1, "access_denials_bypassed": 0,
                                                         "proxy_or_ip_rotation_used": False, "tier2_items_without_collection_basis": 0,
                                                         "upstream_commit": "200740ad7e33238743c253819896c74675f9dbc4"})


def test_first_party_content_skips_web_etiquette_checks(tmp_path):
    # First-party content has no host, so rights signals, probe, UA and rates are n/a; the upstream commit is pinned.
    roots = build_fixture(tmp_path)
    first_party(roots)
    report = run_eval(roots, "1-2")
    for cid in ("S1.rights_signals", "S1.probe", "S2.user_agent", "S2.rate", "S2.rate_gov"):
        assert check_status(report, cid) == "n/a", cid
    assert check_status(report, "S2.pinned_upstream") == "pass"
    assert report["all_passed"] is True
    acq = json.loads((roots["job"] / "qa/reports/acquisition.json").read_text(encoding="utf-8"))
    acq["upstream_commit"] = None
    write(roots["job"] / "qa/reports/acquisition.json", acq)
    assert check_status(run_eval(roots, "2"), "S2.pinned_upstream") == "fail"


def test_memo_schema_first_party_flag_and_legal_refs():
    import jsonschema
    schema = json.loads((ITEM / "manual" / "schemas" / "scoping_memo_record.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(MEMO, schema)
    bad = copy.deepcopy(MEMO)
    bad["third_party_sources"] = False  # a gov open-data source is third-party
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
    for missing in ("third_party_sources", "ranges", "score_tool_sha256"):
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate({k: v for k, v in MEMO.items() if k != missing}, schema)
    bad = copy.deepcopy(MEMO)
    bad["sources"][0]["decision_ref"] = "email of 20 Oct"  # free text is not a citable legal position
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
    ok = copy.deepcopy(MEMO)
    ok["sources"][0]["decision_ref"] = "DEC-0001"
    jsonschema.validate(ok, schema)


def test_media_download_needs_recorded_decision(tmp_path):
    # A filled entry in the legal record, named by the memo, not a separate legal sign-off, is the basis.
    roots = build_fixture(tmp_path)
    assert check_status(run_eval(roots, "2"), "S2.media_download_decision") == "n/a"  # no download planned
    memo = {**MEMO, "uses_video_host": True, "video_media_download": True, "media_download_decision_ref": "DEC-0001"}
    write(roots["job"] / "scoping_memo.yaml", memo)
    assert check_status(run_eval(roots, "2"), "S2.media_download_decision") == "fail"  # row exists but is empty
    write(roots["legal_record"], "decision_id,answer,effective_date,source\n"
                               "DEC-0001,Option adopted (fixture),2026-10-25,\n")
    assert check_status(run_eval(roots, "2"), "S2.media_download_decision") == "fail"  # no source recorded
    write(roots["legal_record"], "decision_id,answer,effective_date,source\n"
                               "DEC-0001,Option adopted (fixture),2026-10-25,fixture approval\n")
    assert check_status(run_eval(roots, "2"), "S2.media_download_decision") == "pass"
    write(roots["job"] / "scoping_memo.yaml", {**memo, "media_download_decision_ref": "DEC-0002"})
    assert check_status(run_eval(roots, "2"), "S2.media_download_decision") == "fail"  # the memo names another decision


def test_validator_rejects_counsel_signoff_steps(tmp_path):
    # No stage, gate or stop rule may wait for a separate legal sign-off.
    doc = yaml.safe_load(STAGES.read_text(encoding="utf-8"))
    p = tmp_path / "s.yaml"
    for mutate in (
        lambda d: d["stages"][2]["actions"].append("Download only after counsel sign-off."),
        lambda d: d["stages"][5]["stop_conditions"].append("Wait for counsel review before upload."),
        lambda d: d["stages"][8]["gate"]["checks"].append({"id": "S8.counsel_ok", "type": "metric", "root": "job",
                                                           "path": "qa/reports/licence_check.json",
                                                           "field": "items_without_counsel_signoff", "op": "==", "value": 0}),
        lambda d: d["stages"][8]["signoff_roles"].append("counsel"),
        lambda d: d.pop("legal_basis_rule"),
    ):
        broken = copy.deepcopy(doc)
        mutate(broken)
        p.write_text(yaml.safe_dump(broken, allow_unicode=True), encoding="utf-8")
        assert vs.main([str(p), "--schema", str(SCHEMA)]) == 1


def test_manual_is_v1_and_approved():
    doc = yaml.safe_load(STAGES.read_text(encoding="utf-8"))
    dod = yaml.safe_load(DOD.read_text(encoding="utf-8"))
    assert doc["manual_version"] == dod["manual_version"] == "1.0.1"
    assert doc["status"] == "approved"
    assert doc["approval"] == {**doc["approval"], "by": "founder", "date": "2026-10-15", "source": "founder approval, 15 Oct 2026"}
    assert "decision_id" in doc["legal_basis_rule"] and "legal sign-off" in doc["legal_basis_rule"]


def test_validator_rejects_undeclared_root_and_misplaced_keys(tmp_path):
    doc = yaml.safe_load(STAGES.read_text(encoding="utf-8"))
    broken = copy.deepcopy(doc)
    del broken["roots"]["legal_record"]
    p = tmp_path / "s.yaml"
    p.write_text(yaml.safe_dump(broken), encoding="utf-8")
    assert vs.main([str(p), "--schema", str(SCHEMA)]) == 1
    broken = copy.deepcopy(doc)
    broken["stages"][0]["gate"]["checks"][0]["exclude"] = ["tests/**"]
    p.write_text(yaml.safe_dump(broken), encoding="utf-8")
    assert vs.main([str(p), "--schema", str(SCHEMA)]) == 1


def test_report_schemas_are_current_and_fixture_reports_validate(tmp_path):
    import jsonschema
    import gen_report_schemas as grs
    assert grs.main(["--check"]) == 0
    roots = build_fixture(tmp_path)
    index = json.loads((ITEM / "manual/schemas/reports/INDEX.json").read_text(encoding="utf-8"))["reports"]
    rootdir = {"job": roots["job"], "hf_repo": roots["hf"], "gh_repo": roots["gh"], "programme": roots["programme"]}
    checked = 0
    for name, entry in index.items():
        f = rootdir[entry["root"]] / entry["path"]
        if not f.exists():
            continue  # dod-only files the stage fixture does not build
        schema = json.loads((ITEM / "manual/schemas/reports" / entry["schema"]).read_text(encoding="utf-8"))
        jsonschema.validate(vs.load_any(f), schema)
        checked += 1
    assert checked >= 14
    dedup = json.loads((ITEM / "manual/schemas/reports/dedup.schema.json").read_text(encoding="utf-8"))
    with pytest.raises(jsonschema.ValidationError):  # a report cannot declare a numeric check n/a
        jsonschema.validate({"duplicate_rate": "n/a", "langid": {"expected_language_share": 1.0},
                             "test_set_overlap_items": 0, "cross_dedup_targets_missing": 0}, dedup)


def test_bl_score_pin_matches_stage0_check():
    doc = yaml.safe_load(STAGES.read_text(encoding="utf-8"))
    c = next(c for c in doc["stages"][0]["gate"]["checks"] if c["id"] == "S0.score_tool_pinned")
    assert c["value"] == [PIN]


@pytest.mark.skipif(not (BL / "src/bl_score").exists(), reason="bl-score not present")
def test_br010_bl_score_matches_pin():
    import pin_bl_score
    assert pin_bl_score.main([str(BL), "--check", str(ITEM / "manual" / "bl-score.pin.json")]) == 0
