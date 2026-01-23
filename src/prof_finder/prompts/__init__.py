"""Prompt management module for LLM interactions."""

from pathlib import Path
from typing import Any, Optional
import yaml


_PROMPTS_DIR = Path(__file__).parent
_cache: dict[str, dict] = {}


def load_prompt_file(name: str) -> dict:
    """Load a prompt file by name.
    
    Args:
        name: Name of the prompt file (without .yaml extension).
        
    Returns:
        Dictionary containing all prompts in the file.
        
    Raises:
        FileNotFoundError: If prompt file doesn't exist.
    """
    if name in _cache:
        return _cache[name]
    
    file_path = _PROMPTS_DIR / f"{name}.yaml"
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    _cache[name] = data
    return data


def get_prompt(
    file_name: str,
    prompt_name: str,
    part: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """Get a prompt with variable substitution.
    
    Args:
        file_name: Name of the prompt file (without .yaml extension).
        prompt_name: Name of the prompt within the file.
        part: Optional part of the prompt (e.g., "system", "user").
        **kwargs: Variables to substitute in the prompt.
        
    Returns:
        Formatted prompt string.
        
    Raises:
        KeyError: If prompt or part not found.
        
    Example:
        >>> get_prompt("resume_parser", "resume_extraction", "user", content="...")
    """
    prompts = load_prompt_file(file_name)
    
    if prompt_name not in prompts:
        raise KeyError(f"Prompt '{prompt_name}' not found in {file_name}.yaml")
    
    prompt_data = prompts[prompt_name]
    
    if part:
        if part not in prompt_data:
            raise KeyError(f"Part '{part}' not found in prompt '{prompt_name}'")
        template = prompt_data[part]
    elif isinstance(prompt_data, str):
        template = prompt_data
    else:
        raise ValueError(
            f"Prompt '{prompt_name}' is a dict, please specify a part (e.g., 'system', 'user')"
        )
    
    # Perform variable substitution
    if kwargs:
        template = template.format(**kwargs)
    
    return template


def clear_cache() -> None:
    """Clear the prompt cache."""
    _cache.clear()
