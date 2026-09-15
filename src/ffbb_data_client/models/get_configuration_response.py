"""Configuration models for FFBB API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GetConfigurationResponse(BaseModel):
    """Response model for /items/configuration endpoint."""

    model_config = ConfigDict(extra="ignore")

    id: int
    key_dh: str = Field(min_length=1)
    key_ms: str = Field(min_length=1)
    key_directus_website: str | None = None
    key_directus_competitions: str | None = None
    ios_version: str | None = None
    android_version: str | None = None
    date_created: str | None = None
    date_updated: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GetConfigurationResponse:
        """Create a GetConfigurationResponse from a dictionary."""
        return cls.model_validate(data)

    @property
    def api_bearer_token(self) -> str:
        """Alias for key_dh - the API bearer token."""
        return self.key_dh

    @property
    def meilisearch_token(self) -> str:
        """Alias for key_ms - the Meilisearch token."""
        return self.key_ms
