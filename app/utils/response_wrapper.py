from typing import Any, Optional
from pydantic import BaseModel


class APIResponse(BaseModel):
    status: str
    message: str
    data: Optional[Any] = None
    error: Optional[Any] = None


def success_response(message: str, data: Any = None) -> APIResponse:
    return APIResponse(status="success", message=message, data=data)


def error_response(message: str, error: Any = None) -> APIResponse:
    return APIResponse(status="error", message=message, error=error)
