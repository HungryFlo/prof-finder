# Tasks: Add LLM Resume Parser

## 1. Prompt 管理模块

- [x] 1.1 创建 `src/prof_finder/prompts/` 目录结构
- [x] 1.2 实现 prompt 加载工具 (`prompts/__init__.py`)
  - [x] 1.2.1 `load_prompt(name: str, **kwargs) -> str` 函数
  - [x] 1.2.2 支持 YAML 文件中的变量替换
- [x] 1.3 创建简历解析 prompt 模板 (`prompts/resume_parser.yaml`)
  - [x] 1.3.1 System prompt：定义角色和任务
  - [x] 1.3.2 User prompt：输入格式和输出要求
  - [x] 1.3.3 包含 JSON Schema 示例

## 2. LLM 简历解析器

- [x] 2.1 创建 `src/prof_finder/parser/llm_parser.py`
  - [x] 2.1.1 实现 `LLMParser` 类，继承 `BaseParser` 接口
  - [x] 2.1.2 实现 `parse(content: str) -> ParsedResume` 方法
  - [x] 2.1.3 实现 JSON 响应解析和转换为 `ParsedResume`
- [x] 2.2 实现错误处理逻辑
  - [x] 2.2.1 API 调用重试机制
  - [x] 2.2.2 JSON 解析错误处理
  - [x] 2.2.3 空结果处理

## 3. 解析流程整合

- [x] 3.1 创建 `src/prof_finder/parser/smart_parser.py`
  - [x] 3.1.1 实现 `SmartParser` 类，封装 LLM + 正则 fallback 逻辑
  - [x] 3.1.2 根据文件扩展名选择合适的正则解析器作为 fallback
- [x] 3.2 修改 `src/prof_finder/cli/profile.py`
  - [x] 3.2.1 使用 `SmartParser` 替换直接调用正则解析器
  - [x] 3.2.2 添加解析方式提示（LLM/正则）

## 4. 测试

- [x] 4.1 编写 LLM 解析器单元测试
  - [x] 4.1.1 Mock API 调用测试解析逻辑
  - [x] 4.1.2 测试 JSON 解析和转换
  - [x] 4.1.3 测试错误处理和 fallback
- [x] 4.2 编写 prompt 加载工具测试
- [x] 4.3 集成测试：使用真实简历文件测试完整流程

## 5. 文档

- [x] 5.1 更新 README.md 说明 LLM 解析功能
- [x] 5.2 在 prompts 目录添加 README 说明 prompt 管理规范
