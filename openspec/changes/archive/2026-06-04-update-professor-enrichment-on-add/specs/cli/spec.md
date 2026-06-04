## MODIFIED Requirements

### Requirement: Professor Add Command

系统 SHALL 提供 `professor add` 命令，添加教授信息。

#### Scenario: Add by Google Scholar
- **WHEN** 用户执行 `prof-finder professor add --scholar "https://scholar.google.com/citations?user=xxx"`
- **THEN** 系统从 Google Scholar 爬取教授信息
- **AND** 显示爬取结果供用户确认
- **AND** 保存到数据库
- **AND** 保存完成后 SHALL 同步运行与 Web 端一致的 enrichment pipeline（论文摘要上限与画像生成），完成后方可返回提示

#### Scenario: Add manually
- **WHEN** 用户执行 `prof-finder professor add --name "Dr. Smith" --affiliation "Stanford CS"`
- **THEN** 保存基本信息到数据库
- **AND** 提示用户可补充 Google Scholar 链接以获取更多数据
- **AND** SHALL 在保存后同步运行科研画像生成 pipeline（基于已有字段，可为稀疏证据输出）
