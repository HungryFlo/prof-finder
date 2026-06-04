"""Professor management commands."""

import re
import time
from typing import Optional
import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..db import get_db
from ..models import Professor
from ..crawler import ScholarCrawler, DblpClient
from ..crawler.dblp import extract_dblp_pid_from_url, dblp_profile_url
from ..utils.publication_merge import merge_publications
from ..utils.name_locales import (
    apply_inferred_locales_from_name,
    infer_locales_from_name,
    merge_name_locales,
)
from ..api.task_manager import TaskStatus, create_task, execute_professor_enrichment
from ..api.enrichment_prefs import (
    flags_from_user_settings_row,
    planned_enrichment_step_count_for_professor,
)
from ..api.source_input_service import keep_non_scholar_paper_summaries
from .utils import get_current_user, display_professor, display_professors_table

app = typer.Typer(no_args_is_help=True)
console = Console()


def extract_scholar_id(url_or_id: str) -> Optional[str]:
    """Extract Google Scholar ID from URL or return ID directly."""
    if re.match(r"^[\w-]+$", url_or_id) and len(url_or_id) < 30:
        return url_or_id

    match = re.search(r"user=([^&]+)", url_or_id)
    if match:
        return match.group(1)

    return None


def _cli_run_professor_enrichment(user_id: int, professor_id: int) -> None:
    """Run enrichment pipeline per UserSettings (blocks until done)."""
    from ..models.schema import Professor, UserSettings

    db = get_db()
    with db.session() as session:
        row = session.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        flags = flags_from_user_settings_row(row)
        professor = (
            session.query(Professor)
            .filter(Professor.id == professor_id, Professor.user_id == user_id)
            .first()
        )
        if not professor:
            console.print(f"[red]错误: 未找到教授 ID {professor_id}[/red]")
            return
        planned = planned_enrichment_step_count_for_professor(professor, flags)

    if planned == 0:
        console.print(
            "[yellow]已跳过信息增强（设置中未启用子步或当前数据无可执行步骤）[/yellow]"
        )
        return

    t = create_task("professor-enrichment", "教授信息增强", user_id, total=planned)
    console.print("[cyan]正在执行教授信息增强（可能需要数分钟）...[/cyan]")
    execute_professor_enrichment(t.task_id, professor_id=professor_id)
    state = t
    if state.status == TaskStatus.FAILED:
        console.print(f"[red]增强失败: {state.error_message}[/red]")
        return
    if state.status == TaskStatus.CANCELLED:
        console.print("[yellow]增强已取消[/yellow]")
        return
    console.print("[green]✓ 教授信息增强已完成[/green]")


