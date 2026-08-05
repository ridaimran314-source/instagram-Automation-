"""Shared enum definitions."""

from enum import StrEnum


class ScholarshipStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"


class JobStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    RENDERED = "rendered"
    PUBLISHED = "published"
    FAILED = "failed"
