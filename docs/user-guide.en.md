# Prof-Finder User Guide

[← README](../README.md) · [中文](user-guide.zh.md)

## About

Prof-Finder is a **locally run** assistant for finding PhD/MPhil supervisors. Your resumes, professor lists, and match results stay on your computer — nothing is uploaded to a cloud server.

**Who it's for:** Students preparing graduate school applications who need to organize target supervisors and draft outreach emails.

**What it does:** Upload your resume to build an academic profile → add professors → get smart match recommendations → generate personalized contact letters. The four steps in the sidebar and dashboard correspond to this workflow.

## Quick Start (Portable Edition)

1. Download the portable package for your OS from [GitHub Releases](https://github.com/HungryFlo/prof-finder/releases).
2. Extract and run `Prof-Finder` (or `Prof-Finder.exe` on Windows).
3. The app starts a local server and opens your browser automatically.
4. Log in with `root` / `root123`, then change your password on first login.
5. Go to **Settings** and enter your DeepSeek API Key.

See `README-PORTABLE.txt` inside the extracted package for portable-specific instructions.

**First run:** Choose a data directory (database, logs, embedding model). Settings are stored in `install.json` next to the executable.

**Uninstall:** Close the app, run `uninstall-prof-finder.bat` (Windows) or `./uninstall-prof-finder.sh` (macOS/Linux), type `DELETE` to confirm.

## Recommended Workflow

1. **Log in** — Use default credentials, then set a new password.
2. **Configure API Key** — Settings → paste your DeepSeek API Key → Save.
3. **Build a profile** — Student Profiles → Upload resume (`.md`, `.tex`, `.txt`). Enable LLM extraction. Activate one profile for matching.
4. **Add professors** — Professors → Add via Google Scholar URL (recommended), DBLP URL, university batch crawl, external profile linking, or manual entry. Track progress in the task panel.
5. **Run matching** — Match Results → on first use, download **Qwen/Qwen3-Embedding-0.6B** from ModelScope (~1.2 GB; requires access to `www.modelscope.cn`) → Run Match.
6. **Generate letters** — Open a professor from match results → Generate letter → **Review and edit before sending**.

Click **Help** in the top-right corner of the app for the full in-app guide.

## How to Get a DeepSeek API Key

1. Visit [DeepSeek Platform](https://platform.deepseek.com) and sign up or log in.
2. Go to **API Keys** and create a new key.
3. Copy the key (`sk-...`). **It is shown only once** — save it immediately.
4. Paste it in Prof-Finder under **Settings → New API Key** and save.
5. Top up your DeepSeek account as needed. Do not share your key.

Features that require an API Key: resume LLM parsing, professor research profiles, paper summaries, contact letter generation, and profile AI chat.

## Best Practices

- Complete your profile before running matches — richer data yields better results.
- Google Scholar and DBLP complement each other; university crawls depend on site structure.
- Ensure one profile is active and you have at least one professor before matching.
- Always review AI-generated emails before sending.
- Default request delay is 3 seconds; increase it if Scholar crawling fails frequently.
- Professor auto-enrichment toggles in Settings consume API credits — disable if not needed.

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
| LLM features not working | Verify your DeepSeek API Key in Settings and check account balance. |
