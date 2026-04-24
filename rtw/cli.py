"""RTW Optimizer CLI -- oneworld Explorer ticket optimization.

Provides commands for validating, costing, NTP estimation, value analysis,
booking script generation, and scraping for RTW itineraries.
"""

import difflib
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Optional

import typer

if TYPE_CHECKING:
    from rtw.search.models import ScoredCandidate
    from rtw.verify.models import VerifyOption, VerifyResult
import yaml
from pydantic import ValidationError

from rtw.models import Itinerary

# ---------------------------------------------------------------------------
# App and sub-apps
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="rtw",
    help="oneworld Explorer RTW ticket optimizer -- validate, cost, NTP, booking.",
    no_args_is_help=True,
)

scrape_app = typer.Typer(
    name="scrape",
    help="Scrape flight prices and availability.",
    no_args_is_help=True,
)

config_app = typer.Typer(
    name="config",
    help="Manage RTW Optimizer configuration.",
    no_args_is_help=True,
)

cache_app = typer.Typer(
    name="cache",
    help="Manage the scrape cache.",
    no_args_is_help=True,
)

login_app = typer.Typer(
    name="login",
    help="Manage service logins.",
    no_args_is_help=True,
)

kb_app = typer.Typer(
    name="kb",
    help="Query the RTW travel intelligence knowledge base.",
    no_args_is_help=True,
)

from rtw.area.cli import area_app  # noqa: E402

app.add_typer(scrape_app, name="scrape")
app.add_typer(config_app, name="config")
app.add_typer(cache_app, name="cache")
app.add_typer(login_app, name="login")
app.add_typer(kb_app, name="kb")
app.add_typer(area_app, name="area")


# ---------------------------------------------------------------------------
# Global option types
# ---------------------------------------------------------------------------

JsonFlag = Annotated[bool, typer.Option("--json", help="Output as JSON.")]
PlainFlag = Annotated[bool, typer.Option("--plain", help="Output as plain text (no color).")]
VerboseFlag = Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output.")]
QuietFlag = Annotated[bool, typer.Option("--quiet", "-q", help="Suppress non-essential output.")]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_format(json_flag: bool = False, plain_flag: bool = False) -> str:
    """Determine output format: json > plain > TTY auto-detect > rich."""
    if json_flag:
        return "json"
    if plain_flag:
        return "plain"
    # Auto-detect: use rich if stdout is a TTY, plain otherwise
    if sys.stdout.isatty():
        return "rich"
    return "plain"


def _setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure logging based on verbosity flags."""
    if quiet:
        logging.basicConfig(level=logging.ERROR)
    elif verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING)


def _known_airport_codes() -> list[str]:
    """Return a list of known airport codes for fuzzy matching."""
    try:
        from rtw.airports import airports_db

        return list(airports_db.keys())
    except SystemExit:
        return []


def _fuzzy_airport_suggestion(code: str) -> str:
    """Suggest close airport codes using difflib."""
    known = _known_airport_codes()
    if not known:
        return ""
    matches = difflib.get_close_matches(code.upper(), known, n=3, cutoff=0.6)
    if matches:
        return f" Did you mean: {', '.join(matches)}?"
    return ""


def _load_itinerary(file: str) -> Itinerary:
    """Load a YAML file and parse it into an Itinerary model.

    Provides helpful error messages for:
    - File not found
    - YAML parse errors (with line/column)
    - Pydantic validation errors (with field-level messages)
    - Unknown airport codes (with fuzzy suggestions)
    """
    path = Path(file)

    # File not found
    if not path.exists():
        hint = ""
        if not path.is_absolute():
            hint = f" (looked in {Path.cwd()})"
        raise typer.BadParameter(
            f"File not found: {file}{hint}\n  Hint: Check the file path and try again."
        )

    # YAML parse
    try:
        with open(path) as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        msg = f"YAML parse error in {file}"
        if hasattr(exc, "problem_mark") and exc.problem_mark is not None:
            mark = exc.problem_mark
            msg += f" at line {mark.line + 1}, column {mark.column + 1}"
        if hasattr(exc, "problem") and exc.problem:
            msg += f": {exc.problem}"
        raise typer.BadParameter(msg)

    if not isinstance(raw, dict):
        raise typer.BadParameter(
            f"Expected a YAML mapping (dict) in {file}, got {type(raw).__name__}"
        )

    # Pydantic validation
    try:
        return Itinerary(**raw)
    except ValidationError as exc:
        lines = [f"Validation errors in {file}:"]
        for err in exc.errors():
            loc = " -> ".join(str(x) for x in err["loc"])
            lines.append(f"  {loc}: {err['msg']}")

            # Fuzzy match airport codes
            if "airport" in loc.lower() and err.get("input"):
                suggestion = _fuzzy_airport_suggestion(str(err["input"]))
                if suggestion:
                    lines.append(f"    {suggestion}")

        raise typer.BadParameter("\n".join(lines))


def _error_panel(message: str) -> None:
    """Print an error message, using Rich panel if available."""
    try:
        from rich.console import Console
        from rich.panel import Panel

        console = Console(stderr=True)
        console.print(Panel(message, title="Error", border_style="red"))
    except Exception:
        typer.echo(f"Error: {message}", err=True)


# ---------------------------------------------------------------------------
# T041: Core commands
# ---------------------------------------------------------------------------


@app.command()
def validate(
    file: str = typer.Argument(help="Path to itinerary YAML file"),
    json: JsonFlag = False,
    plain: PlainFlag = False,
    verbose: VerboseFlag = False,
    quiet: QuietFlag = False,
) -> None:
    """Validate an itinerary against oneworld Rule 3015."""
    _setup_logging(verbose, quiet)
    try:
        itinerary = _load_itinerary(file)
        from rtw.validator import Validator
        from rtw.output import get_formatter

        validator = Validator()
        report = validator.validate(itinerary)
        fmt = get_formatter(_get_format(json, plain))
        typer.echo(fmt.format_validation(report))

        if not report.passed:
            raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except typer.BadParameter:
        raise
    except Exception as exc:
        _error_panel(str(exc))
        raise typer.Exit(code=2)


@app.command()
def cost(
    file: str = typer.Argument(help="Path to itinerary YAML file"),
    json: JsonFlag = False,
    plain: PlainFlag = False,
    verbose: VerboseFlag = False,
    quiet: QuietFlag = False,
) -> None:
    """Estimate costs for an RTW itinerary."""
    _setup_logging(verbose, quiet)
    try:
        itinerary = _load_itinerary(file)
        from rtw.cost import CostEstimator
        from rtw.output import get_formatter

        estimator = CostEstimator()
        estimate = estimator.estimate_total(itinerary)
        fmt = get_formatter(_get_format(json, plain))
        typer.echo(fmt.format_cost(estimate))

        if verbose and not quiet:
            # Show origin comparison and plating comparison
            origins = estimator.compare_origins(itinerary.ticket.type)
            plating = estimator.compare_plating(itinerary)
            typer.echo("\nOrigin comparison (cheapest first):")
            for o in origins[:5]:
                typer.echo(f"  {o['origin']} ({o['name']}): ${o['fare_usd']:,.0f}")
            typer.echo("\nPlating comparison (cheapest first):")
            for p in plating[:5]:
                typer.echo(f"  {p['plating_carrier']} ({p['name']}): ${p['total_yq_usd']:,.0f} YQ")

    except typer.Exit:
        raise
    except typer.BadParameter:
        raise
    except Exception as exc:
        from rtw.cost import FareLookupError

        if isinstance(exc, FareLookupError):
            _error_panel(str(exc))
            raise typer.Exit(code=2)
        _error_panel(str(exc))
        raise typer.Exit(code=2)


@app.command()
def ntp(
    file: str = typer.Argument(help="Path to itinerary YAML file"),
    json: JsonFlag = False,
    plain: PlainFlag = False,
    verbose: VerboseFlag = False,
    quiet: QuietFlag = False,
) -> None:
    """Estimate New Tier Points (NTP) earnings for an itinerary."""
    _setup_logging(verbose, quiet)
    try:
        itinerary = _load_itinerary(file)
        from rtw.ntp import NTPCalculator
        from rtw.output import get_formatter

        calc = NTPCalculator()
        estimates = calc.calculate(itinerary)
        fmt = get_formatter(_get_format(json, plain))
        typer.echo(fmt.format_ntp(estimates))

    except typer.Exit:
        raise
    except typer.BadParameter:
        raise
    except Exception as exc:
        _error_panel(str(exc))
        raise typer.Exit(code=2)


@app.command()
def value(
    file: str = typer.Argument(help="Path to itinerary YAML file"),
    json: JsonFlag = False,
    plain: PlainFlag = False,
    verbose: VerboseFlag = False,
    quiet: QuietFlag = False,
) -> None:
    """Analyze per-segment value of an itinerary."""
    _setup_logging(verbose, quiet)
    try:
        itinerary = _load_itinerary(file)
        from rtw.value import SegmentValueAnalyzer
        from rtw.output import get_formatter

        analyzer = SegmentValueAnalyzer()
        values = analyzer.analyze(itinerary)
        fmt = get_formatter(_get_format(json, plain))
        typer.echo(fmt.format_value(values))

    except typer.Exit:
        raise
    except typer.BadParameter:
        raise
    except Exception as exc:
        _error_panel(str(exc))
        raise typer.Exit(code=2)


@app.command()
def booking(
    file: str = typer.Argument(help="Path to itinerary YAML file"),
    json: JsonFlag = False,
    plain: PlainFlag = False,
    verbose: VerboseFlag = False,
    quiet: QuietFlag = False,
) -> None:
    """Generate a booking script for an itinerary."""
    _setup_logging(verbose, quiet)
    try:
        itinerary = _load_itinerary(file)
        from rtw.booking import BookingGenerator
        from rtw.output import get_formatter

        generator = BookingGenerator()
        script = generator.generate(itinerary)
        fmt = get_formatter(_get_format(json, plain))
        typer.echo(fmt.format_booking(script))

    except typer.Exit:
        raise
    except typer.BadParameter:
        raise
    except Exception as exc:
        _error_panel(str(exc))
        raise typer.Exit(code=2)


# ---------------------------------------------------------------------------
# T042: Analyze and utility commands
# ---------------------------------------------------------------------------


@app.command()
def analyze(
    file: str = typer.Argument(help="Path to itinerary YAML file"),
    json: JsonFlag = False,
    plain: PlainFlag = False,
    verbose: VerboseFlag = False,
    quiet: QuietFlag = False,
) -> None:
    """Run full analysis pipeline: validate, cost, NTP, value."""
    _setup_logging(verbose, quiet)
    try:
        itinerary = _load_itinerary(file)

        from rtw.validator import Validator
        from rtw.cost import CostEstimator
        from rtw.ntp import NTPCalculator
        from rtw.value import SegmentValueAnalyzer
        from rtw.output import get_formatter

        fmt = get_formatter(_get_format(json, plain))

        # Step 1: Validate
        if not quiet:
            typer.echo("--- Validation ---")
        validator = Validator()
        report = validator.validate(itinerary)
        typer.echo(fmt.format_validation(report))

        # Step 2: Cost
        if not quiet:
            typer.echo("\n--- Cost Estimate ---")
        estimator = CostEstimator()
        estimate = estimator.estimate_total(itinerary)
        typer.echo(fmt.format_cost(estimate))

        # Step 3: NTP
        if not quiet:
            typer.echo("\n--- NTP Estimates ---")
        ntp_calc = NTPCalculator()
        ntp_estimates = ntp_calc.calculate(itinerary)
        typer.echo(fmt.format_ntp(ntp_estimates))

        # Step 4: Value
        if not quiet:
            typer.echo("\n--- Segment Value ---")
        analyzer = SegmentValueAnalyzer()
        values = analyzer.analyze(itinerary)
        typer.echo(fmt.format_value(values))

        if not report.passed:
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except typer.BadParameter:
        raise
    except Exception as exc:
        _error_panel(str(exc))
        raise typer.Exit(code=2)


@app.command()
def continent(
    codes: list[str] = typer.Argument(help="Airport IATA codes to look up"),
    json: JsonFlag = False,
    plain: PlainFlag = False,
) -> None:
    """Look up continent and tariff conference for airport codes."""
    from rtw.continents import get_continent, get_tariff_conference
    import json as json_mod

    results = []
    for code in codes:
        code_upper = code.upper()
        cont = get_continent(code_upper)
        if cont is not None:
            tc = get_tariff_conference(cont)
            results.append(
                {
                    "airport": code_upper,
                    "continent": cont.value,
                    "tariff_conference": tc.value,
                }
            )
        else:
            suggestion = _fuzzy_airport_suggestion(code_upper)
            results.append(
                {
                    "airport": code_upper,
                    "continent": "unknown",
                    "tariff_conference": "unknown",
                    "note": f"Unknown airport code.{suggestion}",
                }
            )

    if json:
        typer.echo(json_mod.dumps(results, indent=2))
    else:
        for r in results:
            line = f"  {r['airport']}: {r['continent']} ({r['tariff_conference']})"
            if "note" in r:
                line += f"  -- {r['note']}"
            typer.echo(line)


@app.command()
def show(
    file: str = typer.Argument(help="Path to itinerary YAML file"),
    json: JsonFlag = False,
    plain: PlainFlag = False,
) -> None:
    """Pretty-print an itinerary's segments."""
    try:
        itinerary = _load_itinerary(file)
    except typer.BadParameter:
        raise
    except Exception as exc:
        _error_panel(str(exc))
        raise typer.Exit(code=2)

    if json:
        import json as json_mod

        data = itinerary.model_dump(mode="json")
        typer.echo(json_mod.dumps(data, indent=2))
        return

    ticket = itinerary.ticket
    typer.echo(
        f"Itinerary: {ticket.type.value} ({ticket.cabin.value.title()}) from {ticket.origin}"
    )
    typer.echo(f"Passengers: {ticket.passengers}")
    if ticket.departure:
        typer.echo(f"Departure: {ticket.departure}")
    if ticket.plating_carrier:
        typer.echo(f"Plating: {ticket.plating_carrier}")
    typer.echo(
        f"Segments: {len(itinerary.flown_segments)} flown, "
        f"{len(itinerary.surface_segments)} surface"
    )
    typer.echo("")

    for i, seg in enumerate(itinerary.segments):
        idx = f"{i + 1:>2}"
        route = f"{seg.from_airport}-{seg.to_airport}"
        carrier = seg.carrier or "SURFACE"
        flight = seg.flight or ""
        date_str = str(seg.date) if seg.date else ""
        seg_type = seg.type.value

        line = f"  {idx}. {route:<10} {carrier:<4} {flight:<8} {date_str:<12} [{seg_type}]"
        if seg.notes:
            line += f"  {seg.notes}"
        typer.echo(line)


