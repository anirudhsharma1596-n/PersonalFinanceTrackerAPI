# app/schemas.py
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional
from decimal import Decimal
from typing import Annotated


# ── User schemas ───────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr                    # Pydantic validates email format
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=72)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v):
        if not v.replace("_", "").isalnum():
            raise ValueError("Username must be alphanumeric (underscores allowed)")
        return v.lower()               # always store lowercase


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Auth schemas ───────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"         # standard OAuth2 token type


class TokenData(BaseModel):
    user_id: Optional[int] = None      # extracted from JWT payload


# ── Category schemas ───────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    # Regex validates hex color format: #FF5733
    icon: Optional[str] = Field(None, max_length=50)


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    color: Optional[str]
    icon: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


MoneyAmount = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]


# ── Transaction schemas ────────────────────────────────────────

class TransactionCreate(BaseModel):
    amount: MoneyAmount
    # gt=0 means "greater than zero" — amounts must be positive
    # The type field (income/expense) determines direction, not sign

    type: str = Field(..., pattern="^(income|expense)$")
    description: Optional[str] = Field(None, max_length=500)
    date: datetime
    category_id: Optional[int] = None


class TransactionUpdate(BaseModel):
    # All fields optional — user can update just what they want
    amount: Optional[MoneyAmount] 
    type: Optional[str] = Field(None, pattern="^(income|expense)$")
    description: Optional[str] = Field(None, max_length=500)
    date: Optional[datetime] = None
    category_id: Optional[int] = None


class TransactionResponse(BaseModel):
    id: int
    amount: Decimal
    type: str
    description: Optional[str]
    date: datetime
    category_id: Optional[int]
    category: Optional[CategoryResponse]   # nested response
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Pagination schema (reusable) ───────────────────────────────

class PaginatedResponse(BaseModel):
    items: list                        # will be overridden per endpoint
    total: int                         # total records matching the filter
    page: int                          # current page number
    per_page: int                      # items per page
    total_pages: int                   # total number of pages
    has_next: bool
    has_prev: bool