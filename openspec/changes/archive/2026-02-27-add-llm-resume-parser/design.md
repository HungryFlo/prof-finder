# Design: LLM 简历解析器

## Context

当前简历解析使用正则表达式，存在以下问题：
1. 对简历格式有强假设（section 命名、结构等）
2. 无法处理非标准格式或自定义模板
3. 难以理解语义上下文（如区分"研究助理"和"教学助理"）

项目已集成 DeepSeek API 用于邮件生成，可复用这一基础设施进行简历解析。

## Goals / Non-Goals

**Goals:**
- 使用 LLM 提高简历解析准确率
- 统一管理项目中的 prompt 模板
- 保持向后兼容，正则解析器作为 fallback

**Non-Goals:**
- 不支持 PDF/DOCX 格式（后续扩展）
- 不实现本地 LLM 部署
- 不修改 `ParsedResume` 数据结构

## Decisions

### Decision 1: Prompt 管理方式

**选择**: 使用 YAML 文件管理 prompt 模板

**理由**:
- YAML 支持多行字符串，适合长 prompt
- 可以在 prompt 中定义变量占位符
- 便于版本控制和迭代
- 支持组织多个 prompt 变体

**目录结构**:
```
src/prof_finder/prompts/
├── __init__.py           # Prompt 加载工具
├── resume_parser.yaml    # 简历解析 prompts
└── letter_generator.yaml # 邮件生成 prompts（后续迁移）
```

**Prompt 文件格式**:
```yaml
resume_extraction:
  system: |
    你是一个专业的简历解析助手...
  user: |
    请从以下简历内容中提取结构化信息：
    
    {content}
    
    请以 JSON 格式返回...
```

### Decision 2: 解析策略

**选择**: LLM 优先，正则兜底

**流程**:
1. 尝试使用 LLM 解析简历
2. 如果 LLM 调用失败（网络错误、API 限流等），回退到正则解析
3. 如果正则解析也失败，返回空结果并提示用户手动输入

**理由**:
- LLM 解析质量更高，应优先使用
- 正则解析不依赖网络，可作为离线备选
- 用户无需感知具体使用了哪种解析器

### Decision 3: LLM 输出格式

**选择**: JSON Schema 约束输出

**JSON 结构**:
```json
{
  "name": "张三",
  "education": [
    {
      "degree": "本科",
      "school": "清华大学",
      "major": "计算机科学",
      "period": "2018-2022"
    }
  ],
  "research_experience": [
    {
      "title": "研究助理",
      "organization": "ABC实验室",
      "description": "参与NLP项目...",
      "period": "2021-2022"
    }
  ],
  "projects": [
    {
      "name": "机器翻译系统",
      "description": "基于Transformer的翻译系统..."
    }
  ],
  "skills": ["Python", "PyTorch", "NLP"]
}
```

**理由**:
- 与现有 `ParsedResume` 结构对齐，便于转换
- JSON 格式易于解析和验证
- 可在 prompt 中明确要求输出格式

### Decision 4: 错误处理

**策略**:
| 错误类型 | 处理方式 |
|---------|---------|
| API 网络错误 | 回退到正则解析 |
| API 限流 | 等待后重试（最多2次），然后回退 |
| JSON 解析失败 | 尝试修复 JSON，失败则回退 |
| 提取结果为空 | 回退到正则解析 |

## Risks / Trade-offs

| 风险 | 缓解措施 |
|-----|---------|
| API 调用成本 | 单次解析 token 消耗较小（~2000 tokens），成本可控 |
| 网络依赖 | 正则解析作为 fallback |
| LLM 幻觉 | 用户确认流程已存在，可捕获错误 |
| 响应延迟 | 简历解析是一次性操作，2-3秒延迟可接受 |

## Open Questions

1. 是否需要支持用户选择解析器？（当前设计为自动选择）
2. 是否需要缓存 LLM 解析结果？（当前设计为不缓存）
