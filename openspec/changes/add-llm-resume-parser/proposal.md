# Change: 使用 LLM API 增强简历解析

## Why

当前基于正则表达式的简历解析器（LaTeX/Markdown）对非标准格式的简历效果较差，无法理解语义上下文，导致解析准确率不足。使用 LLM API 进行信息提取可以显著提高解析质量，更好地理解简历内容的语义。

## What Changes

- 新增 LLM 简历解析器，使用 DeepSeek API 进行智能信息提取
- 新增 `src/prof_finder/prompts/` 目录，统一管理项目中的 prompt 模板
- 保留现有正则解析器作为 fallback 方案
- 修改解析流程：优先使用 LLM 解析，失败时回退到正则解析

## Impact

- Affected specs: `resume-parser`
- Affected code:
  - `src/prof_finder/parser/` - 新增 LLM 解析器
  - `src/prof_finder/prompts/` - 新增 prompt 管理模块
  - `src/prof_finder/cli/profile.py` - 修改解析流程
