# app/models.py
from sqlalchemy import (
    Column, Integer, String, Boolean,
    DateTime, ForeignKey, Text, Numeric,
    Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    categories = relationship("Category", back_populates="user",
                              cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user",
                                cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User email={self.email}>"


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)    # hex color e.g. "#FF5733"
    icon = Column(String(50), nullable=True)    # e.g. "food", "car", "home"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")

    # A user can't have two categories with the same name
    # This is a unique constraint SCOPED to a user, not globally unique
    # "Food" can exist for User A and User B, but not twice for User A
    __table_args__ = (
        Index("idx_category_user", "user_id"),
        Index("idx_category_name_user", "name", "user_id", unique=True),
    )

    def __repr__(self):
        return f"<Category name={self.name} user_id={self.user_id}>"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    # Numeric(12, 2) means: up to 12 digits total, 2 decimal places
    # Use Numeric for money, NEVER Float — floats have precision errors
    # 0.1 + 0.2 = 0.30000000000000004 in floating point

    type = Column(String(10), nullable=False)
    # "income" or "expense" — enforced by CheckConstraint below

    description = Column(Text, nullable=True)
    date = Column(DateTime(timezone=True), nullable=False)
    # When the transaction actually happened (user-provided)
    # Different from created_at which is when the record was created

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id",
                         ondelete="SET NULL"), nullable=True)
    # ondelete="SET NULL" means if a category is deleted,
    # transactions keep existing but lose their category
    # Better than CASCADE (which would delete all transactions) or
    # RESTRICT (which would prevent deleting categories that have transactions)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")

    __table_args__ = (
        # Enforce that type can only be "income" or "expense"
        CheckConstraint("type IN ('income', 'expense')", name="chk_type"),
        # Index for the queries we'll run most often
        Index("idx_transaction_user_id", "user_id"),
        Index("idx_transaction_date", "date"),
        Index("idx_transaction_user_date", "user_id", "date"),
        # Composite index — our summary queries filter by BOTH user_id and date
    )

    def __repr__(self):
        return f"<Transaction amount={self.amount} type={self.type}>"