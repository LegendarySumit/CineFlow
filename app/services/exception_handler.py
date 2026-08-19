"""
EXCEPTION HANDLER - Standardized HTTP error responses for API endpoints.

Provides consistent error handling across all FastAPI endpoints:
- Validation errors (400)
- Not found errors (404)
- Server errors (500)
- Custom error mapping
"""

from typing import Any, Callable, TypeVar
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class APIError:
    """Standard API error response format."""
    
    @staticmethod
    def validation_error(detail: str) -> HTTPException:
        """400 - Invalid input or validation failure."""
        logger.warning(f"Validation error: {detail}")
        return HTTPException(status_code=400, detail=detail)
    
    @staticmethod
    def not_found(resource: str, identifier: str = "") -> HTTPException:
        """404 - Resource not found."""
        msg = f"{resource} not found"
        if identifier:
            msg = f"{resource} {identifier} not found"
        logger.warning(f"Not found: {msg}")
        return HTTPException(status_code=404, detail=msg)
    
    @staticmethod
    def internal_error(operation: str, error: Exception = None) -> HTTPException:
        """500 - Server-side error."""
        msg = f"{operation} failed"
        if error:
            logger.error(f"Internal error in {operation}: {error!s}")
        else:
            logger.error(f"Internal error in {operation}")
        return HTTPException(status_code=500, detail=msg)
    
    @staticmethod
    def bad_request(detail: str) -> HTTPException:
        """400 - Bad request."""
        logger.warning(f"Bad request: {detail}")
        return HTTPException(status_code=400, detail=detail)


def handle_api_errors(
    operation: str = "operation",
    log_traceback: bool = False
) -> Callable:
    """
    Decorator for standardized API error handling.
    
    Args:
        operation: Description of operation (for logging)
        log_traceback: Whether to log full traceback on exception
    
    Returns:
        Decorated function with consistent error handling
    
    Example:
        @app.post("/api/analyze")
        @handle_api_errors("crisis analysis")
        async def analyze_crisis(request: AnalysisRequest):
            return analyze(request)
    
    Handles:
        ValueError → 400 Bad Request
        KeyError, TypeError, AttributeError → 500 Internal Server Error
        HTTPException → Pass through unchanged
    """
    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except ValueError as e:
                raise APIError.bad_request(str(e))
            except (KeyError, TypeError, AttributeError) as e:
                if log_traceback:
                    logger.exception(f"Error in {operation}")
                raise APIError.internal_error(operation, e)
            except Exception as e:
                if log_traceback:
                    logger.exception(f"Unexpected error in {operation}")
                raise APIError.internal_error(operation, e)
        
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except ValueError as e:
                raise APIError.bad_request(str(e))
            except (KeyError, TypeError, AttributeError) as e:
                if log_traceback:
                    logger.exception(f"Error in {operation}")
                raise APIError.internal_error(operation, e)
            except Exception as e:
                if log_traceback:
                    logger.exception(f"Unexpected error in {operation}")
                raise APIError.internal_error(operation, e)
        
        # Return async or sync wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def validate_request_field(value: Any, field_name: str, field_type: type = None) -> Any:
    """
    Validate request field and raise standardized error if invalid.
    
    Args:
        value: Value to validate
        field_name: Name of field (for error message)
        field_type: Expected type (optional)
    
    Returns:
        Validated value
    
    Raises:
        APIError.validation_error if validation fails
    """
    if value is None:
        raise APIError.validation_error(f"{field_name} is required")
    
    if isinstance(value, str) and len(value.strip()) == 0:
        raise APIError.validation_error(f"{field_name} cannot be empty")
    
    if field_type and not isinstance(value, field_type):
        raise APIError.validation_error(
            f"{field_name} must be {field_type.__name__}"
        )
    
    return value


def validate_status_field(result: dict[str, Any], operation: str = "operation") -> None:
    """
    Check if result dict has error status and raise if found.
    
    Args:
        result: Result dict to check
        operation: Operation name for error message
    
    Raises:
        APIError.bad_request if result has error status
    """
    if result.get("status") == "error":
        raise APIError.bad_request(result.get("message", f"{operation} failed"))
    
    if result.get("status") == "not_found":
        raise APIError.not_found(operation)