@app.command(name="new")
def new_template(
    template: str = typer.Option(
        ...,
        "--template",
        "-t",
        help="Template name (e.g. done4-eastbound, done5-eastbound)",
    ),
) -> None:
    """Output a YAML itinerary template."""
    templates_dir = Path(__file__).parent / "data" / "templates"

    # Try exact match first, then with .yaml extension
    candidates = [
        templates_dir / template,
        templates_dir / f"{template}.yaml",
        templates_dir / f"{template}.yml",
    ]

    for candidate in candidates:
        if candidate.exists():
            typer.echo(candidate.read_text())
            return

    # List available templates
    available = sorted(p.stem for p in templates_dir.glob("*.yaml"))
    available += sorted(p.stem for p in templates_dir.glob("*.yml"))
    available_str = ", ".join(available) if available else "(none found)"

    raise typer.BadParameter(
        f"Template '{template}' not found.\n"
        f"  Available templates: {available_str}\n"
        f"  Templates directory: {templates_dir}"
    )


# ---------------------------------------------------------------------------
# T043: Scrape commands
# ---------------------------------------------------------------------------


@scrape_app.command(name="prices")
def scrape_prices(
    file: str = typer.Argument(help="Path to itinerary YAML file"),
    backend: Annotated[str, typer.Option("--backend", "-b", help="Flight search backend: auto, serpapi, fast-flights, playwright")] = "auto",
    json: JsonFlag = False,
    plain: PlainFlag = False,
    verbose: VerboseFlag = False,
    quiet: QuietFlag = False,
) -> None:
    """Search Google Flights prices for all segments."""
    _setup_logging(verbose, quiet)

    # Validate backend
    from rtw.scraper.google_flights import SearchBackend
    try:
        search_backend = SearchBackend(backend)
    except ValueError:
        valid = ", ".join(b.value for b in SearchBackend)
        _error_panel(f"Invalid backend '{backend}'. Choose from: {valid}")
        raise typer.Exit(code=2)

    if search_backend == SearchBackend.SERPAPI:
        from rtw.scraper.serpapi_flights import serpapi_available
        if not serpapi_available():
            _error_panel(
                "SERPAPI_API_KEY not set.\n\n"
                "1. Sign up at https://serpapi.com (free tier: 250 searches/mo)\n"
                "2. Set the key: export SERPAPI_API_KEY=your_key_here\n\n"
                "Or use --backend auto to try other backends."
            )
            raise typer.Exit(code=2)

    try:
        itinerary = _load_itinerary(file)
        from rtw.scraper.batch import search_with_fallback
        from rtw.scraper.cache import ScrapeCache
        import json as json_mod

        cache = ScrapeCache()
        results = search_with_fallback(itinerary, cache, backend=search_backend)

        if json:
            data = []
            for i, r in enumerate(results):
                seg = itinerary.segments[i]
                entry = {
                    "segment": i + 1,
                    "route": f"{seg.from_airport}-{seg.to_airport}",
                    "price": None,
                }
                if r is not None:
                    entry["price"] = {
                        "amount": r.price,
                        "currency": getattr(r, "currency", "USD"),
                    }
                data.append(entry)
            typer.echo(json_mod.dumps(data, indent=2))
        else:
            typer.echo("Price Search Results:")
            for i, r in enumerate(results):
                seg = itinerary.segments[i]
                route = f"{seg.from_airport}-{seg.to_airport}"
                if r is not None:
                    typer.echo(f"  {i + 1}. {route}: ${r.price:,.0f}")
                elif seg.is_surface:
                    typer.echo(f"  {i + 1}. {route}: SURFACE (no flight)")
                else:
                    typer.echo(f"  {i + 1}. {route}: no price found")

    except typer.Exit:
        raise
    except typer.BadParameter:
        raise
    except Exception as exc:
        from rtw.scraper.serpapi_flights import SerpAPIAuthError, SerpAPIQuotaError
        if isinstance(exc, SerpAPIAuthError):
            _error_panel(
                "SerpAPI authentication failed.\n\n"
                "Check your key at https://serpapi.com/manage-api-key\n"
                "Or use --backend auto to try other backends."
            )
            raise typer.Exit(code=2)
        if isinstance(exc, SerpAPIQuotaError):
            _error_panel(
                "SerpAPI monthly quota exceeded.\n\n"
                "Upgrade at https://serpapi.com/pricing\n"
                "or use --backend auto to fall back to other search methods."
            )
            raise typer.Exit(code=2)
        _error_panel(str(exc))
        raise typer.Exit(code=2)


@scrape_app.command(name="availability")
def scrape_availability(
    file: str = typer.Argument(help="Path to itinerary YAML file"),
    booking_class: Optional[str] = typer.Option(None, "--class", "-c", help="Override booking class (default: auto per carrier, AA=H, others=D)"),
    verbose: VerboseFlag = False,
    quiet: QuietFlag = False,
) -> None:
    """Check ExpertFlyer availability for all segments."""
    _setup_logging(verbose, quiet)
    try:
        itinerary = _load_itinerary(file)
        from rtw.scraper.batch import check_itinerary_availability

        results = check_itinerary_availability(itinerary, booking_class)

        typer.echo("Availability Results:")
        for i, r in enumerate(results):
            seg = itinerary.segments[i]
            route = f"{seg.from_airport}-{seg.to_airport}"
            if r is not None:
                if hasattr(r, "available"):
                    avail = "AVAILABLE" if r.available else "NOT AVAILABLE"
                    seats = getattr(r, "seats", "?")
                    display = getattr(r, "display_code", f"{seats} seats")
                    flights = getattr(r, "flight_count", 0)
                    extra = f" ({flights} flights)" if flights else ""
                    typer.echo(f"  {i + 1}. {route}: {avail} — {display}{extra}")
                else:
                    avail = "AVAILABLE" if r.get("available") else "NOT AVAILABLE"
                    seats = r.get("seats", "?")
                    typer.echo(f"  {i + 1}. {route}: {avail} ({seats} seats)")
            elif seg.is_surface:
                typer.echo(f"  {i + 1}. {route}: SURFACE (no flight)")
            else:
                typer.echo(f"  {i + 1}. {route}: not checked")

    except typer.Exit:
        raise
    except typer.BadParameter:
        raise
    except Exception as exc:
        _error_panel(str(exc))
        raise typer.Exit(code=2)


# ---------------------------------------------------------------------------
# T043: Config commands
# ---------------------------------------------------------------------------


@config_app.command(name="set-expertflyer")
def config_set_expertflyer(
    username: str = typer.Option(..., prompt=True, help="ExpertFlyer username"),
    password: str = typer.Option(..., prompt=True, hide_input=True, help="ExpertFlyer password"),
) -> None:
    """Store ExpertFlyer credentials in system keyring."""
    try:
        import keyring

        keyring.set_password("expertflyer.com", "username", username)
        keyring.set_password("expertflyer.com", "password", password)
        typer.echo("ExpertFlyer credentials saved to system keyring.")
    except ImportError:
        _error_panel("keyring library not available. Install with: pip install keyring")
        raise typer.Exit(code=1)
    except Exception as exc:
        _error_panel(f"Failed to save credentials: {exc}")
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# T043: Cache commands
# ---------------------------------------------------------------------------


@cache_app.command(name="clear")
def cache_clear() -> None:
    """Clear the scrape cache."""
    from rtw.scraper.cache import ScrapeCache

    cache = ScrapeCache()
    cache.clear()
    typer.echo("Scrape cache cleared.")


# ---------------------------------------------------------------------------
# Login commands
# ---------------------------------------------------------------------------


@login_app.command(name="expertflyer")
def login_expertflyer(
    verbose: VerboseFlag = False,
    quiet: QuietFlag = False,
) -> None:
    """Store ExpertFlyer credentials for D-class availability checks.

    Prompts for email and password, stores them in the system keyring,
    then tests the login by connecting to ExpertFlyer.
    """
    _setup_logging(verbose, quiet)

    try:
        import keyring
    except ImportError:
        _error_panel("keyring library not available. Install with: pip install keyring")
        raise typer.Exit(code=1)

    # Check existing credentials
    existing = keyring.get_password("expertflyer.com", "username")
    if existing and not quiet:
        typer.echo(f"Existing credentials found for: {existing}")
        if not typer.confirm("Replace with new credentials?"):
            typer.echo("Keeping existing credentials.")
            return

    # Prompt for credentials
    username = typer.prompt("ExpertFlyer email")
    password = typer.prompt("ExpertFlyer password", hide_input=True)

    keyring.set_password("expertflyer.com", "username", username)
    keyring.set_password("expertflyer.com", "password", password)
    typer.echo("Credentials saved to system keyring.")

    # Test login
    if not quiet:
        typer.echo("Testing login...")
    try:
        from rtw.scraper.expertflyer import ExpertFlyerScraper

        with ExpertFlyerScraper() as scraper:
            scraper._ensure_logged_in()
            typer.echo("Login test successful.")
    except Exception as exc:
        typer.echo(f"Warning: login test failed ({exc}). Credentials saved anyway.", err=True)


