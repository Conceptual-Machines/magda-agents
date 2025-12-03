"""
MAGDA Agents - Framework interfaces
"""

from abc import ABC, abstractmethod
from typing import Protocol


class AuthProvider(Protocol):
    """Interface for authentication providers."""
    
    def get_user_id(self, ctx) -> str:
        """Get current user ID from context."""
        ...
    
    def require_auth(self, ctx) -> None:
        """Ensure user is authenticated."""
        ...


class BillingProvider(Protocol):
    """Interface for billing/credits providers."""
    
    def check_credits(self, ctx, user_id: str, cost: int) -> None:
        """Check if user has sufficient credits."""
        ...
    
    def deduct_credits(self, ctx, user_id: str, cost: int) -> None:
        """Deduct credits from user account."""
        ...

