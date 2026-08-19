"""
ERROR HANDLER - Standardized error handling patterns across codebase.

Consolidates recurring error patterns:
- JSON parsing errors (JSONDecodeError, ValueError)
- File IO errors (IOError, OSError)
- Data validation errors (KeyError, TypeError, AttributeError)
"""

import json
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


def safe_json_load(file_path: str, fallback: Any = None, context: str = "file") -> Any:
    """
    Safely load JSON with consistent error handling.
    
    Args:
        file_path: Path to JSON file
        fallback: Default value if load fails
        context: Description for logging
    
    Returns:
        Parsed JSON data or fallback value
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse {context} JSON: {e!s}")
        return fallback or {}
    except (IOError, OSError) as e:
        logger.warning(f"Failed to read {context} file: {e!s}")
        return fallback or {}


def safe_json_parse(content: str, fallback: Any = None, context: str = "content") -> Any:
    """
    Safely parse JSON string with consistent error handling.
    
    Args:
        content: JSON string to parse
        fallback: Default value if parse fails
        context: Description for logging
    
    Returns:
        Parsed JSON data or fallback value
    """
    try:
        return json.loads(content) if content else (fallback or {})
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse {context}: {e!s}")
        return fallback or {}


def safe_dict_access(data: dict[str, Any], key: str, fallback: Any = None) -> Any:
    """
    Safely access dictionary with type checking.
    
    Args:
        data: Dictionary to access
        key: Key to access
        fallback: Default value if key missing or type mismatch
    
    Returns:
        Value at key or fallback
    """
    try:
        if not isinstance(data, dict):
            return fallback
        return data.get(key, fallback)
    except (KeyError, TypeError, AttributeError):
        return fallback


def safe_list_access(items: list[Any], index: int, fallback: Any = None) -> Any:
    """
    Safely access list item with bounds checking.
    
    Args:
        items: List to access
        index: Index to access
        fallback: Default value if index out of bounds
    
    Returns:
        Item at index or fallback
    """
    try:
        if not isinstance(items, list) or index < 0 or index >= len(items):
            return fallback
        return items[index]
    except (IndexError, TypeError):
        return fallback


def with_error_handling(
    fallback_value: Any = None,
    context: str = "operation",
    log_level: str = "warning"
) -> Callable:
    """
    Decorator for consistent error handling across functions.
    
    Args:
        fallback_value: Value to return on exception
        context: Description for logging
        log_level: Logging level (warning, error, info)
    
    Example:
        @with_error_handling(fallback_value={}, context="data load")
        def load_config():
            return json.load(...)
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except (json.JSONDecodeError, ValueError, IOError, OSError) as e:
                log_fn = getattr(logger, log_level, logger.warning)
                log_fn(f"{context} failed: {e!s}")
                return fallback_value
            except (KeyError, TypeError, AttributeError) as e:
                log_fn = getattr(logger, log_level, logger.warning)
                log_fn(f"{context} data error: {e!s}")
                return fallback_value
        return wrapper
    return decorator
