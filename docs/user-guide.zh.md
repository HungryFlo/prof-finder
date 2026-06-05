# Prof-Finder 用户使用指南

[← 返回 README](../README.md) · [English](user-guide.en.md)

## 从零开始

### 第一步：首次配置、启动并登录

1. 解压便携包到固定目录，运行 `Prof-Finder`（Windows 为 `Prof-Finder.exe`）。
2. 首次启动会自动打开**首次运行配置**页面；选择数据存储目录（模型将保存在其下的 `models` 子目录），完成后应用会自动重启。
3. 重启后使用默认账号 `root` / `root123` 登录。
4. 首次登录会强制要求修改密码，请设置一个安全的新密码。

**macOS 提示：** 若系统提示「无法验证开发者」，请前往「系统设置 → 隐私与安全性」，允许运行该应用。

### 第二步：配置 LLM API

1. 登录后点击左侧「设置」。
2. 在「LLM API 配置」卡片中选择 API 类型（OpenAI 兼容或 Anthropic），填写 API Key、Base URL 与模型名称，点击「保存设置」。

以下功能需要 API Key 才能使用：

- 简历 LLM 智能解析
- 教授科研画像与论文摘要生成
- 套磁邮件生成
- 画像 AI 聊天优化

详见下方「如何配置 LLM API」。

### 第三步：建立学生画像

1. 点击左侧「学生画像」→「上传简历」。
2. 选择 `.md`、`.tex`、`.txt` 等格式的简历文件。
3. 建议开启 LLM 自动提取，系统会解析研究方向、技能、教育经历等字段。
4. 上传后可在详情页手动编辑或完善信息。
5. 确保至少有一个画像处于「已激活」状态（匹配时使用激活的画像）。

### 第四步：添加教授

1. 点击左侧「教授」→「添加教授」。
2. 推荐方式（按稳定性排序）：
   - **Google Scholar 链接**：粘贴教授 Scholar 主页 URL（引用指标、论文摘要等）。
   - **DBLP 链接**：粘贴 `https://dblp.org/pid/...` 作者主页，稳定获取 CS 论文列表（Scholar 不可用时推荐）。
   - **关联外部档案**：对已导入的教授一键同时搜索 Scholar 与 DBLP，数据合并到同一档案。
   - **院校批量爬取**：选择目标院校，后台自动导入教授列表（完成后自动启动 Scholar + DBLP 匹配）。
   - **手动添加**：填写姓名、单位等基本信息。
3. 添加过程在后台运行，可通过右下角「任务面板」查看进度。

### 第五步：运行匹配

1. 点击左侧「匹配结果」。
2. 首次使用需从 [ModelScope](https://www.modelscope.cn/models/Qwen/Qwen3-Embedding-0.6B) 下载嵌入模型 **Qwen/Qwen3-Embedding-0.6B**（约 1.2 GB，需能访问 `www.modelscope.cn`；保存于数据目录下 `models/qwen3-embedding-0.6b`，下载完成后自动启用）。可用 `bash scripts/check_modelscope.sh` 自检网络。
3. 确认已有激活画像和至少一位教授后，点击「运行匹配」。
4. 匹配完成后，按匹配度排序的教授列表会显示在页面上。

### 第六步：生成套磁邮件

1. 在匹配结果页点击某位教授，打开详情弹窗。
2. 点击「生成邮件」，系统会根据你的画像和教授信息生成个性化套磁信。
3. **务必人工审阅后再发送**，可根据需要编辑内容。

应用内也可点击右上角「使用帮助」查看完整指南。

## 便携版补充说明

在 [GitHub Releases](https://github.com/HungryFlo/prof-finder/releases) 下载与你系统匹配的便携包后：

- 解压并运行 `Prof-Finder` / `Prof-Finder.exe`；不要求安装 Python、Node.js、Poetry 或 npm。
- 解压包内附有 `README-PORTABLE.txt`，含便携版专用说明。
- 首次启动需选择数据存储目录；配置保存在解压目录旁的 `install.json`。
- 卸载：关闭应用后运行 `uninstall-prof-finder.bat`（Windows）或 `./uninstall-prof-finder.sh`（macOS/Linux），输入 `DELETE` 确认。

## 如何配置 LLM API

Prof-Finder 支持两类接口，由你在设置中自行选择服务商、Base URL 与模型名：

| API 类型 | 适用服务示例 | Base URL 示例 | 模型名示例 |
|----------|--------------|---------------|------------|
| OpenAI 兼容 | [DeepSeek](https://platform.deepseek.com)、OpenAI、Ollama 等 | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Anthropic | [Anthropic](https://console.anthropic.com) 或兼容网关 | `https://api.anthropic.com` | `claude-sonnet-4-20250514` |

1. 在服务商控制台创建 API Key（**只显示一次**，请立即保存）。
2. 在 Prof-Finder「设置」中填写 API 类型、Key、Base URL、模型名称并保存。
3. 关注账户余额与用量；请勿将密钥分享给他人。

## 使用建议

- **先完善画像再匹配**：研究方向、技能、经历越完整，匹配结果越准确。
- **教授来源**：Scholar 与 DBLP 互补——Scholar 提供引用与 h-index，DBLP 官方 API 提供稳定的 CS 书目；院校批量爬取受网站结构影响，可能不完整。
- **匹配前检查**：确保已激活一个画像，且教授列表不为空。
- **套磁信审阅**：AI 生成的邮件仅供参考，发送前请仔细修改。
- **请求延时**：默认 3 秒，用于控制 Scholar 爬取频率；若频繁失败可适当增大。
- **自动增强开关**：「设置」中的教授自动增强（论文摘要、科研画像等）会消耗 API 额度，可按需关闭。

## 常见问题

| 问题 | 解决方法 |
|------|----------|
| 数据存在哪里？ | 首次启动时自选目录；路径记录在程序目录下的 `install.json`。删除解压文件夹不会清除已选数据目录中的内容。 |
| 端口被占用 | 关闭其他 Prof-Finder 实例，或重启电脑后再试。 |
| 浏览器未自动打开 | 手动访问终端/控制台输出的本地地址。 |
| 匹配按钮无法点击 | 先下载嵌入模型；确保有已激活的画像和至少一位教授。 |
| Scholar 爬取失败 | 检查网络连接；在「设置」中增大请求延时；稍后重试。 |
| 嵌入模型下载失败 | 确认能访问 `www.modelscope.cn`；运行 `bash scripts/check_modelscope.sh` 排查代理/DNS；便携版检查数据目录磁盘空间。 |
| 如何彻底卸载？ | 关闭应用后运行便携包内的卸载脚本，输入 `DELETE` 确认。仅删除解压文件夹不会清除用户数据。 |
| LLM 功能不可用 | 检查「设置」中是否已配置 DeepSeek API Key，且账户有余额。 |
