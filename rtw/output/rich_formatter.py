"""Rich-based output formatter with colored tables, panels, and severity coding."""

from __future__ import annotations

from io import StringIO

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from rtw.booking import BookingScript
from rtw.models import (
    CostEstimate,
    NTPEstimate,
    SegmentValue,
    Severity,
    ValidationReport,
)

# Severity -> Rich style mapping
_SEVERITY_STYLES = {
    Severity.VIOLATION: "bold red",
    Severity.WARNING: "yellow",
    Severity.INFO: "blue",
}

# Verdict -> Rich style mapping
_VERDICT_STYLES = {
    "Excellent": "bold green",
    "Good": "blue",
    "Moderate": "yellow",
    "Low": "bold red",
}


def _render(renderable) -> str:
    """Render a Rich object to a string."""
    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=120)
    console.print(renderable)
    return buf.getvalue()


class RichFormatter:
    """Format RTW results using Rich tables and panels."""

    def format_validation(self, report: ValidationReport) -> str:
        """Format a validation report with color-coded severity."""
        parts: list[str] = []

        # Summary panel
        ticket = report.itinerary.ticket
        total = len(report.results)
        passed = sum(1 for r in report.results if r.passed)
        violations = report.violation_count
        warnings = report.warning_count

        if report.passed:
            status_text = Text("PASS", style="bold green")
        else:
            status_text = Text("FAIL", style="bold red")

        summary_text = Text()
        summary_text.append("Status:     ")
        summary_text.append_text(status_text)
        summary_text.append(f"\nTicket:     {ticket.type.value} ({ticket.cabin.value.title()}) from {ticket.origin}")
        summary_text.append(f"\nPassengers: {ticket.passengers}")
        summary_text.append(
            f"\nSegments:   {len(report.itinerary.flown_segments)} flown, "
            f"{len(report.itinerary.surface_segments)} surface"
        )
        summary_text.append(f"\nRules:      {passed}/{total} passed")
        if violations:
            summary_text.append(f"\nViolations: ")
            summary_text.append(str(violations), style="bold red")
        else:
            summary_text.append(f"\nViolations: {violations}")
        if warnings:
            summary_text.append(f"\nWarnings:   ")
            summary_text.append(str(warnings), style="yellow")
        else:
            summary_text.append(f"\nWarnings:   {warnings}")

        parts.append(_render(Panel(summary_text, title="Validation Summary", border_style="cyan")))

        # Split results into issues and passes
        issues = [r for r in report.results if not r.passed]
        passes = [r for r in report.results if r.passed and r.severity != Severity.INFO]
        infos = [r for r in report.results if r.passed and r.severity == Severity.INFO]

        # Issues table (violations + warnings)
        if issues:
            issue_table = Table(title="Issues", show_lines=True, border_style="red")
            issue_table.add_column("#", style="dim", justify="right", width=3)
            issue_table.add_column("Severity", width=9)
            issue_table.add_column("Rule", style="cyan", max_width=30)
            issue_table.add_column("Detail", ratio=1)

            for i, r in enumerate(issues, 1):
                sev_style = _SEVERITY_STYLES.get(r.severity, "red")
                sev_text = Text(r.severity.value.upper(), style=sev_style)
                detail = Text(r.message)
                if r.fix_suggestion:
                    detail.append(f"\nFix: {r.fix_suggestion}", style="dim")
                if r.rule_reference:
                    detail.append(f"  [{r.rule_reference}]", style="dim")

                issue_table.add_row(str(i), sev_text, r.rule_name, detail)

            parts.append(_render(issue_table))

        # Passed rules table (compact)
        if passes:
            pass_table = Table(title="Passed Rules", show_lines=False, border_style="green", padding=(0, 1))
            pass_table.add_column("Rule", style="cyan", max_width=35)
            pass_table.add_column(Text("Status", style="green"), width=4, justify="center")
            pass_table.add_column("Detail", ratio=1)

            for r in passes:
                pass_table.add_row(r.rule_name, Text("OK", style="green"), r.message)

            parts.append(_render(pass_table))

        # Info notes (collapsed)
        if infos:
            info_table = Table(title="Info", show_lines=False, border_style="blue", padding=(0, 1))
            info_table.add_column("Rule", style="cyan", max_width=35)
            info_table.add_column("Detail", ratio=1, style="dim")

            for r in infos:
                info_table.add_row(r.rule_name, r.message)

            parts.append(_render(info_table))

        return "\n".join(parts)

    def format_ntp(self, estimates: list[NTPEstimate]) -> str:
        """Format NTP estimates as a table with a total row."""
        table = Table(title="NTP Estimates", show_lines=True)
        table.add_column("#", style="dim", justify="right")
        table.add_column("Route", style="cyan")
        table.add_column("Carrier")
        table.add_column("Distance (mi)", justify="right")
        table.add_column("Method")
        table.add_column("Rate", justify="right")
        table.add_column("NTP", justify="right", style="bold green")
        table.add_column("Confidence")
        table.add_column("Notes")

        total_ntp = 0.0
        total_distance = 0.0

        for e in estimates:
            rate_str = f"{e.rate:.0%}" if e.rate is not None else "-"
            table.add_row(
                str(e.segment_index + 1),
                e.route,
                e.carrier,
                f"{e.distance_miles:,.0f}",
                e.method.value,
                rate_str,
                f"{e.estimated_ntp:,.0f}",
                e.confidence,
                e.notes,
            )
            total_ntp += e.estimated_ntp
            total_distance += e.distance_miles

        # Total row
        table.add_row(
            "",
            Text("TOTAL", style="bold"),
            "",
            f"{total_distance:,.0f}",
            "",
            "",
            Text(f"{total_ntp:,.0f}", style="bold green"),
            "",
            "",
        )

        return _render(table)

    def format_cost(self, estimate: CostEstimate) -> str:
        """Format a cost estimate as a panel."""
        lines = [
            f"Origin:          {estimate.origin}",
            f"Ticket Type:     {estimate.ticket_type.value}",
            f"Base Fare:       ${estimate.base_fare_usd:,.2f}",
            f"Total YQ:        ${estimate.total_yq_usd:,.2f}",
            f"Per Person:      ${estimate.total_per_person_usd:,.2f}",
            f"Passengers:      {estimate.passengers}",
            f"Total All Pax:   ${estimate.total_all_pax_usd:,.2f}",
            f"Plating Carrier: {estimate.plating_carrier}",
        ]
        if estimate.notes:
            lines.append(f"Notes:           {estimate.notes}")

        text = Text("\n".join(lines))
        panel = Panel(text, title="Cost Estimate", border_style="green")
        return _render(panel)

    def format_value(self, values: list[SegmentValue]) -> str:
        """Format segment value analysis with verdict coloring."""
        table = Table(title="Segment Value Analysis", show_lines=True)
        table.add_column("#", style="dim", justify="right")
        table.add_column("Route", style="cyan")
        table.add_column("Carrier")
        table.add_column("J Cost (USD)", justify="right")
        table.add_column("Verdict", min_width=10)
        table.add_column("Suggestion")
        table.add_column("Source", style="dim")

        for v in values:
            verdict_style = _VERDICT_STYLES.get(v.verdict, "")
            verdict = Text(v.verdict, style=verdict_style)

            table.add_row(
                str(v.segment_index + 1),
                v.route,
                v.carrier,
                f"${v.estimated_j_cost_usd:,.0f}",
                verdict,
                v.suggestion,
                v.source,
            )

        return _render(table)

    def format_booking(self, script: BookingScript) -> str:
        """Format a booking script with panels for each section."""
        parts: list[str] = []

        # Opening
        parts.append(_render(Panel(script.opening, title="Opening Script", border_style="cyan")))

        # Segments
        for seg in script.segments:
            border = "yellow" if seg.warnings else "green"
            content = seg.phone_instruction
            if seg.warnings:
                content += "\n\n" + "\n".join(f"  WARNING: {w}" for w in seg.warnings)
            parts.append(
                _render(
                    Panel(
                        content,
                        title=f"Segment {seg.segment_index + 1}: {seg.route}",
                        border_style=border,
                    )
                )
            )

        # Closing
        parts.append(_render(Panel(script.closing, title="Closing Checklist", border_style="cyan")))

        # GDS commands
        gds_block = "\n".join(script.gds_commands)
        parts.append(_render(Panel(gds_block, title="GDS Commands (Amadeus)", border_style="blue")))

        # Warnings summary
        if script.warnings:
            warn_text = "\n".join(f"  - {w}" for w in script.warnings)
            parts.append(
                _render(
                    Panel(
                        warn_text, title=f"Warnings ({len(script.warnings)})", border_style="yellow"
                    )
                )
            )

        return "\n".join(parts)
