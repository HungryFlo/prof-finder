"""Build a portable Prof-Finder archive for the current platform."""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
FRONTEND_DIR = REPO_ROOT / "frontend"
PYINSTALLER_DIST = REPO_ROOT / "build" / "pyinstaller-dist"
PYINSTALLER_WORK = REPO_ROOT / "build" / "pyinstaller-work"
PORTABLE_DIST = REPO_ROOT / "dist" / "portable"


def run(command: list[str], cwd: Path = REPO_ROOT) -> None:
    print(f"+ {' '.join(command)}")
    subprocess.run(command, cwd=cwd, check=True)


def npm_command(*args: str) -> list[str]:
    """Return an npm command that works with Windows GitHub runners."""
    executable = "npm.cmd" if sys.platform == "win32" else "npm"
    return [executable, *args]


def normalize_platform_tag() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()

    arch = {
        "amd64": "x64",
        "x86_64": "x64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }.get(machine, machine)

    os_name = {
        "darwin": "macos",
        "windows": "windows",
        "linux": "linux",
    }.get(system, system)

    return f"{os_name}-{arch}"


def build_frontend(skip_install: bool) -> None:
    if not skip_install:
        run(npm_command("ci"), cwd=FRONTEND_DIR)
    run(npm_command("run", "build"), cwd=FRONTEND_DIR)


def build_executable() -> Path:
    if PYINSTALLER_DIST.exists():
        shutil.rmtree(PYINSTALLER_DIST)
    if PYINSTALLER_WORK.exists():
        shutil.rmtree(PYINSTALLER_WORK)

    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            "--distpath",
            str(PYINSTALLER_DIST),
            "--workpath",
            str(PYINSTALLER_WORK),
            str(REPO_ROOT / "packaging" / "prof-finder.spec"),
        ]
    )

    executable_name = "Prof-Finder.exe" if sys.platform == "win32" else "Prof-Finder"
    onefile_executable = PYINSTALLER_DIST / executable_name
    onedir_executable = PYINSTALLER_DIST / "Prof-Finder" / executable_name

    if onefile_executable.is_file():
        executable = onefile_executable
    elif onedir_executable.is_file():
        executable = onedir_executable
    else:
        raise FileNotFoundError(
            "Expected PyInstaller output not found. Checked "
            f"{onefile_executable} and {onedir_executable}"
        )
    return executable


