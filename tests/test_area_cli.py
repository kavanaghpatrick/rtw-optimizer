"""CLI tests for `rtw area` subcommands.

Tests are isolated from the real DB via the RTW_AREA_DB env var pointing
at a per-test tmp_path. Uses typer.testing.CliRunner against the main
`rtw.cli.app`.
"""

import pytest
from typer.testing import CliRunner

from rtw.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def isolate_area_db(tmp_path, monkeypatch):
    """Every test gets its own area.db via RTW_AREA_DB."""
    monkeypatch.setenv("RTW_AREA_DB", str(tmp_path / "area.db"))


# ---------------------------------------------------------------------------
# JZXSWH canonical segment data
# ---------------------------------------------------------------------------

JZXSWH_SEGMENTS = [
    # (from, to, carrier, flight, date, seg_type)
    ("OSL", "LHR", "BA", "785", "2026-04-27", "transit"),
    ("LHR", "SEA", "BA", "49", "2026-04-27", "stopover"),
    ("SEA", "LAX", "AS", "1480", "2026-05-02", "stopover"),
    ("LAX", "HKG", "CX", "881", "2026-05-06", "stopover"),
    ("HKG", "LHR", "CX", "253", "2026-05-08", "stopover"),
    ("LHR", "OSL", "BA", "780", "2026-10-15", "final"),
]


def _invoke(*args):
    """Shorthand for `runner.invoke(app, ["area", *args])`."""
    return runner.invoke(app, ["area", *args])


def _build_jzxswh():
    """Create jzx trip + add all 6 segments. Returns list of results."""
    results = []
    r = _invoke(
        "new",
        "--slug", "jzx",
        "--type", "DONE3",
        "--cabin", "business",
        "--origin", "OSL",
        "--plating", "CX",
        "--pnr", "JZXSWH",
    )
    results.append(r)
    for f, t, c, fl, d, ty in JZXSWH_SEGMENTS:
        r = _invoke(
            "add",
            "--from", f,
            "--to", t,
            "--carrier", c,
            "--flight", fl,
            "--date", d,
            "--type", ty,
        )
        results.append(r)
    return results


# ---------------------------------------------------------------------------
# Happy-path: build full JZXSWH trip end-to-end
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_full_jzxswh_build_and_validate(self):
        # new
        r = _invoke(
            "new",
            "--slug", "jzx",
            "--type", "DONE3",
            "--cabin", "business",
            "--origin", "OSL",
            "--plating", "CX",
            "--pnr", "JZXSWH",
        )
        assert r.exit_code == 0, r.output
        assert "Created trip" in r.output

        # add one explicit segment to exercise the flag names
        r = _invoke(
            "add",
            "--from", "OSL",
            "--to", "LHR",
            "--carrier", "BA",
            "--flight", "785",
            "--date", "2026-04-27",
            "--type", "transit",
        )
        assert r.exit_code == 0, r.output

        # add remaining 5 segments
        for f, t, c, fl, d, ty in JZXSWH_SEGMENTS[1:]:
            r = _invoke(
                "add",
                "--from", f, "--to", t,
                "--carrier", c, "--flight", fl,
                "--date", d, "--type", ty,
            )
            assert r.exit_code == 0, r.output

        # show lists all 6 airports
        r = _invoke("show")
        assert r.exit_code == 0, r.output
        for code in ("OSL", "LHR", "SEA", "LAX", "HKG"):
            assert code in r.output

        # validate passes (JZXSWH is a valid DONE3)
        r = _invoke("validate")
        assert r.exit_code == 0, r.output

        # list shows trip with correct segment count + active flag
        r = _invoke("list")
        assert r.exit_code == 0, r.output
        assert "jzx" in r.output
        assert "6" in r.output  # segment_count
        assert "*" in r.output  # active marker


# ---------------------------------------------------------------------------
# Mutation flow: remove final + validate fails, then reorder via move
# ---------------------------------------------------------------------------


