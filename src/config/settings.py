"""Pydantic v2 configuration models."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class RiskConfig(BaseModel):
    max_notional_usd: float = Field(gt=0, description="Max notional value per trade in USD")
    max_quantity: int = Field(gt=0, description="Max shares per order")
    max_concentration_pct: float = Field(gt=0, le=100, description="Max portfolio concentration %")
    symbol_whitelist: list[str] = Field(
        default_factory=list, description="Allowed symbols; empty = all allowed"
    )


class RuntimeConfig(BaseModel):
    mode: Literal["offline_replay", "shadow", "uat_confirm", "prod_confirm", "prod_auto"]
    environment: Literal["uat", "prod"]
    region: str = Field(min_length=1)
    account_ids: list[str] = Field(min_length=1)
    confirmation_mode: Literal["auto", "confirm", "skip"]
    risk: RiskConfig

    @field_validator("account_ids")
    @classmethod
    def account_ids_not_empty(cls, v: list[str]) -> list[str]:
        if not v or all(a.strip() == "" for a in v):
            raise ValueError("account_ids must contain at least one non-empty value")
        return v
