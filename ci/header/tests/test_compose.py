"""Tests for the header rules composition (ci/header/compose.py).

fixtures/preview-13-15.json is the real header preview of three outside pull requests (13, 14, 15) against public
main 5f2f839c, produced read-only from public Git objects; their BFME II / Boat statuses are the live ones.
Run from the repository root:  python3 -m unittest discover -s ci/header/tests -v
"""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import compose  # noqa: E402

FIXTURE = json.loads((Path(__file__).parent / "fixtures/preview-13-15.json").read_text())
BASE = FIXTURE["base"]
BY_PR = {item["pr"]: item for item in FIXTURE["results"]}
BOAT_OLD = {"state": "success", "description": "BFME II comparison passed (main c1053d57f7ef)"}
BOAT_NOW = {"state": "success", "description": f"BFME II comparison passed (main {BASE[:12]})"}


def components(pr, boat):
    rows = compose.from_preview(BY_PR[pr])
    rows["H1"] = compose.from_wide_status(boat, BASE)
    rows["H10"] = compose.from_admission(None, rows["H1"])     # as collect.components_for does
    return rows


class RealPullRequests(unittest.TestCase):
    def test_old_lexical_removal_leads_cannot_produce_a_terminal_h4_result(self):
        for pr in (13, 14):
            with self.subTest(pr=pr):
                self.assertTrue(BY_PR[pr]["explicit_removed"])
                rows = components(pr, BOAT_OLD)
                self.assertEqual(rows["H4"]["state"], "held")
                state, text, report = compose.compose(BASE, rows)
                self.assertEqual(state, "pending")
                self.assertIn("| H4 | waiting |", "\n".join(report))

    def test_pending_source_lead_names_the_declaration_and_a_conditional_fix(self):
        row = BY_PR[13]["explicit_removed"][0]
        data = {"preview": BY_PR[13]["preview"], "declaration_review": {"candidates": [
            {"path": row["path"], "line": row["line"], "declaration": "W3DView::m_unk0x2458"}
        ]}}
        components = compose.from_preview(data)
        other = {rule: {"state": "pass"} for rule in compose.RULES}
        other["H4"] = components["H4"]
        state, text, report = compose.compose(BASE, other)
        self.assertEqual(state, "pending")
        self.assertEqual(text, f"Held: H4 waiting to compare W3DView::m_unk0x2458. (main {BASE[:12]})")
        self.assertIn(f"{row['path']}:{row['line']}", "\n".join(report))
        self.assertIn("If you removed or changed W3DView::m_unk0x2458, restore it or add "
                      "Removed-Declaration: W3DView::m_unk0x2458", "\n".join(report))
        self.assertEqual(compose.table_text("Owner::operator|"), "Owner::operator&#124;")

    def test_confirmed_component_refusal_still_names_the_declaration_with_remedy(self):
        confirmed = BY_PR[13]["explicit_removed"]
        preview = [item for item in BY_PR[13]["preview"] if item["rule"] != "H4"]
        preview.append({"rule": "H4", "state": "fail", "findings": confirmed})
        state, text, report = compose.compose(BASE, compose.from_preview({"preview": preview}))
        self.assertEqual(state, "failure")
        self.assertEqual(text, f"H4: This change removes or renames W3DView::m_unk0x2458. (main {BASE[:12]})")
        self.assertIn("Removed-Declaration: W3DView::m_unk0x2458", "\n".join(report))

    def test_pr15_is_held_for_the_rules_not_built(self):
        state, text, report = compose.compose(BASE, components(15, BOAT_OLD))
        self.assertEqual((state, text), ("pending", f"Held: rule not built: H2, H5 (main {BASE[:12]})"))
        self.assertIn("| H1 | waiting |", "\n".join(report))

    def test_wide_verdict_only_counts_on_this_main(self):
        self.assertEqual(compose.from_wide_status(BOAT_OLD, BASE)["state"], "held")
        self.assertEqual(compose.from_wide_status(BOAT_NOW, BASE)["state"], "pass")
        failed = {"state": "failure", "description": f"BFME II check refused this patch (main {BASE[:12]})"}
        self.assertEqual(compose.from_wide_status(failed, BASE)["state"], "fail")
        self.assertEqual(compose.from_wide_status(None, BASE)["state"], "held")


