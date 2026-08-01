# Prof-Finder User Guide

[← README](../README.md) · [中文](user-guide.zh.md)

## About

Prof-Finder is a **locally run** assistant for finding PhD/MPhil supervisors. Your resumes, professor lists, and match results stay on your computer — nothing is uploaded to a cloud server.

**Who it's for:** Students preparing graduate school applications who need to organize target supervisors and draft outreach emails.

**What it does:** Capture experiences in an Experience Pool → build an academic profile → add professors → run local semantic matching → generate personalized contact letters. The five steps on the dashboard correspond to this workflow.

## Quick Start (Portable Edition)

1. Download the portable package for your OS from [GitHub Releases](https://github.com/HungryFlo/prof-finder/releases).
2. Extract and run `Prof-Finder` (or `Prof-Finder.exe` on Windows).
3. On first launch, choose a data directory (database, logs, embedding model). The app restarts, then opens your browser.
4. Log in with `root` / `root123`, then change your password on first login.
5. Go to **Settings** and configure your LLM API (type, key, base URL, model name).

See `README-PORTABLE.txt` inside the extracted package for portable-specific instructions.

**Install config:** Paths are stored in `install.json` next to the executable.

**Uninstall:** Close the app, run `uninstall-prof-finder.bat` (Windows) or `./uninstall-prof-finder.sh` (macOS), type `DELETE` to confirm.

## Recommended Workflow

1. **Log in** — Use default credentials, then set a new password.
2. **Configure LLM API** — Settings → choose API type, key, base URL, and model → Save.
3. **Capture experiences** — Experience Pools → brainstorm, cluster (manual board), and detail academic-related stories; compose writing snippets and optionally apply them to a profile (binds the pool).
4. **Build a profile** — Student Profiles → **Create** → upload materials (`.md`, `.tex`, `.txt`) and/or enter text; optionally bind an experience pool. Enable LLM extraction; refine further with AI chat. Activate one profile for matching.
5. **Add professors** — Professors → Add via Google Scholar URL, DBLP URL, **university faculty-list crawl** (paste a list page URL; extract with LLM or CSS selectors), or manual entry. For existing rows, use **Refresh external profiles** (or link Scholar/DBLP on the detail page). Track progress in the top-bar **task panel**.
6. **Run matching** — Match Results → on first use, download **Qwen/Qwen3-Embedding-0.6B** from ModelScope (~1.2 GB; requires access to `www.modelscope.cn`) → Run Match.
7. **Generate letters** — Choose letter language (中文 / English) → open a professor from match results → Generate letter (uses detailed stories from the bound pool when available) → **Review and edit before sending**.

Click **Help** in the top-right corner of the app for the full in-app guide.

## How to Configure an LLM API

Prof-Finder supports two API styles; you choose the provider, base URL, and model name in Settings:

| API type | Example providers | Base URL example | Model example |
|----------|-------------------|------------------|---------------|
| OpenAI-compatible | [DeepSeek](https://platform.deepseek.com), OpenAI, Ollama | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Anthropic | [Anthropic](https://console.anthropic.com) or compatible gateways | `https://api.anthropic.com` | `claude-sonnet-4-20250514` |

1. Create an API key in your provider console (**shown only once** — save it immediately).
2. In Prof-Finder **Settings**, enter API type, key, base URL, and model name, then save.
3. Monitor usage and balance. Do not share your key.

Features that require LLM API: profile generation / field extraction, experience-pool draft composition, professor profiles, paper summaries, contact letters, profile AI chat, and LLM-mode university list extraction.

## Best Practices

- Capture and detail experiences in a pool before matching and letter writing when possible.
- Complete your profile before running matches — richer data yields better results.
- Google Scholar and DBLP complement each other; university crawls depend on site structure.
- Ensure one profile is active and you have at least one professor before matching.
- Always review AI-generated emails before sending.
- Default request delay is 3 seconds; increase it if Scholar crawling fails frequently.
- Professor auto-enrichment toggles in Settings (publication details, paper summaries, research profiles) consume API credits — disable if not needed.

## FAQ

| Question | Answer |
|----------|--------|
| Where is my data stored? | Chosen during first-run setup; path is stored in `install.json` next to the executable. Deleting the extracted folder does **not** remove your chosen data directory. |
| Port already in use | Close other Prof-Finder instances or restart your computer. |
| Browser didn't open | Manually visit the local URL shown in the terminal/console. |
| Match button disabled | Download the embedding model first; ensure an active profile and at least one professor exist. |
| Scholar crawl failed | Check your network; increase request delay in Settings; retry later. |
| Embedding model download failed | Ensure `www.modelscope.cn` is reachable; run `bash scripts/check_modelscope.sh`; check disk space in your data directory. |
| How to fully uninstall? | Close the app, run the uninstall script in the package, type `DELETE` to confirm. |
| LLM features not working | Verify LLM API type, key, base URL, and model name in Settings, and check account balance. |
| Task shows “Interrupted” | The app exited while the task was running. In the task panel, choose **Resume** to continue from the last progress, or **Discard**. |
