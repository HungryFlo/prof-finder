"""Profile management commands."""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from ..db import get_db
from ..models import UserProfile
from ..parser import MarkdownParser, LaTeXParser, ParsedResume, EducationEntry, ExperienceEntry, ProjectEntry
from .utils import (
    get_current_user,
    display_parsed_resume,
    confirm_and_save_profile,
    display_profile,
)

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("upload")
def upload_resume(
    file_path: Path = typer.Argument(..., help="Path to resume file (.md or .tex)"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Profile title"),
    user: Optional[str] = typer.Option(None, "--user", "-u", help="Username"),
) -> None:
    """Upload and parse a resume file."""
    # Check file exists
    if not file_path.exists():
        console.print(f"[red]错误: 文件不存在: {file_path}[/red]")
        raise typer.Exit(1)

    # Determine parser based on extension
    ext = file_path.suffix.lower()
    
    if ext in MarkdownParser.supported_extensions():
        parser = MarkdownParser()
        source_format = "markdown"
    elif ext in LaTeXParser.supported_extensions():
        parser = LaTeXParser()
        source_format = "latex"
    else:
        console.print(f"[red]错误: 不支持的文件格式 '{ext}'[/red]")
        console.print("[yellow]支持的格式: .md, .markdown, .tex, .latex[/yellow]")
        raise typer.Exit(1)

    # Read and parse file
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        console.print("[red]错误: 文件编码不是UTF-8，请检查文件编码[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]正在解析文件: {file_path}[/cyan]")
    parsed = parser.parse(content)

    # Get user and generate title
    current_user = get_current_user(user)
    profile_title = title or f"简历 - {file_path.stem}"

    # Confirm and save
    confirm_and_save_profile(current_user, parsed, profile_title, source_format)


@app.command("input")
def manual_input(
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Profile title"),
    name: Optional[str] = typer.Option(None, "--name", help="Your name"),
    education: Optional[str] = typer.Option(None, "--education", help="Education background"),
    research: Optional[str] = typer.Option(None, "--research", help="Research experience"),
    projects: Optional[str] = typer.Option(None, "--projects", help="Projects"),
    skills: Optional[str] = typer.Option(None, "--skills", help="Skills (comma-separated)"),
    user: Optional[str] = typer.Option(None, "--user", "-u", help="Username"),
) -> None:
    """Manually input profile information."""
    console.print("[bold cyan]手动输入个人信息[/bold cyan]\n")
    console.print("[dim]提示: 可以直接回车跳过某项[/dim]\n")

    # Interactive input for missing fields
    if name is None:
        name = Prompt.ask("姓名", default="")
    
    if education is None:
        console.print("\n[yellow]教育背景示例:[/yellow]")
        console.print("  本科清华大学计算机科学，硕士斯坦福大学人工智能")
        education = Prompt.ask("教育背景", default="")
    
    if research is None:
        console.print("\n[yellow]科研经历示例:[/yellow]")
        console.print("  在NLP领域发表3篇论文，参与过机器翻译项目")
        research = Prompt.ask("科研经历", default="")
    
    if projects is None:
        console.print("\n[yellow]项目经历示例:[/yellow]")
        console.print("  智能对话系统，自然语言处理")
        projects = Prompt.ask("项目经历 (逗号分隔)", default="")
    
    if skills is None:
        console.print("\n[yellow]技能专长示例:[/yellow]")
        console.print("  Python, TensorFlow, NLP算法")
        skills = Prompt.ask("技能专长 (逗号分隔)", default="")

    # Parse input into structured data
    parsed = ParsedResume(
        name=name if name else None,
        education=_parse_education_text(education),
        research_experience=_parse_experience_text(research),
        projects=_parse_projects_text(projects),
        skills=[s.strip() for s in skills.split(",") if s.strip()] if skills else [],
        raw_content=f"Name: {name}\nEducation: {education}\nResearch: {research}\nProjects: {projects}\nSkills: {skills}",
    )

    # Get user and title
    current_user = get_current_user(user)
    profile_title = title or "手动输入简历"

    # Confirm and save
    confirm_and_save_profile(current_user, parsed, profile_title, "manual")


def _parse_education_text(text: str) -> list[EducationEntry]:
    """Parse education text into entries."""
    if not text:
        return []
    
    entries = []
    # Split by common delimiters
    parts = text.replace("；", ",").replace("，", ",").split(",")
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Try to detect degree and school
        degree = "未知"
        school = part
        
        degree_keywords = {
            "本科": "本科", "学士": "本科", "bachelor": "本科",
            "硕士": "硕士", "master": "硕士", "mphil": "硕士",
            "博士": "博士", "phd": "博士",
        }
        
        for keyword, deg in degree_keywords.items():
            if keyword in part.lower():
                degree = deg
                school = part.replace(keyword, "").strip()
                break
        
        entries.append(EducationEntry(degree=degree, school=school))
    
    return entries


def _parse_experience_text(text: str) -> list[ExperienceEntry]:
    """Parse experience text into entries."""
    if not text:
        return []
    
    # Treat the whole text as one experience entry
    return [ExperienceEntry(title="科研经历", description=text)]


def _parse_projects_text(text: str) -> list[ProjectEntry]:
    """Parse projects text into entries."""
    if not text:
        return []
    
    entries = []
    parts = text.replace("；", ",").replace("，", ",").split(",")
    
    for part in parts:
        part = part.strip()
        if part:
            entries.append(ProjectEntry(name=part))
    
    return entries


@app.command("show")
def show_profile(
    profile_id: Optional[int] = typer.Argument(None, help="Profile ID to show"),
    user: Optional[str] = typer.Option(None, "--user", "-u", help="Username"),
) -> None:
    """Show profile details."""
    current_user = get_current_user(user)
    db = get_db()

    with db.session() as session:
        if profile_id:
            # Show specific profile
            profile = session.query(UserProfile).filter(
                UserProfile.id == profile_id,
                UserProfile.user_id == current_user.id,
            ).first()
            
            if not profile:
                console.print(f"[red]错误: 未找到简历 ID {profile_id}[/red]")
                raise typer.Exit(1)
        else:
            # Show active profile
            profile = session.query(UserProfile).filter(
                UserProfile.user_id == current_user.id,
                UserProfile.is_active == True,
            ).first()
            
            if not profile:
                console.print("[yellow]尚未添加简历[/yellow]")
                console.print("使用 [cyan]prof-finder profile upload[/cyan] 上传简历")
                console.print("或使用 [cyan]prof-finder profile input[/cyan] 手动输入")
                raise typer.Exit(0)

        display_profile(profile)


@app.command("list")
def list_profiles(
    user: Optional[str] = typer.Option(None, "--user", "-u", help="Username"),
) -> None:
    """List all profiles."""
    current_user = get_current_user(user)
    db = get_db()

    with db.session() as session:
        profiles = session.query(UserProfile).filter(
            UserProfile.user_id == current_user.id,
        ).order_by(UserProfile.updated_at.desc()).all()

        if not profiles:
            console.print("[yellow]尚未添加任何简历[/yellow]")
            return

        table = Table(title=f"简历列表 (用户: {current_user.username})")
        table.add_column("ID", style="cyan", width=6)
        table.add_column("标题", style="bold")
        table.add_column("姓名")
        table.add_column("状态")
        table.add_column("更新时间")

        for profile in profiles:
            status = "[green]激活[/green]" if profile.is_active else "[dim]未激活[/dim]"
            table.add_row(
                str(profile.id),
                profile.title,
                profile.name or "-",
                status,
                str(profile.updated_at)[:19],
            )

        console.print(table)


@app.command("activate")
def activate_profile(
    profile_id: int = typer.Argument(..., help="Profile ID to activate"),
    user: Optional[str] = typer.Option(None, "--user", "-u", help="Username"),
) -> None:
    """Set a profile as active."""
    current_user = get_current_user(user)
    db = get_db()

    with db.session() as session:
        profile = session.query(UserProfile).filter(
            UserProfile.id == profile_id,
            UserProfile.user_id == current_user.id,
        ).first()

        if not profile:
            console.print(f"[red]错误: 未找到简历 ID {profile_id}[/red]")
            raise typer.Exit(1)

        # Deactivate all others
        session.query(UserProfile).filter(
            UserProfile.user_id == current_user.id,
        ).update({"is_active": False})

        # Activate this one
        profile.is_active = True
        session.commit()

        console.print(f"[green]✓ 已激活简历: {profile.title}[/green]")


@app.command("delete")
def delete_profile(
    profile_id: int = typer.Argument(..., help="Profile ID to delete"),
    user: Optional[str] = typer.Option(None, "--user", "-u", help="Username"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a profile."""
    from rich.prompt import Confirm

    current_user = get_current_user(user)
    db = get_db()

    with db.session() as session:
        profile = session.query(UserProfile).filter(
            UserProfile.id == profile_id,
            UserProfile.user_id == current_user.id,
        ).first()

        if not profile:
            console.print(f"[red]错误: 未找到简历 ID {profile_id}[/red]")
            raise typer.Exit(1)

        if not force:
            if not Confirm.ask(f"确定要删除简历 '{profile.title}'?", default=False):
                console.print("[yellow]已取消[/yellow]")
                return

        session.delete(profile)
        session.commit()

        console.print(f"[green]✓ 已删除简历: {profile.title}[/green]")