@app.command("add")
def add_professor(
    scholar: Optional[str] = typer.Option(None, "--scholar", "-s", help="Google Scholar URL or ID"),
    dblp: Optional[str] = typer.Option(None, "--dblp", help="DBLP profile URL or pid"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Professor name (manual add)"),
    affiliation: Optional[str] = typer.Option(None, "--affiliation", "-a", help="Affiliation"),
    user: Optional[str] = typer.Option(None, "--user", "-u", help="Username"),
) -> None:
    """Add a professor to your database."""
    current_user = get_current_user(user)
    db = get_db()

    if scholar and dblp:
        console.print("[red]错误: 请只指定 --scholar 或 --dblp 之一[/red]")
        raise typer.Exit(1)

    if dblp:
        try:
            pid = extract_dblp_pid_from_url(dblp)
        except ValueError:
            console.print("[red]错误: 无效的 DBLP URL 或 pid[/red]")
            raise typer.Exit(1)

        with db.session() as session:
            existing = session.query(Professor).filter(
                Professor.user_id == current_user.id,
                Professor.dblp_pid == pid,
            ).first()
            if existing:
                console.print(f"[yellow]教授 {existing.name} 已存在 (ID: {existing.id})[/yellow]")
                return

        console.print("[cyan]正在从 DBLP 获取信息...[/cyan]")
        client = DblpClient()
        author_data = client.get_author(pid)
        if not author_data:
            console.print("[red]错误: 未找到该 DBLP 作者[/red]")
            raise typer.Exit(1)

        console.print(f"\n[green]✓ {author_data['name']}[/green]")
        console.print(f"  论文数: {len(author_data.get('publications', []))}")
        if not Confirm.ask("\n是否保存?", default=True):
            return

        with db.session() as session:
            professor = Professor(
                user_id=current_user.id,
                name=author_data["name"],
                affiliation=author_data.get("affiliation"),
                dblp_pid=pid,
                dblp_url=author_data.get("dblp_url") or dblp_profile_url(pid),
                publications=merge_publications([], author_data.get("publications", []), "dblp"),
                source="dblp",
            )
            apply_inferred_locales_from_name(professor)
            merge_name_locales(professor, en=author_data.get("name"))
            session.add(professor)
            session.flush()
            prof_id = professor.id
        _cli_run_professor_enrichment(current_user.id, prof_id)
        console.print(f"[green]✓ 已保存教授 (ID: {prof_id})[/green]")
        return

    if scholar:
        # Add from Google Scholar
        scholar_id = extract_scholar_id(scholar)
        if not scholar_id:
            console.print("[red]错误: 无效的 Google Scholar URL 或 ID[/red]")
            console.print("[yellow]示例: https://scholar.google.com/citations?user=xxxxx[/yellow]")
            raise typer.Exit(1)

        # Check if already exists
        with db.session() as session:
            existing = session.query(Professor).filter(
                Professor.user_id == current_user.id,
                Professor.google_scholar_id == scholar_id,
            ).first()
            
            if existing:
                console.print(f"[yellow]教授 {existing.name} 已存在 (ID: {existing.id})[/yellow]")
                if Confirm.ask("是否更新信息?", default=True):
                    _update_professor_from_scholar(session, existing, scholar_id)
                    _cli_run_professor_enrichment(current_user.id, existing.id)
                return

        # Fetch from Scholar
        console.print("[cyan]正在从 Google Scholar 获取信息...[/cyan]")
        
        try:
            crawler = ScholarCrawler()
            author_data = crawler.get_author(scholar_id)
        except Exception as e:
            console.print(f"[red]错误: 无法获取 Google Scholar 数据: {e}[/red]")
            raise typer.Exit(1)

        if not author_data:
            console.print("[red]错误: 未找到该 Scholar ID 对应的作者[/red]")
            raise typer.Exit(1)

        # Display fetched data
        console.print("\n[green]✓ 成功获取教授信息:[/green]")
        console.print(f"  姓名: {author_data.get('name', 'N/A')}")
        console.print(f"  单位: {author_data.get('affiliation', 'N/A')}")
        console.print(f"  研究方向: {', '.join(author_data.get('interests', []))}")
        console.print(f"  H-Index: {author_data.get('h_index', 'N/A')}")
        console.print(f"  总引用: {author_data.get('citations', 'N/A')}")
        console.print(f"  论文数: {len(author_data.get('publications', []))}")

        if not Confirm.ask("\n是否保存?", default=True):
            console.print("[yellow]已取消[/yellow]")
            return

        with db.session() as session:
            professor = Professor(
                user_id=current_user.id,
                name=author_data.get("name", "Unknown"),
                affiliation=author_data.get("affiliation"),
                email=author_data.get("email"),
                homepage=author_data.get("homepage"),
                google_scholar_id=scholar_id,
                google_scholar_url=f"https://scholar.google.com/citations?user={scholar_id}",
                research_interests=author_data.get("interests", []),
                publications=author_data.get("publications", []),
                h_index=author_data.get("h_index"),
                total_citations=author_data.get("citations"),
            )
            apply_inferred_locales_from_name(professor)
            merge_name_locales(professor, en=author_data.get("name"))
            session.add(professor)
            session.flush()
            session.refresh(professor)
            pid = professor.id

            console.print(f"[green]✓ 已添加教授: {professor.name} (ID: {professor.id})[/green]")

        _cli_run_professor_enrichment(current_user.id, pid)

    elif name:
        # Manual add
        with db.session() as session:
            professor = Professor(
                user_id=current_user.id,
                name=name,
                affiliation=affiliation,
            )
            apply_inferred_locales_from_name(professor)
            session.add(professor)
            session.flush()
            session.refresh(professor)
            pid = professor.id

            console.print(f"[green]✓ 已添加教授: {professor.name} (ID: {professor.id})[/green]")
            console.print("[dim]提示: 可以稍后使用 --scholar 选项补充 Google Scholar 数据[/dim]")

        _cli_run_professor_enrichment(current_user.id, pid)

    else:
        console.print("[red]错误: 请提供 --scholar 或 --name 参数[/red]")
        raise typer.Exit(1)


def _update_professor_from_scholar(session, professor: Professor, scholar_id: str) -> None:
    """Update professor data from Google Scholar."""
    console.print("[cyan]正在更新 Google Scholar 数据...[/cyan]")
    
    try:
        crawler = ScholarCrawler()
        author_data = crawler.get_author(scholar_id)
    except Exception as e:
        console.print(f"[red]错误: 无法获取数据: {e}[/red]")
        return

    if not author_data:
        console.print("[red]错误: 未找到数据[/red]")
        return

    from ..utils.name_locales import apply_scholar_name_update

    apply_scholar_name_update(professor, author_data.get("name"))
    from ..utils.profile_merge import apply_external_affiliation

    apply_external_affiliation(professor, author_data.get("affiliation"))
    professor.email = author_data.get("email", professor.email)
    professor.homepage = author_data.get("homepage", professor.homepage)
    professor.research_interests = author_data.get("interests", professor.research_interests)
    professor.publications = author_data.get("publications", professor.publications)
    professor.paper_summaries = keep_non_scholar_paper_summaries(professor.paper_summaries or [])
    professor.h_index = author_data.get("h_index", professor.h_index)
    professor.total_citations = author_data.get("citations", professor.total_citations)

    session.commit()
    console.print(f"[green]✓ 已更新教授信息: {professor.name}[/green]")


@app.command("list")
def list_professors(
    user: Optional[str] = typer.Option(None, "--user", "-u", help="Username"),
) -> None:
    """List all professors in your database."""
    current_user = get_current_user(user)
    db = get_db()

    with db.session() as session:
        professors = session.query(Professor).filter(
            Professor.user_id == current_user.id,
        ).order_by(Professor.name).all()

        if not professors:
            console.print("[yellow]尚未添加任何教授[/yellow]")
            console.print("使用 [cyan]prof-finder professor add --scholar <url>[/cyan] 添加教授")
            return

        display_professors_table(professors)
        console.print(f"\n[dim]共 {len(professors)} 位教授[/dim]")


@app.command("show")
def show_professor(
    professor_id: int = typer.Argument(..., help="Professor ID"),
    publications: bool = typer.Option(False, "--publications", "-p", help="Show publications"),
    user: Optional[str] = typer.Option(None, "--user", "-u", help="Username"),
) -> None:
    """Show professor details."""
    current_user = get_current_user(user)
    db = get_db()

    with db.session() as session:
        professor = session.query(Professor).filter(
            Professor.id == professor_id,
            Professor.user_id == current_user.id,
        ).first()

        if not professor:
            console.print(f"[red]错误: 未找到教授 ID {professor_id}[/red]")
            raise typer.Exit(1)

        display_professor(professor, show_publications=publications)


@app.command("update")
def update_professor(
    professor_id: int = typer.Argument(..., help="Professor ID to update"),
    user: Optional[str] = typer.Option(None, "--user", "-u", help="Username"),
) -> None:
    """Update professor data from Google Scholar."""
    current_user = get_current_user(user)
    db = get_db()

    with db.session() as session:
        professor = session.query(Professor).filter(
            Professor.id == professor_id,
            Professor.user_id == current_user.id,
        ).first()

        if not professor:
            console.print(f"[red]错误: 未找到教授 ID {professor_id}[/red]")
            raise typer.Exit(1)

        if not professor.google_scholar_id:
            console.print("[red]错误: 该教授没有 Google Scholar ID，无法更新[/red]")
            raise typer.Exit(1)

        _update_professor_from_scholar(session, professor, professor.google_scholar_id)
        uid = current_user.id
        pid = professor.id

    _cli_run_professor_enrichment(uid, pid)


@app.command("delete")
def delete_professor(
    professor_id: int = typer.Argument(..., help="Professor ID to delete"),
    user: Optional[str] = typer.Option(None, "--user", "-u", help="Username"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a professor from your database."""
    current_user = get_current_user(user)
    db = get_db()

    with db.session() as session:
        professor = session.query(Professor).filter(
            Professor.id == professor_id,
            Professor.user_id == current_user.id,
        ).first()

        if not professor:
            console.print(f"[red]错误: 未找到教授 ID {professor_id}[/red]")
            raise typer.Exit(1)

        if not force:
            if not Confirm.ask(f"确定要删除教授 '{professor.name}'?", default=False):
                console.print("[yellow]已取消[/yellow]")
                return

        session.delete(professor)
        session.commit()

        console.print(f"[green]✓ 已删除教授: {professor.name}[/green]")


@app.command("backfill-name-locales")
def backfill_name_locales(
    user: Optional[str] = typer.Option(None, "--user", "-u", help="Username"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without saving"),
) -> None:
    """Backfill professor name_locales from name, Scholar, and DBLP (no pinyin)."""
    from ..config import settings as app_settings
    from ..models.schema import UserSettings

    current_user = get_current_user(user)
    db = get_db()

    with db.session() as session:
        settings_row = (
            session.query(UserSettings)
            .filter(UserSettings.user_id == current_user.id)
            .first()
        )
        request_delay = (
            settings_row.request_delay if settings_row and settings_row.request_delay
            else app_settings.request_delay
        )
        professor_ids = [
            p.id
            for p in session.query(Professor)
            .filter(Professor.user_id == current_user.id)
            .order_by(Professor.id)
            .all()
        ]

    if not professor_ids:
        console.print("[yellow]没有教授记录[/yellow]")
        return

    scholar = ScholarCrawler()
    dblp_client = DblpClient()
    stats = {"processed": 0, "zh": 0, "en": 0, "skipped": 0}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        bar = progress.add_task("回填 name_locales...", total=len(professor_ids))
        for prof_id in professor_ids:
            progress.advance(bar)
            with db.session() as session:
                prof = (
                    session.query(Professor)
                    .filter(
                        Professor.id == prof_id,
                        Professor.user_id == current_user.id,
                    )
                    .first()
                )
                if not prof:
                    continue
                locales = prof.name_locales or {}
                had_zh = bool((locales.get("zh") or "").strip())
                had_en = bool((locales.get("en") or "").strip())
                if had_zh and had_en:
                    stats["skipped"] += 1
                    continue

                stats["processed"] += 1
                if dry_run:
                    if not had_zh and infer_locales_from_name(prof.name).get("zh"):
                        stats["zh"] += 1
                    if not had_en and (prof.google_scholar_id or prof.dblp_pid):
                        stats["en"] += 1
                    continue

                if not had_zh and apply_inferred_locales_from_name(prof):
                    if (prof.name_locales or {}).get("zh"):
                        stats["zh"] += 1

                if not (prof.name_locales or {}).get("en") and prof.google_scholar_id:
                    try:
                        author_data = scholar.get_author(prof.google_scholar_id)
                        if author_data and merge_name_locales(
                            prof, en=author_data.get("name")
                        ):
                            stats["en"] += 1
                    except Exception as e:
                        console.print(f"[yellow]Scholar 跳过 {prof.name}: {e}[/yellow]")
                    if request_delay > 0:
                        time.sleep(request_delay)

                if not (prof.name_locales or {}).get("en") and prof.dblp_pid:
                    try:
                        author_data = dblp_client.get_author(prof.dblp_pid)
                        if author_data and merge_name_locales(
                            prof, en=author_data.get("name")
                        ):
                            stats["en"] += 1
                    except Exception as e:
                        console.print(f"[yellow]DBLP 跳过 {prof.name}: {e}[/yellow]")

    prefix = "[dry-run] " if dry_run else ""
    console.print(
        f"{prefix}处理 {stats['processed']} 位；补全 zh {stats['zh']}；"
        f"补全 en {stats['en']}；已齐全跳过 {stats['skipped']}"
    )