@login_app.command(name="status")
def login_status(
    json: JsonFlag = False,
) -> None:
    """Check ExpertFlyer credential status."""
    import json as json_mod

    has_creds = False
    username = None
    try:
        import keyring

        username = keyring.get_password("expertflyer.com", "username")
        password = keyring.get_password("expertflyer.com", "password")
        has_creds = bool(username and password)
    except ImportError:
        pass

    if json:
        data = {
            "has_credentials": has_creds,
            "username": username,
        }
        typer.echo(json_mod.dumps(data, indent=2))
        return

    if has_creds:
        typer.echo(f"ExpertFlyer credentials: configured ({username})")
    else:
        typer.echo("ExpertFlyer credentials: not configured")
        typer.echo("Run `rtw login expertflyer` to set up.")


@login_app.command(name="clear")
def login_clear() -> None:
    """Clear saved ExpertFlyer credentials."""
    try:
        import keyring

        keyring.delete_password("expertflyer.com", "username")
        keyring.delete_password("expertflyer.com", "password")
        typer.echo("ExpertFlyer credentials cleared from keyring.")
    except ImportError:
        _error_panel("keyring library not available.")
        raise typer.Exit(code=1)
    except Exception:
        typer.echo("No credentials to clear.")


# ---------------------------------------------------------------------------
# Verify command
# ---------------------------------------------------------------------------


def _scored_to_verify_option(
    scored: "ScoredCandidate", option_id: int
) -> "VerifyOption":
    """Convert a ScoredCandidate to a VerifyOption for D-class checking."""
    from rtw.verify.models import SegmentVerification, VerifyOption

    segments = []
    for i, seg in enumerate(scored.candidate.itinerary.segments):
        seg_type = "SURFACE" if seg.is_surface else "FLOWN"
        segments.append(
            SegmentVerification(
                index=i,
                segment_type=seg_type,
                origin=seg.from_airport,
                destination=seg.to_airport,
                carrier=seg.carrier,
                flight_number=seg.flight,
                target_date=seg.date,
            )
        )
    return VerifyOption(option_id=option_id, segments=segments)


def _display_verify_result(result: "VerifyResult", quiet: bool = False) -> None:
    """Display verification result in rich or plain format."""
    from rtw.verify.models import DClassStatus

    try:
        from rich.console import Console
        from rich.table import Table

        console = Console(stderr=True)
        table = Table(
            title=f"Option {result.option_id} — D-Class Verification",
            show_lines=False,
        )
        table.add_column("#", justify="right", style="dim")
        table.add_column("Route", style="bold")
        table.add_column("Carrier")
        table.add_column("Date")
        table.add_column("D-Class", justify="center")
        table.add_column("Seats", justify="center")

        for seg in result.segments:
            route = f"{seg.origin}→{seg.destination}"
            carrier = seg.carrier or "—"
            date_str = str(seg.target_date) if seg.target_date else "—"

            if seg.segment_type == "SURFACE":
                table.add_row(
                    str(seg.index + 1), route, "SURFACE", "—", "—", "—",
                    style="dim",
                )
                continue

            if seg.dclass is None:
                table.add_row(
                    str(seg.index + 1), route, carrier, date_str, "?", "?",
                )
                continue

            status = seg.dclass.status
            display = seg.dclass.display_code
            seats = str(seg.dclass.seats) if status in (
                DClassStatus.AVAILABLE, DClassStatus.NOT_AVAILABLE
            ) else "—"

            if status == DClassStatus.AVAILABLE:
                style = "green"
            elif status == DClassStatus.NOT_AVAILABLE:
                style = "red"
            elif status == DClassStatus.ERROR:
                style = "yellow"
            else:
                style = "dim"

            # TIGHT badge: ≤2 flights with D availability
            tight = ""
            if seg.dclass.flights and seg.dclass.available_count <= 2:
                tight = " [red bold]TIGHT[/red bold]"

            table.add_row(
                str(seg.index + 1), route, carrier, date_str,
                f"[{style}]{display}[/{style}]{tight}",
                f"[{style}]{seats}[/{style}]",
            )

            # Per-flight sub-rows: show available flights (D>0)
            if seg.dclass.flights and not quiet:
                avail = seg.dclass.available_flights
                for flt in avail:
                    flt_label = flt.flight_number or f"{flt.carrier or carrier}?"
                    flt_dep = flt.depart_time or ""
                    flt_aircraft = f" ({flt.aircraft})" if flt.aircraft else ""
                    stops_str = f" +{flt.stops}" if flt.stops else ""
                    table.add_row(
                        "",
                        f"  [dim]{flt_label}{stops_str}{flt_aircraft}[/dim]",
                        "",
                        f"  [dim]{flt_dep}[/dim]",
                        f"[green]D{flt.seats}[/green]",
                        "",
                    )
                # Show count of D0 flights
                d0_count = seg.dclass.flight_count - seg.dclass.available_count
                if d0_count > 0:
                    table.add_row(
                        "", f"  [dim]({d0_count} more at D0)[/dim]",
                        "", "", "", "",
                    )

            # Alternate date hint for unavailable segments
            if (
                status == DClassStatus.NOT_AVAILABLE
                and seg.dclass.best_alternate
            ):
                alt = seg.dclass.best_alternate
                table.add_row(
                    "", "", "", f"  [dim]Try {alt.date}[/dim]",
                    f"[cyan]D{alt.seats}[/cyan]",
                    f"[cyan]{alt.seats}[/cyan]",
                )

        console.print(table)

        # Connection-only callout
        conn_only = result.connection_only_segments
        if conn_only and not quiet:
            console.print("\n[yellow]Connection-only segments (no nonstop D-class):[/yellow]")
            for seg in conn_only:
                display = seg.dclass.display_code if seg.dclass else "?"
                console.print(
                    f"  #{seg.index + 1}  {seg.origin}→{seg.destination} on {seg.carrier}: "
                    f"{display} available via connections only."
                )
                console.print(
                    f"      [dim]Run: rtw check-nonstop {seg.origin} {seg.destination} {seg.carrier}[/dim]"
                )

        # Summary line
        if result.fully_bookable:
            console.print(
                f"[green bold]All {result.confirmed}/{result.total_flown} "
                f"flown segments have D-class availability.[/green bold]"
            )
        else:
            console.print(
                f"[yellow]{result.confirmed}/{result.total_flown} flown segments "
                f"confirmed ({result.percentage:.0f}%).[/yellow]"
            )

    except ImportError:
        # Plain text fallback
        typer.echo(f"Option {result.option_id} — D-Class Verification", err=True)
        for seg in result.segments:
            route = f"{seg.origin}-{seg.destination}"
            if seg.segment_type == "SURFACE":
                typer.echo(f"  {seg.index + 1}. {route}: SURFACE", err=True)
                continue
            if seg.dclass:
                tight = " TIGHT" if seg.dclass.flights and seg.dclass.available_count <= 2 else ""
                typer.echo(
                    f"  {seg.index + 1}. {route} {seg.carrier or '??'}: "
                    f"{seg.dclass.display_code} ({seg.dclass.seats} seats){tight}",
                    err=True,
                )
                # Per-flight sub-rows
                if seg.dclass.flights and not quiet:
                    for flt in seg.dclass.available_flights:
                        flt_label = flt.flight_number or f"{flt.carrier or seg.carrier or '??'}?"
                        flt_dep = flt.depart_time or ""
                        stops_str = f" +{flt.stops}" if flt.stops else ""
                        typer.echo(
                            f"       {flt_label}{stops_str} {flt_dep} D{flt.seats}",
                            err=True,
                        )
                    d0_count = seg.dclass.flight_count - seg.dclass.available_count
                    if d0_count > 0:
                        typer.echo(f"       ({d0_count} more at D0)", err=True)
                if (
                    seg.dclass.status == DClassStatus.NOT_AVAILABLE
                    and seg.dclass.best_alternate
                ):
                    alt = seg.dclass.best_alternate
                    typer.echo(
                        f"       Try {alt.date}: D{alt.seats}",
                        err=True,
                    )
            else:
                typer.echo(f"  {seg.index + 1}. {route}: not checked", err=True)

        pct = f"{result.percentage:.0f}%" if result.total_flown else "n/a"
        typer.echo(
            f"  Result: {result.confirmed}/{result.total_flown} confirmed ({pct})",
            err=True,
        )


