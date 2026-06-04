# Prof-Finder

**Your Ideal Professor Awaits.** 帮助大学生寻找未来 PhD/MPhil 导师的智能匹配系统。

Prof-Finder 是一款**在本机运行**的研究生导师匹配助手：简历、教授名单与匹配结果保存在你的电脑上，不上传云端。流程为 **上传简历 → 添加教授 → 智能匹配 → 生成套磁信**（与 Web 侧边栏四步一致）。

## 功能特点

- **智能简历解析**：Markdown / LaTeX，LLM 语义理解，失败时回退正则
- **教授信息获取**：Google Scholar、DBLP、院校爬虫、手动录入
- **语义匹配**：Qwen3 嵌入 + 科研画像文本
- **邮件生成**：DeepSeek API 生成个性化联络信
- **多用户**：本地 SQLite，每用户独立数据
- **Web 界面**：Vue 3 + TypeScript + Naive UI + vue-i18n

## 快速开始（便携版）

1. 在 [GitHub Releases](https://github.com/HungryFlo/prof-finder/releases) 下载对应系统压缩包（Windows / macOS arm64 / Linux）。
2. 解压后运行 `Prof-Finder`（Windows 为 `Prof-Finder.exe`），按引导选择数据目录并登录。
3. 默认账号 `root` / `root123`（**首次登录须改密**），在「设置」中配置 [DeepSeek API Key](https://platform.deepseek.com)。

详细步骤、FAQ 与使用建议见 **[用户使用指南（中文）](docs/user-guide.zh.md)**。英文说明见 **[User Guide (English)](docs/user-guide.en.md)**。解压包内另有 `README-PORTABLE.txt`。

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

**AI、嵌入与解析** — [sentence-transformers](https://www.sbert.net/)、[Hugging Face](https://huggingface.co/) 生态、[ModelScope](https://www.modelscope.cn/)（模型分发）、[Qwen](https://github.com/QwenLM)（[Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)）、[OpenAI Python SDK](https://github.com/openai/openai-python)（兼容 DeepSeek API）、[markdown-it-py](https://github.com/executablebooks/markdown-it-py)、[pylatexenc](https://github.com/phfaist/pylatexenc)

**爬取与内容提取** — [Crawl4AI](https://github.com/unclecode/crawl4ai)、[scholarly](https://github.com/scholarly-python-stack/scholarly)、[Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)、[Requests](https://requests.readthedocs.io/)

**其他** — [NumPy](https://numpy.org/)、[PyYAML](https://pyyaml.org/)、[Rich](https://rich.readthedocs.io/)、[pytest](https://pytest.org/) 等工具链，以及 [DBLP](https://dblp.org/) 提供的公开学术数据。

若我们遗漏了应致谢的项目，欢迎提 Issue 告知。

## License

[MIT License](LICENSE)
