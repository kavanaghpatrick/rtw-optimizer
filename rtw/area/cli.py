"""Area CLI: `rtw area` subcommands for live-trip CRUD and validation."""

from datetime import date as Date
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from rtw.area.db import open_area_db
from rtw.area.repo import AreaRepo, NoActiveTripError, TripNotFoundError
from rtw.models import CabinClass, Segment, SegmentType, Ticket, TicketType

area_app = typer.Typer(
    name="area",
    help="Live RTW trip state -- create, modify, validate the current itinerary.",
    no_args_is_help=True,
)

_console = Console()


def _repo() -> AreaRepo:
    return AreaRepo(open_area_db())


def _require_active(repo: AreaRepo) -> int:
    try:
        return repo.get_active_or_raise()
    except NoActiveTripError as exc:
        _console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


# -- trip-level commands -----------------------------------------------------


@area_app.command("new")
def area_new(
    slug: Annotated[str, typer.Option("--slug", help="Unique trip identifier.")],
    ticket_type: Annotated[
        str, typer.Option("--type", help="DONE3, DONE4, AONE4, LONE4, ...")
    ],
    cabin: Annotated[
        str, typer.Option("--cabin", help="economy | business | first")
    ],
    origin: Annotated[str, typer.Option("--origin", help="3-letter IATA origin")],
    passengers: Annotated[int, typer.Option("--pax")] = 1,
    departure: Annotated[
        Optional[str], typer.Option("--departure", help="YYYY-MM-DD")
    ] = None,
    plating: Annotated[
        Optional[str], typer.Option("--plating", help="2-letter plating carrier")
    ] = None,
    pnr: Annotated[Optional[str], typer.Option("--pnr", help="Record locator")] = None,
) -> None:
    """Create a new trip and set it active."""
    try:
        ticket = Ticket(
            type=TicketType(ticket_type.upper()),
            cabin=CabinClass(cabin.lower()),
            origin=origin.upper(),
            passengers=passengers,
            departure=Date.fromisoformat(departure) if departure else None,
            plating_carrier=plating,
        )
    except Exception as exc:
        _console.print(f"[red]Invalid ticket:[/red] {exc}")
        raise typer.Exit(1) from exc

    repo = _repo()
    try:
        trip_id = repo.create_trip(slug, ticket, pnr=pnr, set_active=True)
    except Exception as exc:
        _console.print(f"[red]Failed to create trip:[/red] {exc}")
        raise typer.Exit(1) from exc
    _console.print(
        f"[green]Created trip[/green] {slug} (id={trip_id}) and set active."
    )


@area_app.command("list")
def area_list() -> None:
    """List all trips; active is marked with *."""
    trips = _repo().list_trips()
    if not trips:
        _console.print("[dim]No trips yet. Use `rtw area new` to create one.[/dim]")
        return
    table = Table(title="Trips")
    table.add_column("Active")
    table.add_column("Slug")
    table.add_column("PNR")
    table.add_column("Type")
    table.add_column("Origin")
    table.add_column("Plating")
    table.add_column("Segments")
    for t in trips:
        table.add_row(
            "*" if t["is_active"] else "",
            t["slug"],
            t["pnr"] or "",
            t["ticket_type"],
            t["origin"],
            t["plating_carrier"] or "",
            str(t["segment_count"]),
        )
    _console.print(table)


@area_app.command("switch")
def area_switch(slug: Annotated[str, typer.Argument(help="Trip slug")]) -> None:
    """Switch the active trip by slug."""
    repo = _repo()
    tid = repo.get_trip_by_slug(slug)
    if tid is None:
        _console.print(f"[red]No trip with slug[/red] '{slug}'")
        raise typer.Exit(1)
    repo.set_active(tid)
    _console.print(f"[green]Active trip:[/green] {slug}")


@area_app.command("show")
def area_show(
    slug: Annotated[
        Optional[str], typer.Option("--slug", help="Trip to show; defaults to active.")
    ] = None,
) -> None:
    """Show trip meta + ordered segments."""
    repo = _repo()
    if slug:
        tid = repo.get_trip_by_slug(slug)
        if tid is None:
            _console.print(f"[red]No trip with slug[/red] '{slug}'")
            raise typer.Exit(1)
    else:
        tid = _require_active(repo)

    trip = next((t for t in repo.list_trips() if t["id"] == tid), None)
    if trip is None:
        _console.print("[red]Trip not found.[/red]")
        raise typer.Exit(1)
    _console.print(
        f"[bold]{trip['slug']}[/bold]  type={trip['ticket_type']}  "
        f"cabin={trip['cabin']}  origin={trip['origin']}  "
        f"pnr={trip['pnr'] or '-'}  plating={trip['plating_carrier'] or '-'}"
    )
    segs = repo.list_segments(tid)
    if not segs:
        _console.print("[dim]  (no segments yet -- use `rtw area add`)[/dim]")
        return
    table = Table()
    table.add_column("#")
    table.add_column("From")
    table.add_column("To")
    table.add_column("Carrier")
    table.add_column("Flight")
    table.add_column("Date")
    table.add_column("Type")
    for s in segs:
        table.add_row(
            str(s["position"]),
            s["from_airport"],
            s["to_airport"],
            s["carrier"] or "",
            s["flight"] or "",
            s["date"] or "",
            s["segment_type"],
        )
    _console.print(table)


