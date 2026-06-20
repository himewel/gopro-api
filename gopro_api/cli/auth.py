"""Auth command: AuthPrinter class, async runner, and Typer callback."""

from __future__ import annotations

import asyncio
import json
import sys

import typer
from rich.console import Console
from rich.panel import Panel
from rich.status import Status
from rich.table import Table
from rich import box

from gopro_api.api.models import GoProAuthStatus
from gopro_api.client import AsyncGoProClient

from .app import app
from ._common import _yes_no


class AuthPrinter:
    """Handles Rich, TSV, and JSON rendering for the auth command."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize with an optional Rich console.

        Args:
            console: Console used for Rich output; a default soft-wrap console is
                created when ``None``.
        """
        self._console = console or Console(soft_wrap=True)
        self._active_status: Status | None = None

    def start_stage(self) -> None:
        """Show a spinner while the API verification request runs."""
        self._active_status = self._console.status(
            "⏳ [bold cyan]Verifying access token…[/bold cyan]",
        )
        self._active_status.__enter__()

    def stop_stage(self) -> None:
        """Stop the active spinner, if any."""
        if self._active_status is not None:
            self._active_status.__exit__(None, None, None)
            self._active_status = None

    def _authenticated_label(self, status: GoProAuthStatus) -> str:
        """Format the authenticated field for display.

        Args:
            status: Authentication status from the API client.

        Returns:
            Human-readable yes/no/not checked label.
        """
        if status.authenticated is None:
            return "not checked"
        return _yes_no(status.authenticated)

    def print_rich(self, status: GoProAuthStatus) -> None:
        """Print authentication status as a Rich panel.

        Args:
            status: Authentication status from the API client.
        """
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("field", style="bold")
        table.add_column("value")
        table.add_row("token configured", _yes_no(status.token_configured))
        table.add_row(
            "token source",
            status.token_source or "—",
        )
        table.add_row("authenticated", self._authenticated_label(status))
        if status.http_status is not None:
            table.add_row("http status", str(status.http_status))
        table.add_row("message", status.message)

        border = "green" if status.authenticated else "red"
        if not status.token_configured:
            border = "yellow"
        elif status.authenticated is None:
            border = "yellow"

        self._console.print(
            Panel(
                table,
                title="[bold blue]Authentication[/bold blue]",
                border_style=border,
            ),
        )

    def print_tsv(self, status: GoProAuthStatus) -> None:
        """Print authentication status as tab-separated key/value rows.

        Args:
            status: Authentication status from the API client.
        """
        rows = {
            "token_configured": _yes_no(status.token_configured),
            "token_source": status.token_source or "",
            "authenticated": self._authenticated_label(status),
            "http_status": (
                "" if status.http_status is None else str(status.http_status)
            ),
            "message": status.message,
        }
        console = Console(soft_wrap=True, highlight=False, markup=False)
        console.print("field\tvalue")
        for key, value in rows.items():
            console.print(f"{key}\t{value}")

    def print_json(self, status: GoProAuthStatus) -> None:
        """Print authentication status as JSON on stdout.

        Args:
            status: Authentication status from the API client.
        """
        sys.stdout.write(json.dumps(status.model_dump(mode="json"), indent=2))
        sys.stdout.write("\n")

    def exit_code(self, status: GoProAuthStatus) -> int:
        """Map authentication status to a process exit code.

        Args:
            status: Authentication status from the API client.

        Returns:
            ``0`` when authenticated, ``2`` when the token is missing, ``1`` otherwise.
        """
        if not status.token_configured:
            return 2
        if status.authenticated:
            return 0
        return 1


async def _run_auth(
    *,
    timeout: float,
    json_out: bool,
    tsv: bool,
) -> None:
    """Verify ``GP_ACCESS_TOKEN`` and render the result.

    Args:
        timeout: HTTP timeout in seconds passed to ``AsyncGoProClient``.
        json_out: When ``True``, emit JSON instead of a Rich panel.
        tsv: When ``True``, emit tab-separated values instead of a Rich panel.
    """
    printer = AuthPrinter()
    if not json_out and not tsv:
        printer.start_stage()
    try:
        async with AsyncGoProClient(timeout=timeout) as client:
            status = await client.check_auth()
    finally:
        printer.stop_stage()

    if json_out:
        printer.print_json(status)
    elif tsv:
        printer.print_tsv(status)
    else:
        printer.print_rich(status)

    raise typer.Exit(printer.exit_code(status))


@app.command(
    "auth",
    help=(
        "Verify GP_ACCESS_TOKEN configuration and authentication "
        "(Rich panel by default; --tsv or --json for scripting)"
    ),
)
def auth_command(
    ctx: typer.Context,
    tsv: bool = typer.Option(
        False,
        "--tsv",
        help="Print tab-separated values for scripting",
    ),
    json_out: bool = typer.Option(
        False,
        "--json",
        help="Print structured JSON",
    ),
) -> None:
    """Check whether the GoPro access token is configured and accepted by the API."""
    asyncio.run(
        _run_auth(
            timeout=ctx.obj["timeout"],
            json_out=json_out,
            tsv=tsv,
        ),
    )