def write_portable_readme(target_dir: Path) -> None:
    (target_dir / "README-PORTABLE.txt").write_text(
        """Prof-Finder 便携版用户指南
==========================

【项目简介】

Prof-Finder 是一款在本机运行的研究生导师匹配助手。你的简历、教授名单和匹配结果
都保存在自己的电脑上，不会上传到云端。

适合正在准备 PhD 或 MPhil 申请、需要整理目标导师名单并撰写套磁信的同学使用。

【快速开始】

  - Windows: 双击 Prof-Finder.exe
  - macOS / Linux: 在终端运行 ./Prof-Finder

程序启动后会自动打开浏览器。若未自动打开，请查看终端输出的本地地址。

默认管理员账号:
  用户名: root
  密码: root123（首次登录需修改）

便携版不要求安装 Python、Node.js 等开发工具。
首次启动会在浏览器中引导选择数据存储目录；配置保存在本目录下的 install.json。

【推荐使用流程】

1. 首次配置并登录
   首次运行选择数据目录（模型保存在其 models 子目录），完成后自动重启。
   使用 root / root123 登录，首次登录强制修改密码。
   macOS 若提示无法验证开发者，请前往「系统设置 → 隐私与安全性」允许运行。

2. 配置 DeepSeek API Key
   点击左侧「设置」，在「API 配置」中填写 API Key 并保存。
   详见下方「如何获取 DeepSeek API Key」。

3. 建立学生画像
   「学生画像」→ 上传简历（支持 .md、.tex、.txt 等）。
   建议开启 LLM 自动提取。确保至少有一个画像处于「已激活」状态。

4. 添加教授
   「教授」→ 添加教授。推荐通过 Google Scholar 链接添加。
   也可使用院校批量爬取或手动添加。进度可在右下角任务面板查看。

5. 运行匹配
   「匹配结果」→ 首次使用需下载约 400 MB 嵌入模型（需联网）。
   确认有激活画像和至少一位教授后，点击「运行匹配」。

6. 生成套磁邮件
   在匹配结果中打开教授详情 → 生成邮件。
   务必人工审阅后再发送。

应用内也可点击右上角「使用帮助」查看完整指南。

【如何获取 DeepSeek API Key】

1. 打开 https://platform.deepseek.com ，注册或登录。
2. 进入「API Keys」，创建新密钥。
3. 复制 sk-... 格式的密钥（只显示一次，请立即保存）。
4. 在 Prof-Finder「设置 → 新 API Key」中粘贴并保存。
5. 在 DeepSeek 平台充值或关注用量，勿将密钥分享给他人。

以下功能需要 API Key: 简历 LLM 解析、教授科研画像、论文摘要、套磁邮件、画像 AI 聊天。

【数据存储位置】

  首次启动时在向导中选择；路径记录在 install.json（与本程序同目录）。
  删除解压文件夹不会清除已选数据目录中的内容。

【使用建议】

- 先完善画像再匹配，研究方向和技能越完整，匹配越准确。
- Google Scholar 链接是最稳定的教授来源。
- 匹配前确保已激活一个画像，且教授列表不为空。
- 套磁信生成后务必人工审阅再发送。
- 请求延时默认 3 秒，Scholar 爬取失败时可适当增大。
- 「设置」中的教授自动增强会消耗 API 额度，可按需关闭。

【常见问题】

问: 端口被占用怎么办？
答: 关闭其他 Prof-Finder 实例，或重启电脑。

问: 匹配按钮无法点击？
答: 先下载嵌入模型；确保有已激活画像和至少一位教授。

问: Scholar 爬取失败？
答: 检查网络；增大请求延时；稍后重试。

问: LLM 功能不可用？
答: 检查「设置」中是否已配置 DeepSeek API Key，且账户有余额。

【卸载说明】

  - Windows: 关闭 Prof-Finder，运行 uninstall-prof-finder.bat
  - macOS / Linux: 关闭 Prof-Finder，运行 ./uninstall-prof-finder.sh

卸载脚本会要求输入 DELETE 确认，然后删除配置的数据目录、模型目录并移除本解压文件夹。
该操作不可恢复。仅删除解压文件夹不会清除用户数据。


================================================================================
English User Guide
================================================================================

About
-----

Prof-Finder is a locally run assistant for finding PhD/MPhil supervisors. Your data
stays on your computer — nothing is uploaded to a cloud server.

It is designed for students preparing graduate school applications who need to
organize target supervisors and draft outreach emails.

Quick Start
-----------

  - Windows: double-click Prof-Finder.exe
  - macOS / Linux: run ./Prof-Finder

The app starts a local server and opens your browser automatically.
If the browser does not open, check the local URL printed in the terminal.

Default admin account:
  username: root
  password: root123 (must be changed on first login)

No Python, Node.js, or other dev tools are required.
On first launch, a setup wizard lets you choose where data and models are stored.
The choice is saved in install.json next to this executable.

Recommended Workflow
--------------------

1. First-run setup and log in
   On first launch, pick a data folder (models go in a models subfolder), then the app restarts.
   Log in with root / root123, then set a new password.
   On macOS, if blocked by Gatekeeper, allow the app in System Settings → Privacy & Security.

2. Configure DeepSeek API Key
   Go to Settings → API Configuration, enter your API Key, and save.
   See "How to Get a DeepSeek API Key" below.

3. Build a student profile
   Student Profiles → Upload resume (.md, .tex, .txt, etc.).
   Enable LLM extraction. Activate at least one profile for matching.

4. Add professors
   Professors → Add professor. Google Scholar URL is recommended.
   You can also use university batch crawl or manual entry.
   Track progress in the task panel (bottom-right corner).

5. Run matching
   Match Results → download the embedding model on first use (~400 MB, internet required).
   Ensure an active profile and at least one professor exist, then click Run Match.

6. Generate contact letters
   Open a professor from match results → Generate letter.
   Always review and edit before sending.

Click Help in the top-right corner of the app for the full in-app guide.

How to Get a DeepSeek API Key
-----------------------------

1. Visit https://platform.deepseek.com and sign up or log in.
2. Go to API Keys and create a new key.
3. Copy the key (sk-... format). It is shown only once — save it immediately.
4. Paste it in Prof-Finder under Settings → New API Key and save.
5. Top up your DeepSeek account as needed. Do not share your key.

Features requiring an API Key: resume LLM parsing, professor research profiles,
paper summaries, contact letters, and profile AI chat.

Data Storage Locations
----------------------

  Chosen during first-run setup; recorded in install.json (beside this executable).
  Deleting this extracted folder does NOT remove your chosen data directory.

Best Practices
--------------

- Complete your profile before matching — richer data yields better results.
- Google Scholar URLs are the most reliable professor source.
- Ensure one profile is active and you have at least one professor before matching.
- Always review AI-generated emails before sending.
- Default request delay is 3 seconds; increase if Scholar crawling fails.
- Professor auto-enrichment toggles in Settings consume API credits — disable if not needed.

FAQ
---

Q: Port already in use?
A: Close other Prof-Finder instances or restart your computer.

Q: Match button disabled?
A: Download the embedding model first; ensure an active profile and at least one professor.

Q: Scholar crawl failed?
A: Check your network; increase request delay in Settings; retry later.

Q: LLM features not working?
A: Verify your DeepSeek API Key in Settings and check account balance.

Uninstall
---------

  - Windows: close Prof-Finder, then run uninstall-prof-finder.bat
  - macOS / Linux: close Prof-Finder, then run ./uninstall-prof-finder.sh

The uninstall script asks you to type DELETE, then removes your data folder, model folder, and this app folder.
This action is irreversible. Deleting the extracted folder alone does NOT remove user data.
""",
        encoding="utf-8",
    )


