## MODIFIED Requirements

### Requirement: Professor Add Command

系统 SHALL 提供 `professor add` 命令，添加教授信息。

#### Scenario: Add by Google Scholar
- **WHEN** 用户执行 `prof-finder professor add --scholar "https://scholar.google.com/citations?user=xxx"`
- **THEN** 系统从 Google Scholar 爬取教授信息
- **AND** 显示爬取结果供用户确认
- **AND** 保存到数据库
- **AND** 若当前用户的 UserSettings 中至少有一个自动 enrichment 子步开启且计划子步数大于 0，则在保存后同步运行对应子步（阻塞至完成）；否则跳过并提示无需自动增强

#### Scenario: Add manually
- **WHEN** 用户执行 `prof-finder professor add --name "Dr. Smith" --affiliation "Stanford CS"`
- **THEN** 保存基本信息到数据库
- **AND** 提示用户可补充 Google Scholar 链接以获取更多数据
- **AND** 按用户设置执行计划内的自动 enrichment 子步或跳过
