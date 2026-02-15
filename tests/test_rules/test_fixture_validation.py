"""Parametrized tests for challenge and rule fixtures.

Each fixture was designed to test specific validation scenarios.
This file ensures they produce the expected rule results when run
through the full Validator.
"""

import yaml
import pytest
from pathlib import Path

from rtw.models import Itinerary, Severity
from rtw.validator import Validator

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _load(name: str) -> Itinerary:
    with open(FIXTURES_DIR / name) as f:
        data = yaml.safe_load(f)
    return Itinerary(**data)


def _results_by_rule(report, rule_id: str):
    """Return all results for a given rule_id."""
    return [r for r in report.results if r.rule_id == rule_id]


def _violations_by_rule(report, rule_id: str):
    """Return violation-severity failures for a given rule_id."""
    return [
        r for r in report.results
        if r.rule_id == rule_id and not r.passed and r.severity == Severity.VIOLATION
    ]


def _warnings_by_rule(report, rule_id: str):
    """Return warning-severity failures for a given rule_id."""
    return [
        r for r in report.results
        if r.rule_id == rule_id and not r.passed and r.severity == Severity.WARNING
    ]


def _infos_by_rule(report, rule_id: str):
    """Return INFO-severity results (passed=True) for a given rule_id."""
    return [
        r for r in report.results
        if r.rule_id == rule_id and r.passed and r.severity == Severity.INFO
    ]


@pytest.fixture(scope="module")
def validator():
    return Validator()


# ---------------------------------------------------------------------------
# Challenge Fixtures
# ---------------------------------------------------------------------------

