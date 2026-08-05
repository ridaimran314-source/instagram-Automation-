"""Schemas for operational API responses."""

from pydantic import BaseModel


class OperationResponse(BaseModel):
    """Standard response for operational endpoints."""

    status: str
    detail: str