class Order(unittest.TestCase):
    def all_pass(self):
        return {rule: {"state": "pass"} for rule in compose.RULES}

    def test_all_pass_is_success_bound_to_main(self):
        self.assertEqual(compose.compose(BASE, self.all_pass())[:2],
                         ("success", f"Header rules passed (main {BASE[:12]})"))

    def test_first_failure_in_rule_order_wins_over_everything(self):
        rows = self.all_pass()
        rows["H6"] = {"state": "fail", "message": "Inline body changed behaviour."}
        rows["H3"] = {"state": "fail", "message": "Object is defined twice."}
        rows["H2"] = {"state": "missing"}
        state, text, _ = compose.compose(BASE, rows, ledger_request="R-1")
        self.assertEqual((state, text), ("failure", f"H3: Object is defined twice. (main {BASE[:12]})"))

    def test_ledger_request_waits_before_missing_and_held(self):
        rows = self.all_pass()
        rows["H5"] = {"state": "missing"}
        rows["H6"] = {"state": "held", "message": "Waiting."}
        self.assertEqual(compose.compose(BASE, rows, ledger_request="R-17")[:2],
                         ("pending", f"Held: ledger request R-17 (main {BASE[:12]})"))

    def test_absent_rule_is_not_built_never_passed(self):
        rows = self.all_pass()
        del rows["H2"]
        self.assertEqual(compose.compose(BASE, rows)[:2],
                         ("pending", f"Held: rule not built: H2 (main {BASE[:12]})"))

    def test_held_names_the_first_waiting_rule(self):
        rows = self.all_pass()
        rows["H7"] = {"state": "held", "message": "Former includers of the deleted Draft are not covered yet."}
        state, text, _ = compose.compose(BASE, rows)
        self.assertEqual(state, "pending")
        self.assertTrue(text.startswith("Held: H7 Former includers"))

    def test_descriptions_fit_and_keep_the_marker(self):
        rows = self.all_pass()
        rows["H4"] = {"state": "fail", "message": "x" * 400}
        _, text, _ = compose.compose(BASE, rows)
        self.assertLessEqual(len(text), 140)
        self.assertTrue(text.endswith(f"(main {BASE[:12]})"))

    def test_unknown_state_is_refused(self):
        rows = self.all_pass()
        rows["H3"] = {"state": "maybe"}
        with self.assertRaises(ValueError):
            compose.compose(BASE, rows)

    def test_same_inputs_same_bytes(self):
        a = compose.compose(BASE, components(15, BOAT_OLD))
        b = compose.compose(BASE, json.loads(json.dumps(components(15, BOAT_OLD))))
        self.assertEqual(a, b)


class LanderForms(unittest.TestCase):
    """The lander (BFME_AUTO_HEADERS) recognises exactly these description forms."""

    def test_forms_match_the_lander(self):
        rows = {rule: {"state": "pass"} for rule in compose.RULES}
        self.assertTrue(compose.compose(BASE, rows)[1].endswith(f"(main {BASE[:12]})"))
        self.assertTrue(compose.compose(BASE, rows, "R-1")[1].startswith("Held: ledger request"))
        del rows["H5"]
        self.assertTrue(compose.compose(BASE, rows)[1].startswith("Held: rule not built"))



class WideBudget(unittest.TestCase):
    """H10 from the bot's admission status; it holds and never fails."""

    def rows(self, admission, wide_state="held"):
        rows = {rule: {"state": "pass"} for rule in compose.RULES}
        rows["H1"] = {"state": wide_state, "message": "The wide comparison has not reported for this commit."}
        rows["H10"] = compose.from_admission(admission, rows["H1"])
        return rows

    def test_over_budget_names_h10_not_h1(self):
        state, text, _ = compose.compose(BASE, self.rows({"state": "pending", "description": compose.DAILY_LIMIT}))
        self.assertEqual((state, text), ("pending", f"Held: H10 daily limit for wide checks reached; retried "
                                                    f"automatically (main {BASE[:12]})"))

    def test_admitted_wide_passes_h10_and_h1_still_waits(self):
        state, text, _ = compose.compose(BASE, self.rows({"state": "success", "description": compose.WIDE_ADMITTED}))
        self.assertTrue(text.startswith("Held: H1 "), text)

    def test_a_wide_result_on_this_main_passes_h10_whoever_started_it(self):
        for wide in ("pass", "fail"):
            self.assertEqual(self.rows(None, wide)["H10"]["state"], "pass")

    def test_no_admission_and_no_wide_result_holds_and_never_fails(self):
        for status in (None, {"state": "pending", "description": "Waiting for a maintainer: this changes include/."},
                       {"state": "failure", "description": "anything"}):
            self.assertEqual(self.rows(status)["H10"]["state"], "held")

    def test_all_ten_passing_is_success(self):
        rows = {rule: {"state": "pass"} for rule in compose.RULES}
        self.assertEqual(compose.compose(BASE, rows)[0], "success")


if __name__ == "__main__":
    unittest.main()
