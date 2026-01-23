"""CLI utility functions."""

from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from ..db import get_db
from ..models import User, UserProfile
from ..config import settings
from ..parser import ParsedResume

console = Console()


def get_current_user(username: Optional[str] = None) -> User:
    """Get or create user by username.
    
    Args:
        username: Username to use. If None, uses default from settings.
        
    Returns:
        User instance.
    """
    db = get_db()
    name = username or settings.default_user
    return db.get_or_create_user(name)


def display_parsed_resume(parsed: ParsedResume) -> None:
    """Display parsed resume in a formatted way."""
    console.print()
    console.print(Panel.fit("[bold cyan]解析结果[/bold cyan]", border_style="cyan"))
    console.print()

    if parsed.name:
        console.print(f"[bold]姓名:[/bold] {parsed.name}")
        console.print()

    # Education
    if parsed.education:
        console.print("[bold yellow]【教育背景】[/bold yellow]")
        for edu in parsed.education:
            line = f"  • {edu.degree}: {edu.school}"
            if edu.major:
                line += f" - {edu.major}"
            if edu.period:
                line += f" ({edu.period})"
            console.print(line)
        console.print()

    # Research experience
    if parsed.research_experience:
        console.print("[bold yellow]【科研经历】[/bold yellow]")
        for exp in parsed.research_experience:
            line = f"  • {exp.title}"
            if exp.organization:
                line += f" @ {exp.organization}"
            if exp.period:
                line += f" ({exp.period})"
            console.print(line)
            if exp.description:
                console.print(f"    {exp.description[:100]}{'...' if len(exp.description) > 100 else ''}")
        console.print()

    # Projects
    if parsed.projects:
        console.print("[bold yellow]【项目经历】[/bold yellow]")
        for proj in parsed.projects:
            console.print(f"  • {proj.name}")
            if proj.description:
                console.print(f"    {proj.description[:100]}{'...' if len(proj.description) > 100 else ''}")
        console.print()

    # Skills
    if parsed.skills:
        console.print("[bold yellow]【技能专长】[/bold yellow]")
        console.print(f"  {', '.join(parsed.skills)}")
        console.print()


def confirm_and_save_profile(
    user: User,
    parsed: ParsedResume,
    title: str,
    source_format: str,
) -> Optional[UserProfile]:
    """Display parsed resume and ask for confirmation before saving.
    
    Args:
        user: User to save profile for.
        parsed: Parsed resume data.
        title: Profile title.
        source_format: Source format (markdown, latex, manual).
        
    Returns:
        Saved UserProfile or None if cancelled.
    """
    display_parsed_resume(parsed)

    if parsed.is_empty():
        console.print("[yellow]警告: 未能从文件中提取到有效信息[/yellow]")
        if not Confirm.ask("是否仍要保存原始内容?", default=False):
            return None

    # Ask for confirmation
    console.print("[bold]请确认以上信息是否正确:[/bold]")
    choice = Prompt.ask(
        "选择操作",
        choices=["y", "n", "e"],
        default="y",
        show_choices=True,
    )

    if choice == "n":
        console.print("[red]已取消保存[/red]")
        return None

    if choice == "e":
        # Interactive edit
        parsed = interactive_edit_resume(parsed)

    # Save to database
    db = get_db()
    with db.session() as session:
        # Deactivate other profiles
        session.query(UserProfile).filter(
            UserProfile.user_id == user.id,
            UserProfile.is_active == True,
        ).update({"is_active": False})

        # Create new profile
        profile = UserProfile(
            user_id=user.id,
            title=title,
            name=parsed.name,
            education=[e.to_dict() for e in parsed.education],
            research_experience=[e.to_dict() for e in parsed.research_experience],
            projects=[p.to_dict() for p in parsed.projects],
            skills=parsed.skills,
            raw_content=parsed.raw_content,
            source_format=source_format,
            is_active=True,
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)
        
        console.print(f"[green]✓ 简历已保存 (ID: {profile.id})[/green]")
        return profile


def interactive_edit_resume(parsed: ParsedResume) -> ParsedResume:
    """Allow user to interactively edit parsed resume."""
    console.print("\n[bold]编辑模式 (直接回车保留原值)[/bold]\n")

    # Edit name
    new_name = Prompt.ask("姓名", default=parsed.name or "")
    if new_name:
        parsed.name = new_name

    # Edit skills
    skills_str = ", ".join(parsed.skills)
    new_skills = Prompt.ask("技能 (逗号分隔)", default=skills_str)
    if new_skills:
        parsed.skills = [s.strip() for s in new_skills.split(",") if s.strip()]

    console.print("\n[dim]教育背景和科研经历的编辑暂不支持，可保存后使用 profile edit 命令修改[/dim]\n")

    return parsed