class TestChallengeFixtures:
    """Tests for the 7 challenge fixtures."""

    def test_challenge_au_transcon_gauntlet(self, validator):
        """SYD origin, DONE4. AU transcon group 1 (east coast-Perth) hit twice -> VIOLATION.
        PER->DOH triggers implicit Asia (SWP->EU_ME).
        Open jaw SYD->MEL (both AU) is permitted.
        """
        report = validator.validate(_load("challenge_au_transcon_gauntlet.yaml"))

        # AU transcon violation: group 1 (east coast-Perth) hit 2 times
        au_violations = _violations_by_rule(report, "transcontinental_au")
        assert len(au_violations) >= 1
        assert any("east coast and Perth" in v.message for v in au_violations)

        # Implicit Asia detected (PER->DOH is SWP->EU_ME)
        asia_infos = _infos_by_rule(report, "implicit_asia")
        assert len(asia_infos) >= 1
        assert any("Asia" in r.message for r in asia_infos)

        # Open jaw SYD->MEL permitted (same country AU)
        return_results = _results_by_rule(report, "return_to_origin")
        assert all(r.passed for r in return_results)

        oj_results = _results_by_rule(report, "open_jaw_pairs")
        assert all(r.passed for r in oj_results)

    def test_challenge_us_exception_stress(self, validator):
        """JFK origin, DONE4. Uses US exceptions throughout.
        JFK->LAX = US transcon (only 1, within limit).
        YYZ->JFK = CA->US exempt from intl arrival count.
        Should pass on country rules (US exception allows transit).
        """
        report = validator.validate(_load("challenge_us_exception_stress.yaml"))

        # US transcon: only 1 (JFK->LAX), should pass
        us_transcon = _results_by_rule(report, "transcontinental_us")
        assert all(r.passed for r in us_transcon)

        # Origin country intl limit: US-origin with CA exemption -> should pass
        intl_limit = _violations_by_rule(report, "origin_country_intl_limit")
        assert len(intl_limit) == 0

        # No mid-journey return violation (US exception)
        country_return = _violations_by_rule(report, "origin_country_return")
        assert len(country_return) == 0

        # Return to origin: JFK->JFK
        return_results = _results_by_rule(report, "return_to_origin")
        assert all(r.passed for r in return_results)

    def test_challenge_doh_double_count(self, validator):
        """CAI origin, DONE3. Explicit Asia visit via NRT, then SYD->DOH
        triggers implicit Asia. Asia should NOT be double-counted.
        NRT/HND = same-city group (Tokyo).
        No ocean crossings -> OceanCrossing will fail.
        """
        report = validator.validate(_load("challenge_doh_double_count.yaml"))

        # Implicit Asia detected (SYD->DOH = SWP->EU_ME)
        asia_infos = _infos_by_rule(report, "implicit_asia")
        assert len(asia_infos) >= 1

        # Same-city resolution: NRT/HND = Tokyo
        same_city = _results_by_rule(report, "same_city_resolution")
        assert any("NRT" in r.message and "HND" in r.message for r in same_city)

        # Ocean crossings fail: no flown Atlantic or Pacific
        ocean_violations = _violations_by_rule(report, "ocean_crossings")
        assert len(ocean_violations) >= 1

    def test_challenge_jq_s7_open_jaw(self, validator):
        """NBO origin, DONE4, plating_carrier=IB.
        S7 = ineligible carrier -> VIOLATION.
        JQ recognized as QF codeshare (operating_carrier) -> INFO.
        IB plating + JQ present -> QFJQCodeshare WARNING.
        Open jaw NBO->JNB = both Africa -> permitted.
        """
        report = validator.validate(_load("challenge_jq_s7_open_jaw.yaml"))

        # Overall should fail (S7 violation)
        assert not report.passed

        # S7 ineligible carrier violation
        carrier_violations = _violations_by_rule(report, "eligible_carriers")
        assert len(carrier_violations) >= 1
        assert any("S7" in v.message for v in carrier_violations)

        # QF/JQ codeshare warning (IB plating)
        jq_warnings = _warnings_by_rule(report, "qf_jq_codeshare")
        assert len(jq_warnings) >= 1
        assert any("IB" in w.message for w in jq_warnings)

        # Open jaw NBO->JNB permitted (both Africa)
        return_results = _results_by_rule(report, "return_to_origin")
        assert all(r.passed for r in return_results)

        oj_results = _results_by_rule(report, "open_jaw_pairs")
        assert all(r.passed for r in oj_results)

        # Implicit Asia detected (MEL->DOH = SWP->EU_ME)
        asia_infos = _infos_by_rule(report, "implicit_asia")
        assert len(asia_infos) >= 1

    def test_challenge_uk_country_trap(self, validator):
        """LHR origin, DONE4. HKG->MAN mid-journey: MAN is UK = origin country
        -> OriginCountryReturn VIOLATION.
        CDG->LGW final: LGW/LHR = same-city LON -> returns to origin.
        """
        report = validator.validate(_load("challenge_uk_country_trap.yaml"))

        # Mid-journey return to origin country (UK) violation
        country_return_violations = _violations_by_rule(report, "origin_country_return")
        assert len(country_return_violations) >= 1

        # Returns to origin: LGW is same-city as LHR (LON group)
        return_results = _results_by_rule(report, "return_to_origin")
        assert all(r.passed for r in return_results)

    def test_challenge_transoceanic_surface(self, validator):
        """SYD origin, DONE4. Two transoceanic surface sectors:
        AKL->LAX (TC3->TC1) = #1, SWP-origin allows 1 (WARNING if only 1).
        JFK->LHR (TC1->TC2) = #2 -> with 2 total, SWP allows at most 1 -> VIOLATION.
        IST->BKK (TC2->TC3) = NOT restricted.
        No flown ocean crossings -> OceanCrossing also fails.
        """
        report = validator.validate(_load("challenge_transoceanic_surface.yaml"))

        # Transoceanic surface: 2 detected, SWP-origin allows at most 1 -> VIOLATION
        surface_violations = _violations_by_rule(report, "transoceanic_surface")
        assert len(surface_violations) >= 1
        assert any("2" in v.message for v in surface_violations)

        # Ocean crossings: no flown crossings -> should have violations
        ocean_violations = _violations_by_rule(report, "ocean_crossings")
        assert len(ocean_violations) >= 1

    def test_challenge_maldives_edge(self, validator):
        """MLE origin, DONE4. Open jaw MLE->CMB = MV<->LK bilateral pair -> PASS.
        DOH->CMB = EU_ME->Asia, NOT EU_ME->SWP, so no implicit Asia trigger.
        Should pass on return_to_origin and open_jaw_pairs.
        """
        report = validator.validate(_load("challenge_maldives_edge.yaml"))

        # Open jaw MLE->CMB: MV/LK bilateral -> permitted
        return_results = _results_by_rule(report, "return_to_origin")
        assert all(r.passed for r in return_results)

        oj_results = _results_by_rule(report, "open_jaw_pairs")
        assert all(r.passed for r in oj_results)

        # No implicit Asia: DOH->CMB is EU_ME->Asia, not EU_ME->SWP
        asia_results = _results_by_rule(report, "implicit_asia")
        # Should pass with "No implicit continent visits detected"
        assert all(r.passed for r in asia_results)
        # Should NOT have an INFO about SWP<->EU_ME flights
        asia_infos = _infos_by_rule(report, "implicit_asia")
        assert len(asia_infos) == 0


# ---------------------------------------------------------------------------
# Rule Fixtures
# ---------------------------------------------------------------------------

