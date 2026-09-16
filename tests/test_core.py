from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from job_system.application import create_application_workspace, update_status
from job_system.common import sanitize_windows_name
from job_system.dedup import find_duplicates
from job_system.facts import blocked_claims_in_material, validate_fact_records
from job_system.reports import write_csv_bom
from job_system.scoring import grade_for, load_scoring_config, score_job


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.config = load_scoring_config()

    def test_full_score_is_100_and_grade_a(self):
        ratings = {key: 1 for key in self.config["dimensions"]}
        result = score_job({"dimension_ratings": ratings}, self.config)
        self.assertEqual(result["match_score"], 100)
        self.assertEqual(result["match_grade"], "A")

    def test_grade_boundaries(self):
        expected = {85: "A", 84.99: "B", 75: "B", 74.99: "C", 65: "C", 64.99: "D", 50: "D", 49.99: "E", 0: "E"}
        for score, grade in expected.items():
            self.assertEqual(grade_for(score, self.config), grade)

    def test_penalty_and_veto_are_visible(self):
        ratings = {key: 1 for key in self.config["dimensions"]}
        result = score_job({"dimension_ratings": ratings, "risk_flags": ["missing_mandatory_certificate"]}, self.config)
        self.assertEqual(result["match_score"], 80)
        self.assertIn("missing_mandatory_certificate", result["veto_flags"])


class DedupTests(unittest.TestCase):
    def test_tracking_params_do_not_prevent_duplicate(self):
        base = {"job_id":"a","title":"ERP Consultant","company":"Acme GmbH","location":"Köln","description":"ERP support implementation","source_url":"https://jobs.example/1"}
        copy = dict(base, job_id="b", source_url="https://jobs.example/1?utm_source=board")
        result = find_duplicates([base, copy])
        self.assertEqual(result[1]["duplicate_of"], "a")
        self.assertEqual(len(result[0]["all_source_urls"]), 2)


class ApplicationTests(unittest.TestCase):
    def test_status_requires_explicit_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "status.md"
            with self.assertRaises(PermissionError):
                update_status(path, "approved")
            update_status(path, "approved", user_approved=True)
            self.assertIn("status: approved", path.read_text(encoding="utf-8"))

    def test_duplicate_workspace_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            job = {"company":"SAMPLE GmbH","title":"SAMPLE Role","match_grade":"B","description":"SAMPLE_DATA_NOT_REAL","source_url":"https://example.invalid"}
            create_application_workspace(root, job)
            with self.assertRaises(FileExistsError):
                create_application_workspace(root, job)

    def test_job_marked_duplicate_cannot_create_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = {"company":"SAMPLE GmbH","title":"SAMPLE Duplicate","duplicate_of":"master-1"}
            with self.assertRaises(ValueError):
                create_application_workspace(Path(tmp), job)

    def test_windows_filename_cleaning(self):
        self.assertEqual(sanitize_windows_name("CON"), "_CON")
        self.assertNotIn(":", sanitize_windows_name("ERP: Support/IT"))


class FactTests(unittest.TestCase):
    def test_unsupported_fact_is_blocked(self):
        records = [{"claim":"Led 50 people", "status":"NOT_SUPPORTED", "source":""}]
        self.assertTrue(blocked_claims_in_material("I Led 50 people.", records))

    def test_verified_fact_requires_source(self):
        self.assertTrue(validate_fact_records([{"claim":"Odoo", "status":"VERIFIED", "source":""}]))


class ExportTests(unittest.TestCase):
    def test_utf8_bom_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jobs.csv"
            write_csv_bom(path, [{"company":"Muster GmbH", "location":"Köln"}], ["company", "location"])
            self.assertTrue(path.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertIn("Köln", path.read_text(encoding="utf-8-sig"))

    def test_paths_are_relative_to_requested_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "x.csv"
            write_csv_bom(path, [], ["x"])
            self.assertTrue(path.exists())

    def test_real_tracker_template_has_utf8_bom(self):
        path = Path(__file__).resolve().parents[1] / "data/applications/application-tracker.csv"
        self.assertTrue(path.read_bytes().startswith(b"\xef\xbb\xbf"))


class ConfigurationTests(unittest.TestCase):
    def test_job_sources_have_required_policy_fields(self):
        root = Path(__file__).resolve().parents[1]
        config = json.loads((root / "config/job-sources.yaml").read_text(encoding="utf-8"))
        required = {"id","name","base_url","country","source_type","public_access","login_required","automation_allowed","recommended_search_method","terms_risk","robots_risk","manual_only","notes","last_checked"}
        self.assertGreaterEqual(len(config["sources"]), 10)
        for source in config["sources"]:
            self.assertFalse(required - source.keys(), source.get("id"))

    def test_sample_job_is_explicitly_not_real(self):
        root = Path(__file__).resolve().parents[1]
        sample = json.loads((root / "data/sample/SAMPLE_JOB.json").read_text(encoding="utf-8"))
        self.assertEqual(sample["sample_marker"], "SAMPLE_DATA_NOT_REAL")


class SkillTests(unittest.TestCase):
    def test_skill_frontmatter_and_names(self):
        root = Path(__file__).resolve().parents[1]
        for base in (root / "skills", root / ".agents" / "skills"):
            for directory in base.iterdir():
                if not directory.is_dir():
                    continue
                path = directory / "SKILL.md"
                self.assertTrue(path.exists(), path)
                text = path.read_text(encoding="utf-8")
                match = re.match(r"^---\nname: ([a-z0-9-]+)\ndescription: (.+?)\n---\n", text)
                self.assertIsNotNone(match, path)
                self.assertEqual(match.group(1), directory.name)
                self.assertNotIn("TODO", text)
                self.assertGreaterEqual(len(match.group(2)), 20)


if __name__ == "__main__":
    unittest.main()
