"""Match command for Prof-Finder."""

from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from ..db import get_db
from ..models import UserProfile, Professor, MatchRecord
from ..matcher import KeywordMatcher
from .utils import get_current_user

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("run")
def run_match(
    profile_id: Optional[int] = typer.Option(None, "--profile", "-p", help="Profile ID to use"),
    top_n: int = typer.Option(10, "--top", "-n", help="Number of top matches to show"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save match results to database"),
    user: Optional[str] = typer.Option(None, "--user", "-u", help="Username"),
) -> None:
    """Run matching algorithm against all professors."""
    current_user = get_current_user(user)
    db = get_db()
    matcher = KeywordMatcher()

    with db.session() as session:
        # Get profile
        if profile_id:
            profile = session.query(UserProfile).filter(
                UserProfile.id == profile_id,
                UserProfile.user_id == current_user.id,
            ).first()
        else:
            profile = session.query(UserProfile).filter(
                UserProfile.user_id == current_user.id,
                UserProfile.is_active == True,
            ).first()

        if not profile:
            console.print("[red]错误: 未找到简历[/red]")
            console.print("请先使用 [cyan]prof-finder profile upload[/cyan] 添加简历")
            raise typer.Exit(1)

        console.print(f"[cyan]使用简历: {profile.title}[/cyan]")

        # Get professors
        professors = session.query(Professor).filter(
            Professor.user_id == current_user.id,
        ).all()

        if not professors:
            console.print("[red]错误: 未找到教授数据[/red]")
            console.print("请先使用 [cyan]prof-finder professor add[/cyan] 添加教授")
            raise typer.Exit(1)

        console.print(f"[cyan]正在匹配 {len(professors)} 位教授...[/cyan]\n")

        # Run matching
        results = []
        for professor in professors:
            result = matcher.match(profile, professor)
            results.append(result)

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        top_results = results[:top_n]

        # Display results
        _display_match_results(top_results)

        # Save to database
        if save:
            for result in results:
                # Check if record exists
                existing = session.query(MatchRecord).filter(
                    MatchRecord.user_profile_id == profile.id,
                    MatchRecord.professor_id == result.professor_id,
                ).first()

                if existing:
                    existing.score = result.score
                    existing.match_reasons = result.reasons
                else:
                    record = MatchRecord(
                        user_profile_id=profile.id,
                        professor_id=result.professor_id,
                        score=result.score,
                        match_reasons=result.reasons,
                    )
                    session.add(record)

            session.commit()
            console.print(f"\n[green]✓ 已保存 {len(results)} 条匹配记录[/green]")


def _display_match_results(results: list) -> None:
    """Display match results in a table."""
    table = Table(title="匹配结果")
    table.add_column("排名", justify="center", width=6)
    table.add_column("教授", style="bold")
    table.add_column("匹配度", justify="right", width=8)
    table.add_column("匹配原因", width=50)

    for i, result in enumerate(results, 1):
        score_color = "green" if result.score >= 60 else "yellow" if result.score >= 30 else "red"
        reasons = "\n".join(result.reasons) if result.reasons else "-"
        
        table.add_row(
            str(i),
            result.professor_name,
            f"[{score_color}]{result.score:.1f}[/{score_color}]",
            reasons,
        )

    console.print(table)


@app.command("show")
def show_matches(
    profile_id: Optional[int] = typer.Option(None, "--profile", "-p", help="Profile ID"),
    top_n: int = typer.Option(10, "--top", "-n", help="Number of matches to show"),
    user: Optional[str] = typer.Option(None, "--user", "-u", help="Username"),
) -> None:
    """Show saved match results."""
    current_user = get_current_user(user)
    db = get_db()

    with db.session() as session:
        # Get profile
        if profile_id:
            profile = session.query(UserProfile).filter(
                UserProfile.id == profile_id,
                UserProfile.user_id == current_user.id,
            ).first()
        else:
            profile = session.query(UserProfile).filter(
                UserProfile.user_id == current_user.id,
                UserProfile.is_active == True,
            ).first()

        if not profile:
            console.print("[red]错误: 未找到简历[/red]")
            raise typer.Exit(1)

        # Get match records
        records = session.query(MatchRecord).filter(
            MatchRecord.user_profile_id == profile.id,
        ).order_by(MatchRecord.score.desc()).limit(top_n).all()

        if not records:
            console.print("[yellow]无匹配记录[/yellow]")
            console.print("使用 [cyan]prof-finder match run[/cyan] 执行匹配")
            return

        console.print(f"[cyan]简历: {profile.title}[/cyan]\n")

        table = Table(title="匹配结果")
        table.add_column("排名", justify="center", width=6)
        table.add_column("教授ID", width=8)
        table.add_column("教授", style="bold")
        table.add_column("匹配度", justify="right", width=8)
        table.add_column("已生成邮件", justify="center", width=10)

        for i, record in enumerate(records, 1):
            score_color = "green" if record.score >= 60 else "yellow" if record.score >= 30 else "red"
            letter_status = "[green]✓[/green]" if record.letter_content else "[dim]-[/dim]"
            
            table.add_row(
                str(i),
                str(record.professor_id),
                record.professor.name,
                f"[{score_color}]{record.score:.1f}[/{score_color}]",
                letter_status,
            )

        console.print(table)