def write_uninstall_script(target_dir: Path, platform_tag: str) -> None:
    """Write a platform-specific destructive uninstall script into the package."""
    from prof_finder.packaging.uninstall import write_placeholder_uninstall

    write_placeholder_uninstall(target_dir, platform_tag)


def create_archive(executable: Path, platform_tag: str) -> Path:
    package_name = f"Prof-Finder-{platform_tag}"
    staging_dir = PORTABLE_DIST / package_name
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    bundle_dir = executable.parent if executable.parent.parent == PYINSTALLER_DIST else None
    if bundle_dir:
        for item in bundle_dir.iterdir():
            target = staging_dir / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
    else:
        shutil.copy2(executable, staging_dir / executable.name)
    write_portable_readme(staging_dir)
    write_uninstall_script(staging_dir, platform_tag)

    archive_format = "gztar" if platform_tag.startswith("linux-") else "zip"
    archive_base = PORTABLE_DIST / package_name
    archive_path = shutil.make_archive(str(archive_base), archive_format, staging_dir)
    return Path(archive_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Prof-Finder portable package.")
    parser.add_argument("--platform-tag", default=normalize_platform_tag())
    parser.add_argument("--skip-npm-install", action="store_true")
    parser.add_argument("--skip-frontend", action="store_true")
    args = parser.parse_args()

    if not args.skip_frontend:
        build_frontend(skip_install=args.skip_npm_install)
    elif not (FRONTEND_DIR / "dist" / "index.html").exists():
        raise FileNotFoundError("frontend/dist/index.html is required when --skip-frontend is used")

    executable = build_executable()
    archive_path = create_archive(executable, args.platform_tag)
    print(f"Created portable archive: {archive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
