"""
Product Pydantic schemas — request and response schemas for catalog items.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── Request Schemas ───────────────────────────────────────
class ProductCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    price: float = Field(gt=0, description="Product unit price")
    sku: str = Field(min_length=1, max_length=100, description="Unique stock keeping unit")
    quantity: int = Field(ge=0, default=0, description="Available stock quantity")


class ProductUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    price: float | None = Field(default=None, gt=0)
    sku: str | None = Field(default=None, min_length=1, max_length=100)
    quantity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


# ── Response Schemas ──────────────────────────────────────
class ProductResponse(BaseModel):
    id: str
    title: str
    description: str | None = None
    price: float
    sku: str
    quantity: int
    is_active: bool
    owner_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
