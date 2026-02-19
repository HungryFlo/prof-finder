"""Main CLI entry point for Prof-Finder."""

import typer
from rich.console import Console

from .. import __version__
from .profile import app as profile_app
from .professor import app as professor_app
from .match import app as match_app
from .letter import app as letter_app

# Create main app
app = typer.Typer(
    name="prof-finder",
    help="A tool to help students find potential PhD/MPhil supervisors.",
    no_args_is_help=True,
)

# Register sub-commands
app.add_typer(profile_app, name="profile", help="Manage your profile/resume")
app.add_typer(professor_app, name="professor", help="Manage professor database")
app.add_typer(match_app, name="match", help="Match with professors")
app.add_typer(letter_app, name="letter", help="Generate contact letters")

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold blue]Prof-Finder[/bold blue] version [green]{__version__}[/green]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Prof-Finder: Find your ideal PhD/MPhil supervisor."""
    pass


if __name__ == "__main__":
    app()