@area_app.command("rm-trip")
def area_rm_trip(
    slug: Annotated[str, typer.Argument(help="Slug of trip to delete")],
) -> None:
    """Delete a trip (and all its segments)."""
    repo = _repo()
    tid = repo.get_trip_by_slug(slug)
    if tid is None:
        _console.print(f"[red]No trip with slug[/red] '{slug}'")
        raise typer.Exit(1)
    repo.delete_trip(tid)
    _console.print(f"[green]Deleted trip[/green] {slug}")


# -- segment-level commands --------------------------------------------------


@area_app.command("add")
def area_add(
    from_airport: Annotated[str, typer.Option("--from", help="3-letter IATA")],
    to_airport: Annotated[str, typer.Option("--to", help="3-letter IATA")],
    carrier: Annotated[Optional[str], typer.Option("--carrier")] = None,
    flight: Annotated[Optional[str], typer.Option("--flight")] = None,
    date: Annotated[
        Optional[str], typer.Option("--date", help="YYYY-MM-DD")
    ] = None,
    seg_type: Annotated[
        str, typer.Option("--type", help="stopover | transit | surface | final")
    ] = "stopover",
    position: Annotated[
        Optional[int],
        typer.Option(
            "--pos", help="Insert at position (1-based). Default: append."
        ),
    ] = None,
    notes: Annotated[Optional[str], typer.Option("--notes")] = None,
) -> None:
    """Add a segment to the active trip."""
    repo = _repo()
    tid = _require_active(repo)
    try:
        seg = Segment(
            **{"from": from_airport.upper(), "to": to_airport.upper()},
            carrier=carrier,
            flight=flight,
            date=Date.fromisoformat(date) if date else None,
            type=SegmentType(seg_type),
            notes=notes,
        )
    except Exception as exc:
        _console.print(f"[red]Invalid segment:[/red] {exc}")
        raise typer.Exit(1) from exc

    try:
        repo.add_segment(tid, seg, position=position)
    except (TripNotFoundError, ValueError) as exc:
        _console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc

    where = f"at position {position}" if position else "appended"
    _console.print(
        f"[green]Added[/green] {seg.from_airport}->{seg.to_airport} {where}."
    )


@area_app.command("move")
def area_move(
    from_pos: Annotated[int, typer.Argument(help="Current position (1-based)")],
    to_pos: Annotated[int, typer.Argument(help="New position (1-based)")],
) -> None:
    """Move a segment from one position to another."""
    repo = _repo()
    tid = _require_active(repo)
    try:
        repo.move_segment(tid, from_pos, to_pos)
    except (TripNotFoundError, ValueError) as exc:
        _console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    _console.print(f"[green]Moved[/green] segment {from_pos} -> {to_pos}")


@area_app.command("rm")
def area_rm(
    position: Annotated[int, typer.Argument(help="Position to remove (1-based)")],
) -> None:
    """Remove a segment from the active trip."""
    repo = _repo()
    tid = _require_active(repo)
    try:
        repo.remove_segment(tid, position)
    except (TripNotFoundError, ValueError) as exc:
        _console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    _console.print(f"[green]Removed[/green] segment {position}.")


# -- validator integration ---------------------------------------------------


@area_app.command("validate")
def area_validate(
    json_out: Annotated[bool, typer.Option("--json")] = False,
    plain: Annotated[bool, typer.Option("--plain")] = False,
) -> None:
    """Run the Rule 3015 validator against the active trip."""
    from rtw.output import get_formatter
    from rtw.validator import Validator

    repo = _repo()
    tid = _require_active(repo)
    try:
        itin = repo.load_itinerary(tid)
    except Exception as exc:
        _console.print(f"[red]Cannot build itinerary:[/red] {exc}")
        raise typer.Exit(1) from exc

    report = Validator().validate(itin)
    fmt_name = "json" if json_out else ("plain" if plain else "rich")
    fmt = get_formatter(fmt_name)
    typer.echo(fmt.format_validation(report))
    if not report.passed:
        raise typer.Exit(code=1)