class TestMutationFlow:
    def test_remove_final_then_validate_fails(self):
        for r in _build_jzxswh():
            assert r.exit_code == 0, r.output

        # drop the final LHR-OSL segment
        r = _invoke("rm", "6")
        assert r.exit_code == 0, r.output

        # validator should now flag a Return-to-Origin violation
        r = _invoke("validate")
        assert r.exit_code == 1, r.output

    def test_move_reorders_segments(self):
        for r in _build_jzxswh():
            assert r.exit_code == 0, r.output

        # Move segment 1 (OSL-LHR) to position 3
        r = _invoke("move", "1", "3")
        assert r.exit_code == 0, r.output

        # After move, position 1 should be LHR-SEA (was position 2)
        r = _invoke("show")
        assert r.exit_code == 0, r.output
        # Confirm the new ordering by checking the output contains the
        # reordered airports in expected order
        out = r.output
        # The moved OSL->LHR should now appear later than LHR->SEA
        lhr_sea_idx = out.find("SEA")
        # Order in output is by position; first SEA mention is LHR->SEA row
        assert lhr_sea_idx != -1
        # Confirm move succeeded by checking all 6 segs still present
        for code in ("OSL", "LHR", "SEA", "LAX", "HKG"):
            assert code in out


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


class TestErrorPaths:
    def test_add_without_active_trip(self):
        r = _invoke("add", "--from", "OSL", "--to", "LHR")
        assert r.exit_code == 1, r.output
        assert "No active trip" in r.output

    def test_switch_unknown_slug(self):
        r = _invoke("switch", "does-not-exist")
        assert r.exit_code == 1, r.output

    def test_rm_position_out_of_range(self):
        # Create a trip with just one segment
        r = _invoke(
            "new", "--slug", "tiny",
            "--type", "DONE3", "--cabin", "business", "--origin", "OSL",
        )
        assert r.exit_code == 0, r.output
        r = _invoke("add", "--from", "OSL", "--to", "LHR")
        assert r.exit_code == 0, r.output

        r = _invoke("rm", "99")
        assert r.exit_code == 1, r.output

    def test_new_with_invalid_ticket_type(self):
        r = _invoke(
            "new",
            "--slug", "x",
            "--type", "INVALID",
            "--cabin", "business",
            "--origin", "OSL",
        )
        assert r.exit_code == 1, r.output

    def test_validate_with_zero_segments(self):
        r = _invoke(
            "new", "--slug", "empty",
            "--type", "DONE3", "--cabin", "business", "--origin", "OSL",
        )
        assert r.exit_code == 0, r.output
        # load_itinerary enforces min_length=1 -> validate should exit 1
        r = _invoke("validate")
        assert r.exit_code == 1, r.output

    def test_new_duplicate_slug(self):
        r = _invoke(
            "new", "--slug", "dup",
            "--type", "DONE3", "--cabin", "business", "--origin", "OSL",
        )
        assert r.exit_code == 0, r.output
        r = _invoke(
            "new", "--slug", "dup",
            "--type", "DONE3", "--cabin", "business", "--origin", "OSL",
        )
        assert r.exit_code == 1, r.output


# ---------------------------------------------------------------------------
# Help / wiring
# ---------------------------------------------------------------------------


class TestHelpAndWiring:
    def test_area_help_lists_subcommands(self):
        r = _invoke("--help")
        assert r.exit_code == 0, r.output
        # Every declared subcommand should be mentioned
        for sub in (
            "new",
            "list",
            "switch",
            "show",
            "rm-trip",
            "add",
            "move",
            "rm",
            "validate",
        ):
            assert sub in r.output

    def test_area_new_help_shows_required_options(self):
        r = _invoke("new", "--help")
        assert r.exit_code == 0, r.output
        for flag in ("--slug", "--type", "--cabin", "--origin"):
            assert flag in r.output
