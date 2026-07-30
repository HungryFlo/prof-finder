# Prof-Finder

**Your Ideal Professor Awaits.** 帮助大学生寻找未来 PhD/MPhil 导师的智能匹配系统。

Prof-Finder 是一款**在本机运行**的研究生导师匹配助手：简历、教授名单与匹配结果保存在你的电脑上，不上传云端。流程为 **沉淀经历 → 建立画像 → 添加教授 → 智能匹配 → 生成套磁信**（与应用内工作台五步一致）。

## 功能特点

- **信息池**：脑暴、聚类、细化学术相关经历，取材生成文书片段并可绑定到画像
- **智能简历解析**：Markdown / LaTeX，LLM 语义理解；支持画像 AI 对话打磨
- **教授信息获取**：Google Scholar、DBLP、院校爬虫、外部档案关联、手动录入
- **语义匹配**：Qwen3 嵌入 + 科研画像文本
- **邮件生成**：可配置 LLM API（OpenAI 兼容或 Anthropic），结合画像与信息池经历生成个性化联络信
- **多用户**：本地 SQLite，每用户独立数据
- **Web 界面**：Vue 3 + TypeScript + Naive UI + vue-i18n

## 快速开始（便携版）

1. 在 [GitHub Releases](https://github.com/HungryFlo/prof-finder/releases) 下载对应系统压缩包（Windows / macOS arm64）。
2. 解压后运行 `Prof-Finder`（Windows 为 `Prof-Finder.exe`），按引导选择数据目录并登录。
3. 默认账号 `root` / `root123`（**首次登录须改密**），在「设置」中配置 LLM API（类型、Key、Base URL、模型名）。

详细步骤、FAQ 与使用建议见 **[用户使用指南（中文）](docs/user-guide.zh.md)**。英文说明见 **[User Guide (English)](docs/user-guide.en.md)**。解压包内另有 `README-PORTABLE.txt`。

## 干净卸载

Prof-Finder 便携版**无需安装程序、不写注册表、不往系统目录散落文件**——解压即用，用完可彻底清走。

首次启动选择数据目录后，便携包内的卸载脚本会自动记录你的**应用目录、数据目录与嵌入模型目录**（见 `install.json`）。一键卸载时会一并删除这三处，不会留下 SQLite 数据库、下载的模型或配置文件。

1. **关闭**所有 Prof-Finder 窗口。
2. 在解压目录运行卸载脚本：
   - **Windows**：`uninstall-prof-finder.bat`
   - **macOS / Linux**：`./uninstall-prof-finder.sh`
3. 按提示输入 `DELETE` 确认（输入其他内容则取消）。

> **注意**：仅删除解压文件夹**不会**清除你在首次启动时自选的数据目录；要彻底移除，请使用上述卸载脚本。该操作不可恢复。

## 文档

| 文档 | 说明 |
|------|------|
| [用户使用指南（中文）](docs/user-guide.zh.md) | 完整操作流程、API Key、FAQ |
| [User Guide (English)](docs/user-guide.en.md) | English user documentation |
| [开发者文档](docs/development.zh.md) | 源码安装、配置、CLI、测试与打包 |
| [OpenSpec 规格](openspec/) | 功能需求与变更归档 |

## 参与开发

```bash
git clone https://github.com/HungryFlo/prof-finder.git
cd prof-finder
conda activate prof-finder
poetry install && cd frontend && npm install && cd ..
cp .env.example .env
```

参见 [开发者文档](docs/development.zh.md)。

## 致谢

Prof-Finder 建立在众多优秀的开源项目之上，特此感谢（排名不分先后）：

**Web 与界面** — [Vue.js](https://vuejs.org/)、[Vite](https://vite.dev/)、[Naive UI](https://www.naiveui.com/)、[Tailwind CSS](https://tailwindcss.com/)、[Reka UI](https://reka-ui.com/) / [shadcn-vue](https://www.shadcn-vue.com/)、[Pinia](https://pinia.vuejs.org/)、[Vue Router](https://router.vuejs.org/)、[vue-i18n](https://vue-i18n.intlify.dev/)、[Axios](https://axios-http.com/)

**后端与数据** — [FastAPI](https://fastapi.tiangolo.com/)、[Uvicorn](https://www.uvicorn.org/)、[SQLAlchemy](https://www.sqlalchemy.org/)、[Typer](https://typer.tiangolo.com/)、[Huey](https://huey.readthedocs.io/)、[Pydantic](https://docs.pydantic.dev/)（经 FastAPI 使用）

**AI、嵌入与解析** — [sentence-transformers](https://www.sbert.net/)、[Hugging Face](https://huggingface.co/) 生态、[ModelScope](https://www.modelscope.cn/)（模型分发）、[Qwen](https://github.com/QwenLM)（[Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)）、[OpenAI Python SDK](https://github.com/openai/openai-python)（OpenAI 兼容 API）、[Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python)、[markdown-it-py](https://github.com/executablebooks/markdown-it-py)、[pylatexenc](https://github.com/phfaist/pylatexenc)

**爬取与内容提取** — [Crawl4AI](https://github.com/unclecode/crawl4ai)、[scholarly](https://github.com/scholarly-python-stack/scholarly)、[Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)、[Requests](https://requests.readthedocs.io/)

**其他** — [NumPy](https://numpy.org/)、[PyYAML](https://pyyaml.org/)、[Rich](https://rich.readthedocs.io/)、[pytest](https://pytest.org/) 等工具链，以及 [DBLP](https://dblp.org/) 提供的公开学术数据。

若我们遗漏了应致谢的项目，欢迎提 Issue 告知。

## License

Prof-Finder is released under the [MIT License](LICENSE).

Third-party components (Python, frontend, runtime models, and external services) are listed in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Portable release archives include the same
`LICENSE` and `THIRD_PARTY_NOTICES.md` files.

To refresh the notices after dependency changes:

```bash
python scripts/generate_third_party_notices.py
```