def _display_verify_summary(results: list) -> None:
    """Show a summary panel after batch verify."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text

        console = Console(stderr=True)
        lines = Text()

        for vr in results:
            label = f"Option {vr.option_id}: {vr.confirmed}/{vr.total_flown} D-class"
            if vr.fully_bookable:
                lines.append(f"  {label} ", style="green bold")
                lines.append("(fully bookable)\n", style="green")
            elif vr.percentage >= 50:
                lines.append(f"  {label} ", style="yellow")
                lines.append(f"({vr.percentage:.0f}%)\n", style="yellow")
            else:
                lines.append(f"  {label} ", style="red")
                lines.append(f"({vr.percentage:.0f}%)\n", style="red")

        console.print(Panel(lines, title="D-Class Summary", border_style="blue"))

    except ImportError:
        typer.echo("--- D-Class Summary ---", err=True)
        for vr in results:
            status = "BOOKABLE" if vr.fully_bookable else f"{vr.percentage:.0f}%"
            typer.echo(
                f"  Option {vr.option_id}: {vr.confirmed}/{vr.total_flown} ({status})",
                err=True,
            )


@app.command()
def verify(
    option_ids: Annotated[
        Optional[list[int]], typer.Argument(help="Option IDs to verify (1-based). Omit for top 3.")
    ] = None,
    booking_class: Annotated[Optional[str], typer.Option("--class", "-c", help="Override booking class (default: auto per carrier, AA=H, others=D)")] = None,
    no_cache: Annotated[bool, typer.Option("--no-cache", help="Skip cache")] = False,
    json: JsonFlag = False,
    plain: PlainFlag = False,
    verbose: VerboseFlag = False,
    quiet: QuietFlag = False,
) -> None:
    """Verify D-class availability for saved search results.

    Uses ExpertFlyer to check booking class availability on each flown
    segment. Requires a prior `rtw search` and `rtw login expertflyer`.
    """
    _setup_logging(verbose, quiet)

    try:
        from rtw.verify.state import SearchState
        from rtw.scraper.expertflyer import ExpertFlyerScraper, _get_credentials
        from rtw.scraper.cache import ScrapeCache
        from rtw.verify.verifier import DClassVerifier
        import json as json_mod

        # Load last search result
        state = SearchState()
        search_result = state.load()
        if search_result is None:
            _error_panel(
                "No saved search results found.\n\n"
                "Run `rtw search` first, then `rtw verify`."
            )
            raise typer.Exit(code=1)

        age = state.state_age_minutes()
        if age and age > 60 and not quiet:
            typer.echo(
                f"Warning: search results are {age:.0f} minutes old. "
                "Consider re-running `rtw search`.",
                err=True,
            )

        # Determine which options to verify
        if option_ids is None:
            ids = list(range(1, min(4, len(search_result.options) + 1)))
        else:
            ids = option_ids

        # Validate IDs
        for oid in ids:
            if oid < 1 or oid > len(search_result.options):
                _error_panel(
                    f"Option {oid} does not exist. "
                    f"Available: 1-{len(search_result.options)}"
                )
                raise typer.Exit(code=2)

        # Check credentials
        if _get_credentials() is None:
            _error_panel(
                "No ExpertFlyer credentials found.\n\n"
                "Run `rtw login expertflyer` to set up."
            )
            raise typer.Exit(code=1)

        # Build verifier with context-managed scraper
        with ExpertFlyerScraper() as scraper:
            verifier = DClassVerifier(
                scraper=scraper,
                cache=ScrapeCache(),
                booking_class=booking_class,
            )
            # Note: booking_class=None means auto per-carrier (AA=H, others=D)

            # Convert and verify with Rich progress
            results = []
            use_rich_progress = not json and not quiet and not plain

            for oid in ids:
                scored = search_result.options[oid - 1]
                option = _scored_to_verify_option(scored, oid)
                route_label = (
                    f"{option.segments[0].origin}→...→{option.segments[-1].destination}"
                    if option.segments else "?"
                )

                if use_rich_progress:
                    try:
                        from rich.console import Console
                        from rich.status import Status

                        console = Console(stderr=True)
                        status = Status(
                            f"Option {oid}: checking {route_label}...",
                            console=console,
                            spinner="dots",
                        )
                        status.start()

                        def _progress(current, total, seg, _s=status, _oid=oid):
                            label = seg.dclass.display_code if seg.dclass else "..."
                            _s.update(
                                f"Option {_oid}: {seg.origin}→{seg.destination} "
                                f"[{current}/{total}] {label}"
                            )

                        vr = verifier.verify_option(
                            option, progress_cb=_progress, no_cache=no_cache
                        )
                        status.stop()
                    except ImportError:
                        # Fall back to plain echo
                        use_rich_progress = False
                        vr = verifier.verify_option(option, no_cache=no_cache)
                elif not quiet and not json:
                    typer.echo(f"Verifying option {oid} ({route_label})...", err=True)

                    def _progress(current, total, seg):
                        status = seg.dclass.display_code if seg.dclass else "..."
                        typer.echo(
                            f"  [{current}/{total}] {seg.origin}→{seg.destination}: {status}",
                            err=True,
                        )

                    vr = verifier.verify_option(
                        option, progress_cb=_progress, no_cache=no_cache
                    )
                else:
                    vr = verifier.verify_option(option, no_cache=no_cache)

                results.append(vr)

                if not json and not quiet:
                    _display_verify_result(vr)
                    typer.echo("", err=True)

            # Summary panel for batch verify
            if not json and not quiet and len(results) > 1:
                _display_verify_summary(results)

        if json:
            data = [r.model_dump(mode="json") for r in results]
            typer.echo(json_mod.dumps(data, indent=2))

    except typer.Exit:
        raise
    except Exception as exc:
        _error_panel(str(exc))
        raise typer.Exit(code=2)


# ---------------------------------------------------------------------------
# T049: Search command
# ---------------------------------------------------------------------------


@app.command()
def search(
    cities: Annotated[str, typer.Option("--cities", "-c", help="Comma-separated IATA codes to visit")] = "",
    date_from: Annotated[str, typer.Option("--from", "-f", help="Start date (YYYY-MM-DD)")] = "",
    date_to: Annotated[str, typer.Option("--to", "-t", help="End date (YYYY-MM-DD)")] = "",
    origin: Annotated[str, typer.Option("--origin", "-o", help="Origin airport IATA code")] = "",
    cabin: Annotated[str, typer.Option("--cabin", help="Cabin class")] = "business",
    ticket_type: Annotated[str, typer.Option("--type", help="Ticket type")] = "DONE4",
    top_n: Annotated[int, typer.Option("--top", "-n", help="Max results")] = 10,
    rank_by: Annotated[str, typer.Option("--rank-by", help="Ranking strategy")] = "availability",
    skip_availability: Annotated[bool, typer.Option("--skip-availability", help="Skip availability check")] = False,
    nonstop: Annotated[bool, typer.Option("--nonstop", help="Show only nonstop flights")] = False,
    backend: Annotated[str, typer.Option("--backend", "-b", help="Flight search backend: auto, serpapi, fast-flights, playwright")] = "auto",
    verify_dclass: Annotated[bool, typer.Option("--verify-dclass", help="Auto-verify D-class on top results via ExpertFlyer")] = False,
    export: Annotated[int, typer.Option("--export", "-e", help="Export option N as YAML")] = 0,
    json: JsonFlag = False,
    plain: PlainFlag = False,
    verbose: VerboseFlag = False,
    quiet: QuietFlag = False,
) -> None:
    """Search for valid RTW itinerary options."""
    _setup_logging(verbose, quiet)

    # Validate required inputs
    if not cities:
        _error_panel("Missing --cities. Example: --cities LHR,NRT,SYD,JFK")
        raise typer.Exit(code=2)
    if not date_from or not date_to:
        _error_panel("Missing --from and/or --to dates. Example: --from 2025-09-01 --to 2025-11-15")
        raise typer.Exit(code=2)
    if not origin:
        _error_panel("Missing --origin. Example: --origin CAI")
        raise typer.Exit(code=2)

    # Validate backend
    from rtw.scraper.google_flights import SearchBackend
    try:
        search_backend = SearchBackend(backend)
    except ValueError:
        valid = ", ".join(b.value for b in SearchBackend)
        _error_panel(f"Invalid backend '{backend}'. Choose from: {valid}")
        raise typer.Exit(code=2)

    if search_backend == SearchBackend.SERPAPI:
        from rtw.scraper.serpapi_flights import serpapi_available
        if not serpapi_available():
            _error_panel(
                "SERPAPI_API_KEY not set.\n\n"
                "1. Sign up at https://serpapi.com (free tier: 250 searches/mo)\n"
                "2. Set the key: export SERPAPI_API_KEY=your_key_here\n\n"
                "Or use --backend auto to try other backends."
            )
            raise typer.Exit(code=2)

    try:
        from datetime import date as Date

        from rtw.search.query import parse_search_query
        from rtw.search.generator import generate_candidates
        from rtw.search.scorer import score_candidates, rank_candidates
        from rtw.search.models import ScoredCandidate, SearchResult
        from rtw.output.search_formatter import (
            format_search_skeletons_rich,
            format_search_skeletons_plain,
            format_search_results_rich,
            format_search_results_plain,
            format_search_json,
        )

        city_list = [c.strip() for c in cities.split(",") if c.strip()]
        df = Date.fromisoformat(date_from)
        dt = Date.fromisoformat(date_to)

        # Phase 1: Parse and validate
        query = parse_search_query(
            cities=city_list,
            origin=origin,
            date_from=df,
            date_to=dt,
            cabin=cabin,
            ticket_type=ticket_type,
            top_n=top_n,
            rank_by=rank_by,
        )

        # Phase 2: Generate candidates (with optional nonstop pre-filter)
        ns_filter = None
        if nonstop:
            from rtw.nonstop.checker import NonstopChecker
            from rtw.scraper.serpapi_flights import serpapi_available

            if serpapi_available():
                ns_checker = NonstopChecker(cache=ScrapeCache())
                ns_date = df  # Use search start date for nonstop check
                ns_cache: dict[tuple[str, str, str], bool] = {}

                def _nonstop_filter(o: str, d: str, c: str) -> bool:
                    key = (o.upper(), d.upper(), c.upper())
                    if key not in ns_cache:
                        result = ns_checker.check(o, d, c, ns_date)
                        ns_cache[key] = result.has_nonstop
                    return ns_cache[key]

                ns_filter = _nonstop_filter
                if not quiet:
                    typer.echo("Nonstop pre-filter active (--nonstop).", err=True)
            else:
                if not quiet:
                    typer.echo(
                        "Warning: --nonstop used but SERPAPI_API_KEY not set. "
                        "Skipping nonstop pre-filter.",
                        err=True,
                    )

        candidates = generate_candidates(query, nonstop_filter=ns_filter)
        if not candidates:
            if not quiet:
                msg = "No valid itinerary options found."
                if nonstop and ns_filter:
                    msg += (
                        "\n\nThe --nonstop filter may have eliminated all candidates.\n"
                        "Try without --nonstop, or run `rtw check-nonstop` to verify routes."
                    )
                else:
                    msg += " Try different cities or ticket type."
                _error_panel(msg)
            raise typer.Exit(code=1)

        # Phase 3: Score and rank (initial)
        scored = [ScoredCandidate(candidate=c) for c in candidates]
        scored = score_candidates(scored, rank_by=rank_by)
        ranked = rank_candidates(scored, top_n=top_n)

        total_generated = len(candidates)

        # Base fare lookup (for skeleton display and later comparison)
        from rtw.cost import CostEstimator
        base_fare_usd = CostEstimator().get_base_fare(query.origin, query.ticket_type)

        # Phase 4: Display skeletons (unless JSON or export-only)
        if not json and export == 0 and not quiet:
            result = SearchResult(
                query=query,
                candidates_generated=total_generated,
                options=ranked,
                base_fare_usd=base_fare_usd,
            )
            fmt = _get_format(False, plain)
            if fmt == "rich":
                typer.echo(format_search_skeletons_rich(result))
            else:
                typer.echo(format_search_skeletons_plain(result))

        # Phase 5: Availability check (top 3 unless skipped)
        if not skip_availability:
            from rtw.scraper.cache import ScrapeCache
            from rtw.search.availability import AvailabilityChecker

            max_stops = 0 if nonstop else None
            checker = AvailabilityChecker(
                cache=ScrapeCache(), cabin=cabin, max_stops=max_stops, backend=search_backend,
            )
            check_count = min(3, len(ranked))

            if not quiet and not json:
                typer.echo(f"Checking availability for top {check_count} options...", err=True)

            for i in range(check_count):
                def _progress(idx, total, seg_info, result):
                    if verbose and not quiet:
                        status = result.status.value if result else "?"
                        typer.echo(
                            f"  [{idx + 1}/{total}] {seg_info['from']}-{seg_info['to']}: {status}",
                            err=True,
                        )

                checker.check_candidate(ranked[i], query, progress_cb=_progress if verbose else None)

            # Re-score with availability data
            ranked = score_candidates(ranked, rank_by=rank_by)
            ranked = rank_candidates(ranked, top_n=top_n)

        # Compute fare comparison for all ranked options
        from rtw.search.fare_comparison import compute_fare_comparison
        for opt in ranked:
            opt.fare_comparison = compute_fare_comparison(opt, query)

        # Phase 6: Final output
        result = SearchResult(
            query=query,
            candidates_generated=total_generated,
            options=ranked,
            base_fare_usd=base_fare_usd,
        )

        # Save search state for `rtw verify`
        from rtw.verify.state import SearchState
        SearchState().save(result)

        # Phase 6.5: Optional D-class verification
        if verify_dclass:
            from rtw.scraper.expertflyer import ExpertFlyerScraper, _get_credentials

            if _get_credentials() is None:
                if not quiet:
                    typer.echo(
                        "Skipping D-class verification: no ExpertFlyer credentials. "
                        "Run `rtw login expertflyer` first.",
                        err=True,
                    )
            else:
                from rtw.verify.verifier import DClassVerifier

                verify_count = min(3, len(ranked))
                if not quiet and not json:
                    typer.echo(
                        f"\nVerifying D-class for top {verify_count} options...",
                        err=True,
                    )
                with ExpertFlyerScraper() as ef_scraper:
                    dclass_verifier = DClassVerifier(
                        scraper=ef_scraper,
                        cache=ScrapeCache(),
                    )
                    for i in range(verify_count):
                        option = _scored_to_verify_option(ranked[i], i + 1)
                        vr = dclass_verifier.verify_option(option)
                        if not quiet and not json:
                            _display_verify_result(vr, quiet=quiet)

        if json:
            typer.echo(format_search_json(result))
        elif export > 0:
            if export > len(ranked):
                _error_panel(f"Option {export} does not exist. Only {len(ranked)} options available.")
                raise typer.Exit(code=2)
            from rtw.search.exporter import export_itinerary
            yaml_str = export_itinerary(ranked[export - 1], query)
            typer.echo(yaml_str)
        else:
            fmt = _get_format(False, plain)
            if fmt == "rich":
                typer.echo(format_search_results_rich(result))
            else:
                typer.echo(format_search_results_plain(result))

    except ValueError as exc:
        _error_panel(str(exc))
        raise typer.Exit(code=2)
    except typer.Exit:
        raise
    except Exception as exc:
        from rtw.scraper.serpapi_flights import SerpAPIAuthError, SerpAPIQuotaError
        if isinstance(exc, SerpAPIAuthError):
            _error_panel(
                "SerpAPI authentication failed.\n\n"
                "Check your key at https://serpapi.com/manage-api-key\n"
                "Or use --backend auto to try other backends."
            )
            raise typer.Exit(code=2)
        if isinstance(exc, SerpAPIQuotaError):
            _error_panel(
                "SerpAPI monthly quota exceeded.\n\n"
                "Upgrade at https://serpapi.com/pricing\n"
                "or use --backend auto to fall back to other search methods."
            )
            raise typer.Exit(code=2)
        _error_panel(str(exc))
        raise typer.Exit(code=2)


# ---------------------------------------------------------------------------
# Nonstop check command
# ---------------------------------------------------------------------------


def _parse_route_string(route: str) -> list[tuple[str, str, str]]:
    """Parse route format: 'LHR-HEL:AY,HEL-NRT:AY,NRT-SYD:QF'."""
    import re

    segments = []
    for part in route.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"([A-Za-z]{3})-([A-Za-z]{3}):([A-Za-z]{2})", part)
        if not m:
            raise typer.BadParameter(
                f"Invalid route segment: '{part}'\n"
                "  Expected format: LHR-HEL:AY (ORIGIN-DEST:CARRIER)"
            )
        segments.append((m.group(1).upper(), m.group(2).upper(), m.group(3).upper()))
    if not segments:
        raise typer.BadParameter("Empty route string.")
    return segments


def _parse_pairs_file(path: Path) -> list[tuple[str, str, str]]:
    """Parse file with 'ORIGIN DEST CARRIER' per line."""
    if not path.exists():
        raise typer.BadParameter(f"File not found: {path}")
    segments = []
    for line_num, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 3:
            raise typer.BadParameter(
                f"Line {line_num}: expected 'ORIGIN DEST CARRIER', got: {line}"
            )
        segments.append((parts[0].upper(), parts[1].upper(), parts[2].upper()))
    if not segments:
        raise typer.BadParameter(f"No segments found in {path}")
    return segments


@app.command(name="check-nonstop")
def check_nonstop(
    origin: Annotated[Optional[str], typer.Argument(help="Origin airport (3-letter IATA)")] = None,
    dest: Annotated[Optional[str], typer.Argument(help="Destination airport (3-letter IATA)")] = None,
    carrier: Annotated[Optional[str], typer.Argument(help="Carrier (2-letter IATA)")] = None,
    route: Annotated[Optional[str], typer.Option("--route", "-r", help="Batch route: 'LHR-HEL:AY,HEL-DOH:QR'")] = None,
    file: Annotated[Optional[str], typer.Option("--file", "-f", help="File with 'ORIGIN DEST CARRIER' per line")] = None,
    date: Annotated[Optional[str], typer.Option("--date", "-d", help="Check date (ISO format, default: 30 days from now)")] = None,
    json: JsonFlag = False,
    plain: PlainFlag = False,
    verbose: VerboseFlag = False,
    quiet: QuietFlag = False,
) -> None:
    """Check nonstop flight service for a route or batch of routes.

    Single:  rtw check-nonstop LHR HEL AY
    Batch:   rtw check-nonstop --route "LHR-HEL:AY,HEL-DOH:QR"
    File:    rtw check-nonstop --file pairs.txt
    """
    import datetime
    import json as json_mod

    from rtw.nonstop.checker import NonstopChecker
    from rtw.scraper.cache import ScrapeCache
    from rtw.scraper.serpapi_flights import serpapi_available

    _setup_logging(verbose, quiet)
    fmt = _get_format(json, plain)

    # Check SERPAPI_API_KEY
    if not serpapi_available():
        _error_panel(
            "SERPAPI_API_KEY not set.\n\n"
            "Get a key at https://serpapi.com/ and set:\n"
            "  export SERPAPI_API_KEY='your-key-here'"
        )
        raise typer.Exit(code=2)

    # Parse date
    if date:
        try:
            check_date = datetime.date.fromisoformat(date)
        except ValueError:
            _error_panel(f"Invalid date format: {date}\n  Expected: YYYY-MM-DD")
            raise typer.Exit(code=2)
    else:
        check_date = datetime.date.today() + datetime.timedelta(days=30)

    # Determine mode: route string > file > single
    if route:
        segments = _parse_route_string(route)
    elif file:
        segments = _parse_pairs_file(Path(file))
    elif origin and dest and carrier:
        segments = [(origin.upper(), dest.upper(), carrier.upper())]
    else:
        _error_panel(
            "Provide either:\n"
            "  rtw check-nonstop LHR HEL AY\n"
            "  rtw check-nonstop --route 'LHR-HEL:AY,HEL-DOH:QR'\n"
            "  rtw check-nonstop --file pairs.txt"
        )
        raise typer.Exit(code=2)

    # Validate codes
    for o, d, c in segments:
        if len(o) != 3:
            suggestion = _fuzzy_airport_suggestion(o)
            _error_panel(f"Invalid airport code: {o}{suggestion}")
            raise typer.Exit(code=2)
        if len(d) != 3:
            suggestion = _fuzzy_airport_suggestion(d)
            _error_panel(f"Invalid airport code: {d}{suggestion}")
            raise typer.Exit(code=2)
        if len(c) != 2:
            _error_panel(f"Invalid carrier code: {c}\n  Expected 2-letter IATA code.")
            raise typer.Exit(code=2)

    checker = NonstopChecker(cache=ScrapeCache())
    is_batch = len(segments) > 1

    if is_batch:
        _run_batch_nonstop(checker, segments, check_date, fmt, verbose, quiet, json_mod)
    else:
        _run_single_nonstop(checker, segments[0], check_date, fmt, verbose, quiet, json_mod)


def _run_single_nonstop(checker, segment, check_date, fmt, verbose, quiet, json_mod):
    """Run single nonstop check and display result."""
    origin, dest, carrier = segment
    result = checker.check_with_alternatives(origin, dest, carrier, check_date)

    if fmt == "json":
        typer.echo(json_mod.dumps(result.model_dump(mode="json"), indent=2))
        raise typer.Exit(code=0 if result.has_nonstop else 1)

    if result.error:
        _error_panel(f"Check failed: {result.error}")
        raise typer.Exit(code=2)

    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()

        if result.has_nonstop:
            console.print(
                f"\n[bold green]NONSTOP AVAILABLE[/] "
                f"[cyan]{origin}[/]-[cyan]{dest}[/] on [bold]{carrier}[/] ({result.carrier_name})"
            )
            console.print(
                f"  {result.nonstop_flight_count} nonstop flight{'s' if result.nonstop_flight_count != 1 else ''}"
                + (f" | ${result.price_range_usd[0]:.0f}-${result.price_range_usd[1]:.0f}" if result.price_range_usd else "")
            )
        else:
            console.print(
                f"\n[bold red]NO NONSTOP SERVICE[/] "
                f"[cyan]{origin}[/]-[cyan]{dest}[/] on [bold]{carrier}[/] ({result.carrier_name})"
            )

        # Alternatives table (only nonstop carriers per UX Q1)
        nonstop_alts = result.nonstop_alternatives
        if nonstop_alts:
            table = Table(title="Oneworld Nonstop Alternatives", show_lines=False)
            table.add_column("Carrier", style="bold")
            table.add_column("Nonstops", justify="right")
            table.add_column("Price Range", justify="right")
            for alt in nonstop_alts:
                price_str = (
                    f"${alt.price_range_usd[0]:.0f}-${alt.price_range_usd[1]:.0f}"
                    if alt.price_range_usd else "-"
                )
                table.add_row(
                    f"{alt.carrier} {alt.carrier_name}",
                    str(alt.nonstop_flight_count),
                    price_str,
                )
            console.print(table)
        elif not result.has_nonstop:
            console.print("[dim]No oneworld carriers have nonstop service on this route.[/]")

        if verbose and result.from_cache:
            console.print("[dim]Result from cache[/]")

    except ImportError:
        # Plain fallback
        status = "NONSTOP" if result.has_nonstop else "NO NONSTOP"
        typer.echo(f"{status} {origin}-{dest} {carrier} ({result.carrier_name})")

    raise typer.Exit(code=0 if result.has_nonstop else 1)


def _run_batch_nonstop(checker, segments, check_date, fmt, verbose, quiet, json_mod):
    """Run batch nonstop check and display results."""
    # Progress callback
    progress_lines = []

    def progress_cb(current, total, label):
        if not quiet:
            typer.echo(f"  [{current}/{total}] {label}", err=True)

    result = checker.check_batch(segments, check_date, progress_cb=progress_cb)

    if fmt == "json":
        typer.echo(json_mod.dumps(result.model_dump(mode="json"), indent=2))
        raise typer.Exit(code=0 if result.all_clear else 1)

    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()

        table = Table(title=f"Nonstop Check — {check_date.isoformat()}", show_lines=False)
        table.add_column("#", justify="right", style="dim")
        table.add_column("Route", style="cyan")
        table.add_column("Carrier", style="bold")
        table.add_column("Status")
        table.add_column("Flights", justify="right")
        table.add_column("Alternatives")

        for seg in result.segments:
            r = seg.result
            if r is None:
                table.add_row(str(seg.index + 1), f"{seg.origin}-{seg.destination}", seg.carrier, "[yellow]ERROR[/]", "-", "-")
                continue

            if r.error:
                status = "[yellow]ERROR[/]"
            elif r.has_nonstop:
                status = "[green]NONSTOP[/]"
            else:
                status = "[red]NO NONSTOP[/]"

            alt_str = ", ".join(a.carrier for a in r.nonstop_alternatives) if r.nonstop_alternatives else "-"

            table.add_row(
                str(seg.index + 1),
                f"{seg.origin}-{seg.destination}",
                f"{seg.carrier} {r.carrier_name}",
                status,
                str(r.nonstop_flight_count) if not r.error else "-",
                alt_str,
            )

        console.print(table)

        # Summary
        if result.all_clear:
            console.print(f"\n[bold green]{result.nonstop_count}/{result.total} ALL CLEAR[/] — all segments have nonstop service")
        else:
            parts = []
            if result.nonstop_count:
                parts.append(f"[green]{result.nonstop_count} nonstop[/]")
            if result.no_nonstop_count:
                parts.append(f"[red]{result.no_nonstop_count} no nonstop[/]")
            if result.error_count:
                parts.append(f"[yellow]{result.error_count} error[/]")
            console.print(f"\n{result.total} segments: {', '.join(parts)}")

        if verbose:
            console.print(f"[dim]API calls used: {result.api_calls_used}[/]")

    except ImportError:
        # Plain fallback
        for seg in result.segments:
            r = seg.result
            if r and r.has_nonstop:
                typer.echo(f"NONSTOP {seg.origin}-{seg.destination} {seg.carrier}")
            elif r and r.error:
                typer.echo(f"ERROR   {seg.origin}-{seg.destination} {seg.carrier}: {r.error}")
            else:
                typer.echo(f"NONE    {seg.origin}-{seg.destination} {seg.carrier}")
        status_str = "ALL CLEAR" if result.all_clear else "INCOMPLETE"
        typer.echo(f"\n{status_str}: {result.nonstop_count}/{result.total} nonstop")

    raise typer.Exit(code=0 if result.all_clear else 1)


# ---------------------------------------------------------------------------
# Build command — route string to YAML
# ---------------------------------------------------------------------------


@app.command(name="build")
def build(
    route: Annotated[str, typer.Option("--route", "-r", help="Route: 'LAX-HND:JL,HND-SYD:JL,SYD-DOH:QR,DOH-LAX:QR'")] = "",
    origin: Annotated[Optional[str], typer.Option("--origin", "-o", help="Origin airport (3-letter IATA)")] = None,
    ticket_type: Annotated[str, typer.Option("--type", "-t", help="Ticket type (DONE4, LONE3, etc.)")] = "DONE4",
    cabin: Annotated[str, typer.Option("--cabin", "-c", help="Cabin class")] = "business",
    departure: Annotated[Optional[str], typer.Option("--departure", "-d", help="Departure date (ISO format)")] = None,
    gap: Annotated[int, typer.Option("--gap", "-g", help="Days between stopovers")] = 4,
    out: Annotated[Optional[str], typer.Option("--out", help="Write YAML to file")] = None,
    validate: Annotated[bool, typer.Option("--validate", help="Run validation after building")] = False,
    ntp: Annotated[bool, typer.Option("--ntp", help="Calculate NTP after building")] = False,
    plain: PlainFlag = False,
) -> None:
    """Build a YAML itinerary from a route string.

    Example:
      rtw build --route "LAX-HND:JL,HND-SYD:JL,SYD-DOH:QR,DOH-LAX:QR" \\
                --origin LAX --type DONE4 --departure 2026-04-01 --validate --ntp
    """
    import datetime

    from rtw.models import CabinClass, Itinerary, Segment, SegmentType, Ticket, TicketType

    if not route:
        _error_panel("--route is required.\n  Example: --route 'LAX-HND:JL,HND-SYD:JL'")
        raise typer.Exit(code=2)

    # Parse segments
    try:
        parsed = _parse_route_string(route)
    except typer.BadParameter as exc:
        _error_panel(str(exc))
        raise typer.Exit(code=2)

    # Infer origin from first segment if not provided
    if not origin:
        origin = parsed[0][0]

    origin = origin.upper()

    # Parse ticket type
    try:
        tt = TicketType(ticket_type.upper())
    except ValueError:
        valid = ", ".join(t.value for t in TicketType)
        _error_panel(f"Invalid ticket type: {ticket_type}\n  Valid: {valid}")
        raise typer.Exit(code=2)

    # Parse cabin
    try:
        cab = CabinClass(cabin.lower())
    except ValueError:
        valid = ", ".join(c.value for c in CabinClass)
        _error_panel(f"Invalid cabin: {cabin}\n  Valid: {valid}")
        raise typer.Exit(code=2)

    # Parse departure date
    if departure:
        try:
            dep_date = datetime.date.fromisoformat(departure)
        except ValueError:
            _error_panel(f"Invalid date: {departure}\n  Expected: YYYY-MM-DD")
            raise typer.Exit(code=2)
    else:
        dep_date = datetime.date.today() + datetime.timedelta(days=60)

    # Build segments with dates
    segments = []
    current_date = dep_date
    for i, (from_apt, to_apt, carrier_code) in enumerate(parsed):
        is_last = i == len(parsed) - 1
        seg_type = SegmentType.FINAL if is_last else SegmentType.STOPOVER

        segments.append(
            Segment(
                **{
                    "from": from_apt,
                    "to": to_apt,
                    "carrier": carrier_code,
                    "date": current_date,
                    "type": seg_type,
                }
            )
        )

        if not is_last:
            current_date = current_date + datetime.timedelta(days=gap)

    # Build itinerary
    ticket = Ticket(
        type=tt,
        cabin=cab,
        origin=origin,
        passengers=1,
        departure=dep_date,
        plating_carrier="AA",
    )
    itinerary = Itinerary(ticket=ticket, segments=segments)

    # Serialize to YAML
    segments_data = []
    for seg in itinerary.segments:
        entry: dict = {
            "from": seg.from_airport,
            "to": seg.to_airport,
            "carrier": seg.carrier,
            "type": seg.type.value,
        }
        if seg.date:
            entry["date"] = seg.date.isoformat()
        segments_data.append(entry)

    yaml_data = {
        "ticket": {
            "type": itinerary.ticket.type.value,
            "cabin": itinerary.ticket.cabin.value,
            "origin": itinerary.ticket.origin,
            "passengers": itinerary.ticket.passengers,
            "departure": dep_date.isoformat(),
            "plating_carrier": "AA",
        },
        "segments": segments_data,
    }

    yaml_str = yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)

    # Output
    if out:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(yaml_str)
        typer.echo(f"Written to {out_path}")
    else:
        typer.echo(yaml_str)

    # Optional validation
    if validate:
        from rtw.validator import Validator

        validator = Validator()
        report = validator.validate(itinerary)
        total_rules = len(report.results)
        violations = report.violations
        if report.passed:
            typer.echo(f"Validation: PASS ({total_rules} rules checked, 0 violations)")
        else:
            typer.echo(f"Validation: FAIL ({len(violations)} violations)")
            for v in violations:
                typer.echo(f"  - {v.message}")
            raise typer.Exit(code=1)

    # Optional NTP
    if ntp:
        from rtw.ntp import NTPCalculator

        calc = NTPCalculator()
        estimates = calc.calculate(itinerary)
        total_ntp = sum(e.estimated_ntp for e in estimates)
        total_dist = sum(e.distance_miles for e in estimates)
        typer.echo(f"NTP: {total_ntp:,.0f} from {total_dist:,.0f} miles ({len(estimates)} segments)")
        for e in estimates:
            rate_str = f"{e.rate:.0f}%" if e.rate else "rev"
            typer.echo(f"  {e.route:10s} {e.carrier:3s} {e.distance_miles:>6,.0f} mi  {rate_str:>5s}  {e.estimated_ntp:>6,.0f} NTP")


# ---------------------------------------------------------------------------
# Scan dates command — D-class date scanner
# ---------------------------------------------------------------------------


@app.command(name="scan-dates")
def scan_dates(
    origin: Annotated[str, typer.Argument(help="Origin airport (3-letter IATA)")],
    dest: Annotated[str, typer.Argument(help="Destination airport (3-letter IATA)")],
    carrier: Annotated[str, typer.Argument(help="Carrier (2-letter IATA)")],
    date_from: Annotated[str, typer.Option("--from", help="Start date (ISO format)")] = "",
    date_to: Annotated[str, typer.Option("--to", help="End date (ISO format)")] = "",
    booking_class: Annotated[str, typer.Option("--class", "-c", help="Booking class")] = "D",
    nonstop_only: Annotated[bool, typer.Option("--nonstop-only", help="Only show dates with nonstop D-class")] = False,
    dow: Annotated[Optional[str], typer.Option("--dow", help="Days of week filter: mon,wed,thu")] = None,
    plain: PlainFlag = False,
    verbose: VerboseFlag = False,
    quiet: QuietFlag = False,
) -> None:
    """Scan a date range for D-class availability on one route.

    Example:
      rtw scan-dates HEL LAX AY --from 2026-04-01 --to 2026-04-30
      rtw scan-dates HEL LAX AY --from 2026-04-01 --to 2026-04-30 --nonstop-only --dow mon,wed,thu
    """
    import datetime

    _setup_logging(verbose, quiet)

    # Parse dates
    if not date_from:
        start = datetime.date.today() + datetime.timedelta(days=30)
    else:
        try:
            start = datetime.date.fromisoformat(date_from)
        except ValueError:
            _error_panel(f"Invalid --from date: {date_from}\n  Expected: YYYY-MM-DD")
            raise typer.Exit(code=2)

    if not date_to:
        end = start + datetime.timedelta(days=30)
    else:
        try:
            end = datetime.date.fromisoformat(date_to)
        except ValueError:
            _error_panel(f"Invalid --to date: {date_to}\n  Expected: YYYY-MM-DD")
            raise typer.Exit(code=2)

    if end < start:
        _error_panel("--to must not be before --from")
        raise typer.Exit(code=2)

    # Parse day-of-week filter
    dow_filter: Optional[set[int]] = None
    if dow:
        day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
        dow_filter = set()
        for d in dow.lower().split(","):
            d = d.strip()
            if d not in day_map:
                _error_panel(f"Invalid day: {d}\n  Valid: mon,tue,wed,thu,fri,sat,sun")
                raise typer.Exit(code=2)
            dow_filter.add(day_map[d])

    origin = origin.upper()
    dest = dest.upper()
    carrier = carrier.upper()

    # Check ExpertFlyer credentials
    from rtw.scraper.expertflyer import ExpertFlyerScraper

    scraper = ExpertFlyerScraper()

    # Build date list
    dates = []
    current = start
    while current <= end:
        if dow_filter is None or current.weekday() in dow_filter:
            dates.append(current)
        current += datetime.timedelta(days=1)

    if not dates:
        _error_panel("No dates match the given range and day-of-week filter.")
        raise typer.Exit(code=2)

    typer.echo(f"Scanning {origin}-{dest} {carrier} {booking_class}-class: {len(dates)} dates ({start} to {end})")

    # Scan each date
    results = []
    best_ns_date = None
    best_ns_seats = 0
    nonstop_dates = 0

    for d in dates:
        try:
            result = scraper.check_availability(origin, dest, d, carrier=carrier, booking_class=booking_class)
            if result is None:
                _error_panel("ExpertFlyer login failed. Run: python3 -m rtw login expertflyer")
                raise typer.Exit(code=2)

            ns_flights = result.nonstop_flights or []
            ns_seats = max((f.seats for f in ns_flights), default=0) if ns_flights else 0
            total_seats = result.seats
            ns_count = len(ns_flights)
            conn_count = result.available_count - ns_count

            if ns_seats > 0:
                nonstop_dates += 1
                if ns_seats > best_ns_seats:
                    best_ns_seats = ns_seats
                    best_ns_date = d

            if nonstop_only and ns_seats == 0:
                continue

            # Find best nonstop flight number
            best_fn = "-"
            if ns_flights:
                best_f = max(ns_flights, key=lambda f: f.seats)
                best_fn = best_f.flight_number or f"{carrier}?"

            results.append((d, total_seats, ns_seats, ns_count, conn_count, best_fn))

        except typer.Exit:
            raise
        except Exception as exc:
            if "login" in str(exc).lower() or "session" in str(exc).lower():
                _error_panel(f"ExpertFlyer session error: {exc}")
                raise typer.Exit(code=2)
            results.append((d, -1, 0, 0, 0, f"ERR"))

    scraper.close()

    # Display results
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title=f"{origin}-{dest} {carrier} {booking_class}-class Date Scan")
        table.add_column("Date", style="cyan")
        table.add_column("Day", style="dim")
        table.add_column(f"{booking_class} Total", justify="right")
        table.add_column("Nonstop", justify="right")
        table.add_column("Conn", justify="right", style="dim")
        table.add_column("Best Flight")

        for d, total, ns, ns_cnt, conn, fn in results:
            if total < 0:
                table.add_row(d.isoformat(), d.strftime("%a"), "[red]ERR[/]", "-", "-", fn)
            elif ns > 0:
                table.add_row(
                    d.isoformat(), d.strftime("%a"),
                    f"{booking_class}{total}", f"[bold green]{booking_class}{ns}[/] ({ns_cnt})",
                    str(conn), f"[green]{fn}[/]",
                )
            else:
                table.add_row(
                    d.isoformat(), d.strftime("%a"),
                    f"{booking_class}{total}", f"[dim]{booking_class}0[/]",
                    str(conn), "[dim]-[/]",
                )

        console.print(table)

    except ImportError:
        for d, total, ns, ns_cnt, conn, fn in results:
            marker = "NONSTOP" if ns > 0 else "conn" if total > 0 else "ERR" if total < 0 else "none"
            typer.echo(f"  {d} ({d.strftime('%a')})  {booking_class}{total}  ns={ns}  {marker}  {fn}")

    # Summary
    total_checked = len(dates)
    if nonstop_dates > 0:
        typer.echo(f"\n{nonstop_dates}/{total_checked} dates have nonstop {booking_class}-class. Best: {best_ns_date} {booking_class}{best_ns_seats}")
    else:
        typer.echo(f"\n0/{total_checked} dates have nonstop {booking_class}-class.")


# ---------------------------------------------------------------------------
# KB commands
# ---------------------------------------------------------------------------


def _kb_error(message: str) -> None:
    """Print a KB error and exit."""
    _error_panel(message)
    raise typer.Exit(code=1)


def _open_kb(db_path: Optional[str] = None):
    """Open the KnowledgeBase, handling missing DB gracefully."""
    from rtw.kb import KnowledgeBase, KnowledgeBaseError

    path = Path(db_path) if db_path else None
    try:
        return KnowledgeBase(db_path=path)
    except KnowledgeBaseError as exc:
        _kb_error(str(exc))


def _score_bar(score: float, width: int = 10) -> str:
    """Render a score as a text bar for plain output."""
    filled = int(round(score * width / 10))
    return "#" * filled + "-" * (width - filled)


def _display_kb_results(
    results: list,
    fmt: str,
    *,
    verbose: bool = False,
    query: str = "",
) -> None:
    """Display SearchResult list in rich/plain/json format."""
    import json as json_mod

    if fmt == "json":
        output = {
            "query": query,
            "result_count": len(results),
            "results": [r.to_dict() for r in results],
        }
        typer.echo(json_mod.dumps(output, indent=2))
        return

    if not results:
        typer.echo("  No results found.")
        return

    if fmt == "rich":
        try:
            from rich.console import Console
            from rich.table import Table

            console = Console()
            table = Table(
                title=f"KB Results ({len(results)} found)",
                show_lines=False,
            )
            table.add_column("#", justify="right", style="dim", width=3)
            table.add_column("Score", justify="right", width=5)
            table.add_column("Source", style="cyan", max_width=30)
            table.add_column("Heading", max_width=50)

            for i, r in enumerate(results, 1):
                score_str = f"{r.score:.1f}"
                if r.score >= 8:
                    score_str = f"[bold green]{score_str}[/]"
                elif r.score >= 6:
                    score_str = f"[green]{score_str}[/]"
                elif r.score >= 4:
                    score_str = f"[yellow]{score_str}[/]"
                else:
                    score_str = f"[dim]{score_str}[/]"

                table.add_row(
                    str(i),
                    score_str,
                    r.article_slug,
                    r.heading or r.section or "(untitled)",
                )

            console.print(table)

            # Show body previews
            if verbose:
                console.print()
                for i, r in enumerate(results, 1):
                    body_preview = r.body[:400].strip()
                    if len(r.body) > 400:
                        body_preview += "..."
                    console.print(
                        f"[dim][{i}][/] {body_preview}"
                    )
                    if r.source_refs:
                        refs = ", ".join(r.source_refs[:3])
                        console.print(f"    [dim]Sources: {refs}[/]")
                    console.print()
            else:
                # Show brief snippets for top 3
                console.print()
                for i, r in enumerate(results[:3], 1):
                    body_preview = r.body[:200].strip()
                    if len(r.body) > 200:
                        body_preview += "..."
                    console.print(f"[dim][{i}][/] {body_preview}")
                    console.print()

            return
        except ImportError:
            pass  # Fall through to plain

    # Plain text output
    for i, r in enumerate(results, 1):
        score_bar = _score_bar(r.score)
        typer.echo(
            f"  {i:>2}. [{score_bar}] {r.score:.1f}  "
            f"{r.article_slug} / {r.heading or r.section or '(untitled)'}"
        )
        if verbose:
            body_preview = r.body[:300].strip()
            if len(r.body) > 300:
                body_preview += "..."
            typer.echo(f"      {body_preview}")
            if r.source_refs:
                typer.echo(f"      Sources: {', '.join(r.source_refs[:3])}")
            typer.echo()


def _display_facts(facts: list, fmt: str) -> None:
    """Display Fact list in rich/plain/json format."""
    import json as json_mod

    if fmt == "json":
        typer.echo(json_mod.dumps([f.to_dict() for f in facts], indent=2))
        return

    if not facts:
        typer.echo("  No facts found.")
        return

    if fmt == "rich":
        try:
            from rich.console import Console
            from rich.table import Table

            console = Console()
            table = Table(title=f"Facts ({len(facts)} found)", show_lines=True)
            table.add_column("Subject", style="bold")
            table.add_column("Predicate", style="cyan")
            table.add_column("Value", style="green")
            table.add_column("Conf.", justify="right", width=5)
            table.add_column("Article", style="dim")

            for f in facts:
                conf_str = f"{f.confidence:.0%}" if f.confidence else "?"
                table.add_row(
                    f.subject, f.predicate, f.value, conf_str, f.article_slug
                )

            console.print(table)

            # Show source quotes for high-confidence facts
            for f in facts:
                if f.source_quote:
                    console.print(
                        f"  [dim]{f.subject}/{f.predicate}: "
                        f"\"{f.source_quote[:200]}\"[/]"
                    )

            return
        except ImportError:
            pass

    # Plain text
    for f in facts:
        conf = f"{f.confidence:.0%}" if f.confidence else "?"
        typer.echo(
            f"  {f.subject:<12} {f.predicate:<25} {f.value:<30} "
            f"[{conf}] ({f.article_slug})"
        )
        if f.source_quote:
            quote = f.source_quote[:150]
            if len(f.source_quote) > 150:
                quote += "..."
            typer.echo(f"    \"{quote}\"")


def _display_stale(articles: list[dict], fmt: str) -> None:
    """Display stale articles in rich/plain/json format."""
    import json as json_mod

    if fmt == "json":
        typer.echo(json_mod.dumps(articles, indent=2))
        return

    if not articles:
        typer.echo("  All articles are fresh.")
        return

    if fmt == "rich":
        try:
            from rich.console import Console
            from rich.table import Table

            console = Console()
            table = Table(
                title=f"Stale Articles ({len(articles)} found)", show_lines=False
            )
            table.add_column("Article", style="bold")
            table.add_column("Title")
            table.add_column("Source Date", style="cyan")
            table.add_column("Age (days)", justify="right")

            for a in articles:
                age = f"{a['age_days']:.0f}" if a.get("age_days") else "unknown"
                date_str = a.get("source_date") or "none"
                table.add_row(a["slug"], a["title"], date_str, age)

            console.print(table)
            return
        except ImportError:
            pass

    # Plain text
    for a in articles:
        age = f"{a['age_days']:.0f}d" if a.get("age_days") else "unknown"
        date_str = a.get("source_date") or "none"
        typer.echo(f"  {a['slug']:<35} {date_str:<12} {age:>8}  {a['title']}")


def _display_stats(stats_data: dict, fmt: str) -> None:
    """Display KB stats in rich/plain/json format."""
    import json as json_mod

    if fmt == "json":
        typer.echo(json_mod.dumps(stats_data, indent=2))
        return

    if fmt == "rich":
        try:
            from rich.console import Console
            from rich.table import Table

            console = Console()
            table = Table(title="Knowledge Base Statistics", show_lines=False)
            table.add_column("Metric", style="bold")
            table.add_column("Value", justify="right", style="green")

            display_names = {
                "articles": "Articles",
                "chunks": "Chunks (searchable units)",
                "facts": "Structured facts",
                "sources": "Source references",
                "carriers_tracked": "Carriers tracked",
                "topics": "Topics",
                "fresh_articles": "Fresh articles (<=90d)",
                "stale_articles": "Stale articles (>90d)",
                "oldest_article": "Oldest article",
                "newest_article": "Newest article",
            }

            for key, label in display_names.items():
                if key in stats_data:
                    val = stats_data[key]
                    table.add_row(label, str(val) if val is not None else "-")

            console.print(table)
            return
        except ImportError:
            pass

    # Plain text
    typer.echo("  Knowledge Base Statistics")
    typer.echo("  " + "-" * 40)
    for key, val in stats_data.items():
        label = key.replace("_", " ").title()
        typer.echo(f"  {label:<30} {val}")


def _display_related(items: list, fmt: str) -> None:
    """Display RelatedItem list in rich/plain/json format."""
    import json as json_mod

    if fmt == "json":
        typer.echo(json_mod.dumps([i.to_dict() for i in items], indent=2))
        return

    if not items:
        typer.echo("  No related content found.")
        return

    if fmt == "rich":
        try:
            from rich.console import Console
            from rich.table import Table

            console = Console()
            table = Table(
                title=f"Related Content ({len(items)} found)", show_lines=False
            )
            table.add_column("#", justify="right", style="dim", width=3)
            table.add_column("Strength", justify="right", width=8)
            table.add_column("Relation", style="cyan", width=14)
            table.add_column("Heading", max_width=50)

            for i, item in enumerate(items, 1):
                strength = f"{item.strength:.0%}"
                table.add_row(str(i), strength, item.relation, item.heading or "(untitled)")

            console.print(table)

            # Show previews
            console.print()
            for i, item in enumerate(items[:5], 1):
                console.print(f"  [dim][{i}][/] {item.body_preview}")
                console.print()

            return
        except ImportError:
            pass

    # Plain text
    for i, item in enumerate(items, 1):
        typer.echo(
            f"  {i:>2}. [{item.strength:.0%}] {item.relation:<14} "
            f"{item.heading or '(untitled)'}"
        )
        typer.echo(f"      {item.body_preview[:200]}")


# --- KB Subcommands ---


@kb_app.command(name="search")
def kb_search(
    query: Annotated[str, typer.Argument(help="Natural language search query")],
    carrier: Annotated[
        Optional[str],
        typer.Option("--carrier", "-c", help="Filter by carrier code"),
    ] = None,
    topic: Annotated[
        Optional[str],
        typer.Option("--topic", "-t", help="Filter by topic"),
    ] = None,
    limit: Annotated[
        int, typer.Option("--limit", "-n", help="Max results")
    ] = 10,
    json_out: JsonFlag = False,
    plain: PlainFlag = False,
    verbose: VerboseFlag = False,
) -> None:
    """Search the knowledge base with natural language."""
    kb = _open_kb()
    with kb:
        results = kb.search(query, carrier=carrier, topic=topic, limit=limit)
        fmt = _get_format(json_out, plain)
        _display_kb_results(results, fmt, verbose=verbose, query=query)


@kb_app.command(name="carrier")
def kb_carrier(
    code: Annotated[str, typer.Argument(help="2-letter IATA carrier code")],
    context: Annotated[
        Optional[str],
        typer.Option("--context", help="Filter: yq, msc, availability, booking"),
    ] = None,
    limit: Annotated[int, typer.Option("--limit", "-n")] = 20,
    json_out: JsonFlag = False,
    plain: PlainFlag = False,
    verbose: VerboseFlag = False,
) -> None:
    """Show all knowledge about a specific carrier."""
    kb = _open_kb()
    with kb:
        results = kb.carrier_lookup(code, context=context, limit=limit)
        fmt = _get_format(json_out, plain)
        _display_kb_results(results, fmt, verbose=verbose, query=code)


@kb_app.command(name="lookup")
def kb_lookup(
    subject: Annotated[
        str, typer.Argument(help="Subject to look up (carrier, route, rule)")
    ],
    predicate: Annotated[
        Optional[str],
        typer.Argument(help="Predicate to narrow (yq, rate, etc.)"),
    ] = None,
    json_out: JsonFlag = False,
    plain: PlainFlag = False,
) -> None:
    """Look up structured facts. Example: rtw kb lookup BA yq"""
    kb = _open_kb()
    with kb:
        facts = kb.fact_lookup(subject, predicate)
        fmt = _get_format(json_out, plain)
        _display_facts(facts, fmt)


@kb_app.command(name="ask")
def kb_ask(
    question: Annotated[str, typer.Argument(help="Natural language question")],
    limit: Annotated[int, typer.Option("--limit", "-n")] = 5,
    json_out: JsonFlag = False,
    plain: PlainFlag = False,
    verbose: VerboseFlag = False,
) -> None:
    """Answer a question using the knowledge base."""
    kb = _open_kb()
    with kb:
        results = kb.answer(question, limit=limit)
        fmt = _get_format(json_out, plain)
        _display_kb_results(results, fmt, verbose=verbose, query=question)


@kb_app.command(name="related")
def kb_related(
    chunk_id: Annotated[
        int, typer.Argument(help="Chunk ID to find related content for")
    ],
    limit: Annotated[int, typer.Option("--limit", "-n")] = 10,
    json_out: JsonFlag = False,
    plain: PlainFlag = False,
) -> None:
    """Find content related to a specific chunk."""
    kb = _open_kb()
    with kb:
        items = kb.related(chunk_id, limit=limit)
        fmt = _get_format(json_out, plain)
        _display_related(items, fmt)


@kb_app.command(name="stale")
def kb_stale(
    days: Annotated[
        int, typer.Option("--days", "-d", help="Max age in days")
    ] = 90,
    json_out: JsonFlag = False,
    plain: PlainFlag = False,
) -> None:
    """Find stale knowledge older than a threshold."""
    kb = _open_kb()
    with kb:
        articles = kb.stale_articles(max_age_days=days)
        fmt = _get_format(json_out, plain)
        _display_stale(articles, fmt)


@kb_app.command(name="stats")
def kb_stats(
    json_out: JsonFlag = False,
    plain: PlainFlag = False,
) -> None:
    """Show knowledge base statistics."""
    kb = _open_kb()
    with kb:
        data = kb.stats()
        fmt = _get_format(json_out, plain)
        _display_stats(data, fmt)


@kb_app.command(name="brief")
def kb_brief(
    origin: Annotated[
        Optional[str],
        typer.Option("--origin", "-o", help="Origin airport code"),
    ] = None,
    ticket: Annotated[
        Optional[str],
        typer.Option("--ticket", "-t", help="Ticket type (DONE3, DONE4, etc.)"),
    ] = None,
    carrier_codes: Annotated[
        Optional[list[str]],
        typer.Option("--carrier", "-c", help="Carrier codes"),
    ] = None,
    city: Annotated[
        Optional[list[str]],
        typer.Option("--city", help="Cities on route"),
    ] = None,
    json_out: JsonFlag = False,
    plain: PlainFlag = False,
) -> None:
    """Contextual briefing for a specific booking scenario."""
    kb = _open_kb()
    with kb:
        results = kb.context_brief(
            origin=origin,
            ticket_type=ticket,
            carriers=carrier_codes,
            cities=city,
        )
        fmt = _get_format(json_out, plain)
        _display_kb_results(results, fmt, verbose=True, query="brief")


@kb_app.command(name="topic")
def kb_topic(
    name: Annotated[str, typer.Argument(help="Topic name or partial match")],
    limit: Annotated[int, typer.Option("--limit", "-n")] = 15,
    json_out: JsonFlag = False,
    plain: PlainFlag = False,
    verbose: VerboseFlag = False,
) -> None:
    """Show everything on a topic."""
    kb = _open_kb()
    with kb:
        results = kb.topic_search(name, limit=limit)
        fmt = _get_format(json_out, plain)
        _display_kb_results(results, fmt, verbose=verbose, query=name)


@kb_app.command(name="list")
def kb_list(
    json_out: JsonFlag = False,
    plain: PlainFlag = False,
) -> None:
    """List all articles in the knowledge base."""
    import json as json_mod

    kb = _open_kb()
    with kb:
        articles = kb.list_articles()
        fmt = _get_format(json_out, plain)

        if fmt == "json":
            typer.echo(json_mod.dumps(articles, indent=2))
            return

        if not articles:
            typer.echo("  No articles in the knowledge base.")
            return

        if fmt == "rich":
            try:
                from rich.console import Console
                from rich.table import Table

                console = Console()
                table = Table(
                    title=f"KB Articles ({len(articles)})", show_lines=False
                )
                table.add_column("Article", style="bold")
                table.add_column("Title")
                table.add_column("Category", style="cyan")
                table.add_column("Words", justify="right")
                table.add_column("Sections", justify="right")
                table.add_column("Findings", justify="right")

                for a in articles:
                    table.add_row(
                        a["slug"],
                        a["title"],
                        a.get("category") or "-",
                        str(a.get("word_count") or "-"),
                        str(a.get("section_count", 0)),
                        str(a.get("finding_count", 0)),
                    )
                console.print(table)
                return
            except ImportError:
                pass

        # Plain text
        for a in articles:
            typer.echo(
                f"  {a['slug']:<35} {a.get('category') or '-':<14} "
                f"{a.get('word_count') or '-':>6} words  "
                f"{a.get('section_count', 0):>3} sections  "
                f"{a.get('finding_count', 0):>3} findings  "
                f"{a['title']}"
            )


@kb_app.command(name="carriers")
def kb_carriers(
    json_out: JsonFlag = False,
    plain: PlainFlag = False,
) -> None:
    """List all carriers with mention counts."""
    import json as json_mod

    kb = _open_kb()
    with kb:
        carrier_list = kb.list_carriers()
        fmt = _get_format(json_out, plain)

        if fmt == "json":
            typer.echo(json_mod.dumps(carrier_list, indent=2))
            return

        if not carrier_list:
            typer.echo("  No carrier data found.")
            return

        if fmt == "rich":
            try:
                from rich.console import Console
                from rich.table import Table

                console = Console()
                table = Table(title="Carrier Mentions", show_lines=False)
                table.add_column("Carrier", style="bold")
                table.add_column("Total", justify="right")
                table.add_column("YQ", justify="right")
                table.add_column("MSC", justify="right")
                table.add_column("Avail.", justify="right")
                table.add_column("Warnings", justify="right", style="red")

                for c in carrier_list:
                    table.add_row(
                        c["carrier"],
                        str(c["total_mentions"]),
                        str(c.get("yq_mentions", 0)),
                        str(c.get("msc_mentions", 0)),
                        str(c.get("avail_mentions", 0)),
                        str(c.get("warnings", 0)),
                    )
                console.print(table)
                return
            except ImportError:
                pass

        # Plain text
        typer.echo(
            f"  {'Carrier':<10} {'Total':>6} {'YQ':>5} {'MSC':>5} "
            f"{'Avail':>6} {'Warn':>5}"
        )
        typer.echo("  " + "-" * 42)
        for c in carrier_list:
            typer.echo(
                f"  {c['carrier']:<10} {c['total_mentions']:>6} "
                f"{c.get('yq_mentions', 0):>5} {c.get('msc_mentions', 0):>5} "
                f"{c.get('avail_mentions', 0):>6} {c.get('warnings', 0):>5}"
            )


@kb_app.command(name="topics")
def kb_topics(
    json_out: JsonFlag = False,
    plain: PlainFlag = False,
) -> None:
    """List all topics."""
    import json as json_mod

    kb = _open_kb()
    with kb:
        topic_list = kb.list_topics()
        fmt = _get_format(json_out, plain)

        if fmt == "json":
            typer.echo(json_mod.dumps(topic_list, indent=2))
            return

        if not topic_list:
            typer.echo("  No topics found.")
            return

        if fmt == "rich":
            try:
                from rich.console import Console
                from rich.table import Table

                console = Console()
                table = Table(title="KB Topics", show_lines=False)
                table.add_column("Topic", style="bold")
                table.add_column("Display Name")
                table.add_column("Chunks", justify="right")
                table.add_column("Description", max_width=40)

                for t in topic_list:
                    table.add_row(
                        t["name"],
                        t.get("display") or "",
                        str(t.get("chunk_count", 0)),
                        t.get("description") or "",
                    )
                console.print(table)
                return
            except ImportError:
                pass

        # Plain text
        for t in topic_list:
            typer.echo(
                f"  {t['name']:<30} {t.get('chunk_count', 0):>4} chunks  "
                f"{t.get('display') or ''}"
            )


@kb_app.command(name="sources")
def kb_sources(
    source_type: Annotated[
        Optional[str],
        typer.Option("--type", help="flyertalk_thread, document, web"),
    ] = None,
    article: Annotated[
        Optional[str], typer.Option("--article", help="Article slug")
    ] = None,
    json_out: JsonFlag = False,
    plain: PlainFlag = False,
) -> None:
    """List knowledge base sources."""
    import json as json_mod

    kb = _open_kb()
    with kb:
        srcs = kb.get_sources(source_type=source_type, article_slug=article)
        fmt = _get_format(json_out, plain)

        if fmt == "json":
            typer.echo(json_mod.dumps(srcs, indent=2))
            return

        if not srcs:
            typer.echo("  No sources found.")
            return

        if fmt == "rich":
            try:
                from rich.console import Console
                from rich.table import Table

                console = Console()
                table = Table(
                    title=f"KB Sources ({len(srcs)})", show_lines=False
                )
                table.add_column("Type", style="cyan")
                table.add_column("Reference")
                table.add_column("Title")
                table.add_column("Date", style="dim")

                for s in srcs:
                    table.add_row(
                        s.get("source_type", ""),
                        s.get("reference", ""),
                        s.get("title") or "",
                        s.get("date") or "-",
                    )
                console.print(table)
                return
            except ImportError:
                pass

        # Plain text
        for s in srcs:
            typer.echo(
                f"  [{s.get('source_type', '')}] "
                f"{s.get('title') or s.get('reference', '')}  "
                f"{s.get('date') or ''}"
            )


# Also expose get_sources on KnowledgeBase for programmatic use
# (already defined in the class -- the CLI wrapper above calls it)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