class TestRuleFixtures:
    """Tests for the 7 rule-specific fixtures."""

    def test_rule_4c_open_jaw(self, validator):
        """Open jaw LHR->CDG: GB!=FR, no bilateral pair.
        ReturnToOrigin VIOLATION, OpenJawPairs VIOLATION.
        """
        report = validator.validate(_load("rule_4c_open_jaw.yaml"))

        # Return to origin fails: CDG != LHR and not same-city
        return_violations = _violations_by_rule(report, "return_to_origin")
        assert len(return_violations) >= 1

        # Open jaw pair not permitted: GB->FR has no bilateral
        oj_violations = _violations_by_rule(report, "open_jaw_pairs")
        assert len(oj_violations) >= 1
        assert any("LHR" in v.message or "CDG" in v.message for v in oj_violations)

    def test_rule_4f_country_limit(self, validator):
        """LHR origin: 2 intl departures from UK (LHR->JFK + MAN->CDG) -> VIOLATION.
        Also 2 intl arrivals into UK (DOH->MAN + CDG->LHR) -> VIOLATION.
        """
        report = validator.validate(_load("rule_4f_country_limit.yaml"))

        intl_violations = _violations_by_rule(report, "origin_country_intl_limit")
        assert len(intl_violations) >= 1

        # Should have departure limit violation
        assert any("departure" in v.message.lower() for v in intl_violations)

        # Should have arrival limit violation
        assert any("arrival" in v.message.lower() for v in intl_violations)

    def test_rule_4i_surface_ban(self, validator):
        """LAX->LHR surface = TC1->TC2 = transoceanic surface.
        Non-SWP origin (CAI) -> no exemption -> VIOLATION.
        """
        report = validator.validate(_load("rule_4i_surface_ban.yaml"))

        surface_violations = _violations_by_rule(report, "transoceanic_surface")
        assert len(surface_violations) >= 1
        assert any("LAX" in v.message or "LHR" in v.message for v in surface_violations)

        # Ocean crossings: Atlantic via surface, not flown -> violation
        ocean_violations = _violations_by_rule(report, "ocean_crossings")
        assert any("Atlantic" in v.message for v in ocean_violations)

    def test_rule_4j_codeshare(self, validator):
        """SYD origin, plating_carrier=IB.
        JQ (operating_carrier) with QF marketing -> codeshare recognized.
        IB plating + JQ -> QFJQCodeshare WARNING.
        S7 = ineligible -> EligibleCarrier VIOLATION.
        """
        report = validator.validate(_load("rule_4j_codeshare.yaml"))

        # S7 violation
        carrier_violations = _violations_by_rule(report, "eligible_carriers")
        assert len(carrier_violations) >= 1
        assert any("S7" in v.message for v in carrier_violations)

        # QF/JQ codeshare warning (IB plating restricts JQ)
        jq_warnings = _warnings_by_rule(report, "qf_jq_codeshare")
        assert len(jq_warnings) >= 1
        assert any("IB" in w.message for w in jq_warnings)

    def test_rule_4l_au_transcon(self, validator):
        """SYD origin. SYD->PER + PER->MEL = east coast-Perth group hit 2 times.
        TranscontinentalAU VIOLATION.
        """
        report = validator.validate(_load("rule_4l_au_transcon.yaml"))

        au_violations = _violations_by_rule(report, "transcontinental_au")
        assert len(au_violations) >= 1
        assert any("east coast and Perth" in v.message for v in au_violations)
        # Verify segments involved include both transcon segments
        assert any(len(v.segments_involved) == 2 for v in au_violations)

    def test_rule_s8_citypair(self, validator):
        """CAI origin. DOH->LHR flown twice in same direction -> VIOLATION.
        CityPairDirection VIOLATION.
        """
        report = validator.validate(_load("rule_s8_citypair.yaml"))

        citypair_violations = _violations_by_rule(report, "city_pair_direction")
        assert len(citypair_violations) >= 1
        assert any("DOH" in v.message and "LHR" in v.message for v in citypair_violations)
        # Should identify 2 occurrences
        assert any("2" in v.message for v in citypair_violations)

    def test_rule_implicit_asia(self, validator):
        """SYD origin. SYD->DOH = SWP->EU_ME triggers implicit Asia (INFO).
        NRT explicitly visits Asia -> Asia NOT double-counted.
        Continents visited should include Asia exactly once.
        """
        report = validator.validate(_load("rule_implicit_asia.yaml"))

        # Implicit Asia detected
        asia_infos = _infos_by_rule(report, "implicit_asia")
        assert len(asia_infos) >= 1
        assert any("Asia" in r.message for r in asia_infos)
        assert any("SYD-DOH" in r.message or "SYD" in r.message for r in asia_infos)

        # Continent count: should pass (4 continents for DONE4)
        # SWP, EU_ME, N_America, Asia (implicit or explicit via NRT)
        continent_results = _results_by_rule(report, "continent_count")
        assert all(r.passed for r in continent_results)
