"""Tests for rtw build CLI command."""

import datetime
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from rtw.cli import app
from rtw.models import Itinerary


runner = CliRunner()

ROUTE_4SEG = "LAX-HND:JL,HND-SYD:JL,SYD-DOH:QR,DOH-LAX:QR"
ROUTE_5SEG = "LAX-HND:JL,HND-SYD:JL,SYD-DOH:QR,DOH-LHR:QR,LHR-LAX:BA"


class TestBuildBasic:
    def test_outputs_yaml(self):
        result = runner.invoke(app, ["build", "--route", ROUTE_4SEG, "--origin", "LAX"])
        assert result.exit_code == 0
        data = yaml.safe_load(result.output)
        assert data["ticket"]["type"] == "DONE4"
        assert data["ticket"]["origin"] == "LAX"
        assert len(data["segments"]) == 4

    def test_segments_match_route(self):
        result = runner.invoke(app, ["build", "--route", ROUTE_4SEG, "--origin", "LAX"])
        data = yaml.safe_load(result.output)
        segs = data["segments"]
        assert segs[0]["from"] == "LAX"
        assert segs[0]["to"] == "HND"
        assert segs[0]["carrier"] == "JL"
        assert segs[-1]["from"] == "DOH"
        assert segs[-1]["to"] == "LAX"
        assert segs[-1]["carrier"] == "QR"

    def test_last_segment_is_final(self):
        result = runner.invoke(app, ["build", "--route", ROUTE_4SEG, "--origin", "LAX"])
        data = yaml.safe_load(result.output)
        assert data["segments"][-1]["type"] == "final"
        for seg in data["segments"][:-1]:
            assert seg["type"] == "stopover"

    def test_infers_origin_from_first_segment(self):
        result = runner.invoke(app, ["build", "--route", ROUTE_4SEG])
        data = yaml.safe_load(result.output)
        assert data["ticket"]["origin"] == "LAX"

    def test_lowercase_uppercased(self):
        result = runner.invoke(app, ["build", "--route", "lax-hnd:jl,hnd-lax:jl", "--origin", "lax"])
        data = yaml.safe_load(result.output)
        assert data["ticket"]["origin"] == "LAX"
        assert data["segments"][0]["from"] == "LAX"
        assert data["segments"][0]["carrier"] == "JL"


class TestBuildDates:
    def test_default_departure_is_future(self):
        result = runner.invoke(app, ["build", "--route", ROUTE_4SEG])
        data = yaml.safe_load(result.output)
        first_date = datetime.date.fromisoformat(data["segments"][0]["date"])
        assert first_date > datetime.date.today()

    def test_explicit_departure(self):
        result = runner.invoke(app, ["build", "--route", ROUTE_4SEG, "--departure", "2026-06-01"])
        data = yaml.safe_load(result.output)
        assert data["segments"][0]["date"] == "2026-06-01"

    def test_gap_between_segments(self):
        result = runner.invoke(app, ["build", "--route", ROUTE_4SEG, "--departure", "2026-06-01", "--gap", "3"])
        data = yaml.safe_load(result.output)
        dates = [datetime.date.fromisoformat(s["date"]) for s in data["segments"]]
        # Gap of 3 days between stopovers
        assert (dates[1] - dates[0]).days == 3
        assert (dates[2] - dates[1]).days == 3

    def test_default_gap_is_4(self):
        result = runner.invoke(app, ["build", "--route", ROUTE_4SEG, "--departure", "2026-06-01"])
        data = yaml.safe_load(result.output)
        dates = [datetime.date.fromisoformat(s["date"]) for s in data["segments"]]
        assert (dates[1] - dates[0]).days == 4


class TestBuildOptions:
    def test_ticket_type_override(self):
        result = runner.invoke(app, ["build", "--route", ROUTE_4SEG, "--type", "LONE3"])
        data = yaml.safe_load(result.output)
        assert data["ticket"]["type"] == "LONE3"

    def test_cabin_override(self):
        result = runner.invoke(app, ["build", "--route", ROUTE_4SEG, "--cabin", "economy"])
        data = yaml.safe_load(result.output)
        assert data["ticket"]["cabin"] == "economy"

    def test_write_to_file(self, tmp_path):
        out_file = tmp_path / "test.yaml"
        result = runner.invoke(app, ["build", "--route", ROUTE_4SEG, "--out", str(out_file)])
        assert result.exit_code == 0
        assert out_file.exists()
        data = yaml.safe_load(out_file.read_text())
        assert len(data["segments"]) == 4

    def test_roundtrip_validate(self, tmp_path):
        """Build YAML then load it back as an Itinerary."""
        out_file = tmp_path / "roundtrip.yaml"
        runner.invoke(app, ["build", "--route", ROUTE_4SEG, "--origin", "LAX", "--out", str(out_file)])
        data = yaml.safe_load(out_file.read_text())
        itinerary = Itinerary(**data)
        assert len(itinerary.segments) == 4
        assert itinerary.ticket.origin == "LAX"


class TestBuildValidation:
    def test_validate_pass(self):
        result = runner.invoke(app, ["build", "--route", ROUTE_4SEG, "--origin", "LAX", "--departure", "2026-04-01", "--validate"])
        assert result.exit_code == 0
        assert "PASS" in result.output

    def test_ntp_output(self):
        result = runner.invoke(app, ["build", "--route", ROUTE_4SEG, "--origin", "LAX", "--departure", "2026-04-01", "--ntp"])
        assert result.exit_code == 0
        assert "NTP:" in result.output
        assert "LAX-HND" in result.output


class TestBuildErrors:
    def test_missing_route(self):
        result = runner.invoke(app, ["build"])
        assert result.exit_code == 2

    def test_invalid_route_format(self):
        result = runner.invoke(app, ["build", "--route", "INVALID"])
        assert result.exit_code == 2

    def test_invalid_ticket_type(self):
        result = runner.invoke(app, ["build", "--route", ROUTE_4SEG, "--type", "BOGUS"])
        assert result.exit_code == 2

    def test_invalid_date(self):
        result = runner.invoke(app, ["build", "--route", ROUTE_4SEG, "--departure", "not-a-date"])
        assert result.exit_code == 2
