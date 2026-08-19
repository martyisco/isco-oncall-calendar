import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
GENERATOR = PROJECT / "scripts" / "generate_schedule.py"


class GenerateScheduleTests(unittest.TestCase):
    def generate(self, source, today="2026-08-19"):
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "rotation.yaml"
            output_path = Path(directory) / "schedule.json"
            source_path.write_text(source, encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(GENERATOR),
                    "--source",
                    str(source_path),
                    "--output",
                    str(output_path),
                    "--today",
                    today,
                    "--months-ahead",
                    "6",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(output_path.read_text(encoding="utf-8"))

    def test_generates_current_rotation_from_explicit_anchor(self):
        schedule = self.generate(
            """
timezone: America/New_York
rotation:
  boundary:
    weekday: Monday
    local_time: "08:00"
  members:
    - name: Operator A
    - name: Operator B
    - name: Operator C
  rotation_anchor:
    start: "2026-08-17T08:00:00-04:00"
    primary: Operator A
overrides: []
"""
        )
        first = schedule["blocks"][0]
        self.assertEqual(first["primary"], "Operator A")
        self.assertEqual(first["start"], "2026-08-17T08:00:00-04:00")
        self.assertEqual(first["end"], "2026-08-24T08:00:00-04:00")
        self.assertEqual(schedule["blocks"][1]["primary"], "Operator B")
        self.assertEqual(schedule["timezone"], "America/New_York")

    def test_override_replaces_primary_for_matching_week(self):
        schedule = self.generate(
            """
timezone: America/New_York
rotation:
  boundary:
    weekday: Monday
    local_time: "08:00"
  members:
    - name: Operator A
    - name: Operator B
    - name: Operator C
  rotation_anchor:
    start: "2026-08-17T08:00:00-04:00"
    primary: Operator A
overrides:
  - id: coverage-2026-08-24
    start: "2026-08-24T08:00:00-04:00"
    end: "2026-08-31T08:00:00-04:00"
    coverer: Operator D
    reason: "Coverage swap"
"""
        )
        matching = next(block for block in schedule["blocks"] if block["start"].startswith("2026-08-24"))
        self.assertEqual(matching["primary"], "Operator D")
        self.assertTrue(matching["override"])
        self.assertEqual(matching["note"], "Coverage swap")

    def test_output_keeps_six_full_months_ahead(self):
        schedule = self.generate(
            """
timezone: America/New_York
rotation:
  boundary:
    weekday: Monday
    local_time: "08:00"
  members:
    - name: Operator A
  rotation_anchor:
    start: "2026-08-17T08:00:00-04:00"
    primary: Operator A
overrides: []
"""
        )
        self.assertEqual(schedule["generated_at"], "2026-08-19")
        self.assertGreaterEqual(schedule["coverage_through"], "2027-02-28T23:59:59-05:00")


if __name__ == "__main__":
    unittest.main()