def display_profile(profile: UserProfile) -> None:
    """Display a user profile."""
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]{profile.title}[/bold cyan] (ID: {profile.id})",
        subtitle=f"{'[green]当前激活[/green]' if profile.is_active else '[dim]未激活[/dim]'}",
        border_style="cyan",
    ))
    console.print()

    if profile.name:
        console.print(f"[bold]姓名:[/bold] {profile.name}")
        console.print()

    # Education
    if profile.education:
        console.print("[bold yellow]【教育背景】[/bold yellow]")
        for edu in profile.education:
            line = f"  • {edu.get('degree', '未知')}: {edu.get('school', '未知')}"
            if edu.get('major'):
                line += f" - {edu['major']}"
            if edu.get('period'):
                line += f" ({edu['period']})"
            console.print(line)
        console.print()

    # Research experience
    if profile.research_experience:
        console.print("[bold yellow]【科研经历】[/bold yellow]")
        for exp in profile.research_experience:
            line = f"  • {exp.get('title', '未知')}"
            if exp.get('organization'):
                line += f" @ {exp['organization']}"
            if exp.get('period'):
                line += f" ({exp['period']})"
            console.print(line)
            if exp.get('description'):
                desc = exp['description']
                console.print(f"    {desc[:100]}{'...' if len(desc) > 100 else ''}")
        console.print()

    # Projects
    if profile.projects:
        console.print("[bold yellow]【项目经历】[/bold yellow]")
        for proj in profile.projects:
            console.print(f"  • {proj.get('name', '未知')}")
            if proj.get('description'):
                desc = proj['description']
                console.print(f"    {desc[:100]}{'...' if len(desc) > 100 else ''}")
        console.print()

    # Skills
    if profile.skills:
        console.print("[bold yellow]【技能专长】[/bold yellow]")
        console.print(f"  {', '.join(profile.skills)}")
        console.print()

    console.print(f"[dim]创建时间: {profile.created_at}[/dim]")
    console.print(f"[dim]更新时间: {profile.updated_at}[/dim]")


def display_professor(professor, show_publications: bool = False) -> None:
    """Display professor information."""
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]{professor.name}[/bold cyan]",
        subtitle=f"ID: {professor.id}",
        border_style="cyan",
    ))
    console.print()

    if professor.affiliation:
        console.print(f"[bold]院系/大学:[/bold] {professor.affiliation}")
    if professor.email:
        console.print(f"[bold]邮箱:[/bold] {professor.email}")
    if professor.homepage:
        console.print(f"[bold]个人主页:[/bold] {professor.homepage}")
    if professor.google_scholar_url:
        console.print(f"[bold]Google Scholar:[/bold] {professor.google_scholar_url}")
    
    console.print()

    if professor.research_interests:
        console.print("[bold yellow]【研究方向】[/bold yellow]")
        console.print(f"  {', '.join(professor.research_interests)}")
        console.print()

    if professor.h_index or professor.total_citations:
        console.print("[bold yellow]【学术指标】[/bold yellow]")
        if professor.h_index:
            console.print(f"  H-Index: {professor.h_index}")
        if professor.total_citations:
            console.print(f"  总引用: {professor.total_citations}")
        console.print()

    if show_publications and professor.publications:
        console.print("[bold yellow]【代表论文】[/bold yellow]")
        for i, pub in enumerate(professor.publications[:10], 1):
            title = pub.get('title', '未知标题')
            year = pub.get('year', '')
            citations = pub.get('citations', 0)
            console.print(f"  {i}. {title}")
            console.print(f"     [dim]年份: {year} | 引用: {citations}[/dim]")
        if len(professor.publications) > 10:
            console.print(f"  [dim]... 还有 {len(professor.publications) - 10} 篇论文[/dim]")
        console.print()

    console.print(f"[dim]更新时间: {professor.updated_at}[/dim]")


def display_professors_table(professors: list) -> None:
    """Display professors in a table."""
    table = Table(title="教授列表")
    table.add_column("ID", style="cyan", width=6)
    table.add_column("姓名", style="bold")
    table.add_column("院系/大学", width=30)
    table.add_column("研究方向", width=40)
    table.add_column("H-Index", justify="right", width=8)

    for prof in professors:
        interests = ", ".join(prof.research_interests[:3]) if prof.research_interests else "-"
        if prof.research_interests and len(prof.research_interests) > 3:
            interests += "..."
        
        table.add_row(
            str(prof.id),
            prof.name,
            prof.affiliation or "-",
            interests,
            str(prof.h_index) if prof.h_index else "-",
        )

    console.print(table)
