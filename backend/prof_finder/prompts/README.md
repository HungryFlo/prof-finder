# Prompts Directory

This directory contains all LLM prompt templates used by Prof-Finder.

## Structure

```
prompts/
├── __init__.py           # Prompt loading utilities
├── resume_parser.yaml    # Resume parsing prompts
└── README.md             # This file
```

## Usage

```python
from prof_finder.prompts import get_prompt

# Get a prompt with variable substitution
system_prompt = get_prompt("resume_parser", "resume_extraction", "system")
user_prompt = get_prompt("resume_parser", "resume_extraction", "user", content="...")
```

## YAML Format

Each prompt file follows this structure:

```yaml
prompt_name:
  system: |
    System prompt content...
  user: |
    User prompt with {variable} placeholders...
```

## Adding New Prompts

1. Create a new YAML file or add to an existing one
2. Follow the naming convention: `<module>_<function>.yaml`
3. Include both `system` and `user` prompts when applicable
4. Use `{variable}` syntax for dynamic content
5. Document the expected variables in comments

## Best Practices

- Keep prompts concise and focused
- Use clear JSON schema examples for structured output
- Test prompts with various inputs before committing
- Version control prompt changes carefully (they affect output quality)
