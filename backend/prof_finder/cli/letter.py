"""Letter generation command for Prof-Finder."""

from typing import Optional
from ..utils.time import utc_now
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from ..db import get_db
from ..models import UserProfile, Professor, MatchRecord
from ..llm import LetterGenerator
from ..config import settings
from .utils import get_current_user

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("generate")
def generate_letter(
    professor_id: int = typer.Argument(..., help="Professor ID to generate letter for"),
    profile_id: Optional[int] = typer.Option(None, "--profile", "-p", help="Profile ID to use"),
    language: str = typer.Option("zh", "--lang", "-l", help="Language: zh (Chinese) or en (English)"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save letter to database"),
    user: Optional[str] = typer.Option(None, "--user", "-u", help="Username"),
) -> None:
    """Generate a contact letter for a professor."""
    # Check API key
    if not settings.deepseek_api_key:
        console.print("[red]错误: 未配置 DEEPSEEK_API_KEY[/red]")
        console.print("请在 .env 文件中配置 API Key")
        raise typer.Exit(1)

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

        # Get professor
        professor = session.query(Professor).filter(
            Professor.id == professor_id,
            Professor.user_id == current_user.id,
        ).first()

        if not professor:
            console.print(f"[red]错误: 未找到教授 ID {professor_id}[/red]")
            raise typer.Exit(1)

        # Get match record for reasons
        match_record = session.query(MatchRecord).filter(
            MatchRecord.user_profile_id == profile.id,
            MatchRecord.professor_id == professor_id,
        ).first()

        match_reasons = match_record.match_reasons if match_record else None

        console.print(f"[cyan]正在为 {professor.name} 生成联络邮件...[/cyan]\n")

        # Generate letter
        try:
            generator = LetterGenerator()
            letter = generator.generate(
                profile=profile,
                professor=professor,
                match_reasons=match_reasons,
                language=language,
            )
        except Exception as e:
            console.print(f"[red]错误: 生成失败 - {e}[/red]")
            raise typer.Exit(1)

        # Display letter
        console.print(Panel(
            letter,
            title=f"[bold]致 {professor.name} 的联络邮件[/bold]",
            border_style="green",
        ))

        # Save if requested
        if save:
            if not match_record:
                match_record = MatchRecord(
                    user_profile_id=profile.id,
                    professor_id=professor_id,
                    score=0,
                    match_reasons=[],
                )
                session.add(match_record)

            match_record.letter_content = letter
            match_record.letter_generated_at = utc_now()
            session.commit()

            console.print("\n[green]✓ 邮件已保存[/green]")


@app.command("show")
def show_letter(
    professor_id: int = typer.Argument(..., help="Professor ID"),
    profile_id: Optional[int] = typer.Option(None, "--profile", "-p", help="Profile ID"),
    user: Optional[str] = typer.Option(None, "--user", "-u", help="Username"),
) -> None:
    """Show a previously generated letter."""
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

        # Get match record
        record = session.query(MatchRecord).filter(
            MatchRecord.user_profile_id == profile.id,
            MatchRecord.professor_id == professor_id,
        ).first()

        if not record or not record.letter_content:
            console.print("[yellow]未找到已生成的邮件[/yellow]")
            console.print(f"使用 [cyan]prof-finder letter generate {professor_id}[/cyan] 生成邮件")
            return

        console.print(Panel(
            record.letter_content,
            title=f"[bold]致 {record.professor.name} 的联络邮件[/bold]",
            subtitle=f"生成时间: {record.letter_generated_at}",
            border_style="green",
        ))


@app.command("batch")
def batch_generate(
    top_n: int = typer.Option(5, "--top", "-n", help="Generate for top N matches"),
    profile_id: Optional[int] = typer.Option(None, "--profile", "-p", help="Profile ID"),
    language: str = typer.Option("zh", "--lang", "-l", help="Language: zh or en"),
    user: Optional[str] = typer.Option(None, "--user", "-u", help="Username"),
) -> None:
    """Generate letters for top matched professors."""
    # Check API key
    if not settings.deepseek_api_key:
        console.print("[red]错误: 未配置 DEEPSEEK_API_KEY[/red]")
        raise typer.Exit(1)

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

        # Get top matches without letters
        records = session.query(MatchRecord).filter(
            MatchRecord.user_profile_id == profile.id,
            MatchRecord.letter_content == None,
        ).order_by(MatchRecord.score.desc()).limit(top_n).all()

        if not records:
            console.print("[yellow]没有需要生成邮件的匹配记录[/yellow]")
            console.print("所有匹配的教授都已生成邮件，或没有匹配记录")
            return

        console.print(f"[cyan]将为 {len(records)} 位教授生成邮件[/cyan]\n")

        if not Confirm.ask("确认继续?", default=True):
            console.print("[yellow]已取消[/yellow]")
            return

        generator = LetterGenerator()
        success_count = 0

        for record in records:
            try:
                console.print(f"[cyan]生成中: {record.professor.name}...[/cyan]")
                
                letter = generator.generate(
                    profile=profile,
                    professor=record.professor,
                    match_reasons=record.match_reasons,
                    language=language,
                )

                record.letter_content = letter
                record.letter_generated_at = utc_now()
                session.commit()

                console.print(f"[green]✓ {record.professor.name}[/green]")
                success_count += 1

            except Exception as e:
                console.print(f"[red]✗ {record.professor.name}: {e}[/red]")

        console.print(f"\n[green]成功生成 {success_count}/{len(records)} 封邮件[/green]")
