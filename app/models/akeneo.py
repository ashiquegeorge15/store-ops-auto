from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


class LinkedData(BaseModel):
    """Linked data model for Akeneo values"""
    attribute: Optional[str] = None
    code: Optional[str] = None
    labels: Optional[Dict[str, str]] = None


class Value(BaseModel):
    """Akeneo product value model"""
    locale: Optional[str] = None
    scope: Optional[str] = None
    data: Any = None
    linked_data: Optional[LinkedData] = None
    reference_data_name: Optional[str] = None
    attribute_type: Optional[str] = None
    assets: Optional[List[Dict[str, Any]]] = None


class ProductDetails(BaseModel):
    """Akeneo product details model"""
    id: str = Field(..., description="Product identifier")
    family: str = Field(..., description="Product family")
    parent: Optional[str] = Field(None, description="Parent product")
    values: Dict[str, List[Value]] = Field(..., description="Product values")


class Asset(BaseModel):
    """Akeneo asset model"""
    code: str = Field(..., description="Asset code")
    values: Dict[str, List[Value]] = Field(..., description="Asset values")


class AkeneoTokenResponse(BaseModel):
    """Akeneo token response model"""
    access_token: str = Field(..., description="Access token")
    expires_in: int = Field(..., description="Token expiry time in seconds")
    token_type: str = Field(..., description="Token type")
    scope: Optional[str] = Field(None, description="Token scope")
    refresh_token: Optional[str] = Field(None, description="Refresh token") 