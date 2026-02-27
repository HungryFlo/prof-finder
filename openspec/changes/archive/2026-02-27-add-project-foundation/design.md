# Design: Add Project Foundation

## Context

Prof-Finder 是一个帮助学生寻找导师的CLI工具。作为项目的第一个版本，需要建立清晰的架构以支持后续功能扩展（Web前端、更多简历格式、大学网站爬虫适配器等）。

**约束条件**：
- 个人部署，开源分享
- 第一版仅支持CLI
- 数据需要持久化（SQLite）
- 简历解析后需用户确认

## Goals / Non-Goals

**Goals**:
- 建立可扩展的项目结构
- 实现完整的CLI命令框架
- 支持LaTeX和Markdown简历解析
- 数据模型支持所有核心实体

**Non-Goals**:
- 本阶段不实现Web前端
- 本阶段不实现大学官网爬虫
- 本阶段不实现匹配算法和邮件生成的具体逻辑（仅占位）

## Decisions

### 1. 项目结构

**Decision**: 采用 src-layout 结构

```
prof-finder/
├── src/
│   └── prof_finder/
│       ├── __init__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py          # Typer入口
│       │   ├── profile.py       # profile命令组
│       │   ├── professor.py     # professor命令组
│       │   ├── match.py         # match命令
│       │   └── letter.py        # letter命令
│       ├── parser/
│       │   ├── __init__.py
│       │   ├── base.py          # 抽象基类
│       │   ├── markdown_parser.py
│       │   └── latex_parser.py
│       ├── models/
│       │   ├── __init__.py
│       │   └── schema.py        # SQLAlchemy模型
│       ├── db/
│       │   ├── __init__.py
│       │   └── database.py      # 数据库连接和操作
│       └── config.py            # 配置管理
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   └── test_models.py
├── data/                        # 数据存储目录（gitignored）
├── pyproject.toml
├── .env.example
└── README.md
```

**Rationale**: src-layout 是Python现代项目的推荐结构，避免导入冲突，便于打包发布。

### 2. CLI框架选择

**Decision**: 使用 Typer

**Alternatives considered**:
- Click: 更底层，需要更多样板代码
- argparse: 标准库但功能有限

**Rationale**: Typer 基于 Click，提供类型注解支持和自动生成帮助文档，代码更简洁。

### 3. 数据模型设计

**Decision**: 使用 SQLAlchemy ORM + SQLite，支持多用户和教授池管理

```python
# 核心模型
class User(Base):
    """用户账户"""
    id: int (PK)
    username: str (unique)  # 用户标识
    created_at: datetime

class UserProfile(Base):
    """用户简历（一个用户可有多份简历）"""
    id: int (PK)
    user_id: FK -> User
    name: str  # 简历中的姓名
    title: str  # 简历标题/版本名（如"申请NLP方向"）
    education: JSON  # [{"degree": "本科", "school": "清华", "major": "CS"}]
    research_experience: JSON  # [{"title": "...", "description": "..."}]
    projects: JSON
    skills: JSON  # ["Python", "NLP", "TensorFlow"]
    raw_content: str  # 原始简历内容
    is_active: bool  # 是否为当前使用的简历
    created_at: datetime
    updated_at: datetime

class Professor(Base):
    """教授信息（用户独立的教授池）"""
    id: int (PK)
    user_id: FK -> User  # 所属用户（教授池隔离）
    name: str
    affiliation: str  # 院系/大学
    research_interests: JSON  # ["NLP", "Machine Learning"]
    homepage: str
    google_scholar_id: str
    google_scholar_url: str
    publications: JSON  # [{title, year, citations}]
    h_index: int (nullable)
    citations: int (nullable)
    email: str (nullable)
    created_at: datetime
    updated_at: datetime

class MatchRecord(Base):
    """匹配记录"""
    id: int (PK)
    user_profile_id: FK -> UserProfile
    professor_id: FK -> Professor
    score: float
    match_reasons: JSON  # ["研究方向匹配: NLP", "技能匹配: Python"]
    letter_content: str (nullable)
    letter_generated_at: datetime (nullable)
    created_at: datetime
```

**关键设计决策**:
- **用户隔离**: 每个用户有独立的教授池，互不干扰
- **多简历支持**: 一个用户可创建多份简历，用 `is_active` 标记当前使用的
- **教授可更新**: 通过 `updated_at` 跟踪，支持重新爬取更新

**Rationale**: JSON字段存储灵活的结构化数据，避免过度规范化。SQLite足够个人使用，后续可迁移到PostgreSQL。

### 4. 简历解析策略

**Decision**: 基于正则表达式 + 关键词匹配的规则解析

**Workflow**:
1. 读取文件内容
2. 识别文件格式（.md / .tex）
3. 提取结构化信息（教育背景、科研经历、技能）
4. 展示提取结果，用户确认/修改
5. 保存到数据库

**Markdown解析**:
- 按标题层级分割内容
- 识别常见标题（Education, Experience, Skills, 教育背景, 科研经历等）

**LaTeX解析**:
- 使用 pylatexenc 转为纯文本
- 识别 `\section{}`, `\subsection{}` 结构
- 提取列表项（`\item`）

**Rationale**: 第一版采用规则方法，简单可控。后续可引入LLM辅助解析提高准确率。

### 5. 配置管理

**Decision**: python-dotenv + Pydantic Settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_path: str = "./data/prof_finder.db"
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    request_delay: int = 3
    
    class Config:
        env_file = ".env"
```

**Rationale**: Pydantic提供类型验证和默认值，比手动解析更健壮。

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| 简历格式多样，解析准确率有限 | 用户确认机制，允许手动修改 |
| SQLite并发限制 | 个人使用场景足够，后续可迁移 |
| 数据模型可能需要调整 | JSON字段提供灵活性，便于迭代 |

## Migration Plan

N/A（新项目，无需迁移）

## Open Questions

1. ~~是否需要支持多用户简历？~~ **已确认**：支持多用户，每用户可有多份简历
2. ~~教授数据更新策略？~~ **已确认**：手动触发更新，用户可随时重新爬取教授信息
