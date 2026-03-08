# app/utils/pagination.py
from fastapi import Query
from dataclasses import dataclass
from sqlalchemy.orm import Query as SQLQuery


@dataclass
class PaginationParams:
    """
    Reusable pagination parameters injected into any endpoint.

    Usage in a route:
    def get_transactions(pagination: PaginationParams = Depends(get_pagination)):
    """
    page: int
    per_page: int

    @property
    def offset(self):
        return (self.page - 1) * self.per_page


def get_pagination(
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=20, ge=1, le=100,
                          description="Items per page (max 100)")
) -> PaginationParams:
    return PaginationParams(page=page, per_page=per_page)


def paginate(query: SQLQuery, pagination: PaginationParams) -> dict:
    """
    Apply pagination to any SQLAlchemy query and return metadata.

    This is the core pagination function — call it from any endpoint
    that returns a list of items.
    """
    total = query.count()              # total records matching filters

    items = query.offset(pagination.offset)\
                 .limit(pagination.per_page)\
                 .all()

    total_pages = (total + pagination.per_page - 1) // pagination.per_page
    # This is ceiling division without importing math
    # e.g. 21 items, 20 per page = ceil(21/20) = 2 pages

    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_pages": total_pages,
        "has_next": pagination.page < total_pages,
        "has_prev": pagination.page > 1,
    }
