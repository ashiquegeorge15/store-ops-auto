from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class CampaignType(str, Enum):
    DOD = "DOD"  # Deal of the Day
    SPIN_WHEEL = "SPIN_WHEEL"
    FLASH_SALE = "FLASH_SALE"
    OTHER = "OTHER"


class RequestType(str, Enum):
    SP_CHANGE = "SP Change"
    REPLACEMENT = "Replacement"


class MonetaryType(str, Enum):
    ORGANIC = "Organic"
    INORGANIC = "Inorganic"


class RawCampaignData(BaseModel):
    """Raw campaign data from MySQL database"""
    issue_type: str = Field(..., description="Campaign type (DOD, etc.)")
    live_date: str = Field(..., description="Campaign start date")
    segment: str = Field(..., description="Segment information")
    slot: Optional[int] = Field(None, description="Slot number")
    end_date: str = Field(..., description="Campaign end date")
    request_type: str = Field(..., description="Request type")
    monetary_type: Optional[str] = Field(None, description="Monetary type")
    cpc: Optional[float] = Field(None, description="Cost per click")
    product_id: str = Field(..., description="Product ID")
    akeneo_product_name: Optional[str] = Field(None, description="Akeneo product name")
    akeneo_brand_name: Optional[str] = Field(None, description="Akeneo brand name")
    selling_price: float = Field(..., description="Selling price")
    projected_inventory: Optional[int] = Field(None, description="Projected inventory")
    brand: Optional[str] = Field(None, description="Brand")
    preferred_landing_sku_id: Optional[str] = Field(None, description="Preferred landing SKU ID")
    property: Optional[str] = Field(None, description="Campaign property")
    funnel: Optional[str] = Field(None, description="Funnel")
    mv: Optional[str] = Field(None, description="MV")
    top_bet_date: Optional[str] = Field(None, description="Top bet date")
    campaign_name: Optional[str] = Field(None, description="Campaign name")
    top_bet: Optional[str] = Field(None, description="Top bet")
    article_type: Optional[str] = Field(None, description="Article type")
    akeneo_family: Optional[str] = Field(None, description="Akeneo family")
    MRP: Optional[float] = Field(None, description="Maximum Retail Price")
    segment_in: Optional[str] = Field(None, description="Segment in")
    remarks: Optional[str] = Field(None, description="Remarks")
    price_remarks: Optional[str] = Field(None, description="Price remarks")
    user_email: Optional[str] = Field(None, description="User email")
    impressions: Optional[int] = Field(None, description="Impressions")
    tacos: Optional[float] = Field(None, description="TACOS")
    index: Optional[int] = Field(None, description="Index")
    available_inventory: Optional[int] = Field(None, description="Available inventory")


class FalconFormattedData(BaseModel):
    """Formatted data for Falcon API"""
    sku_id: str = Field(..., description="SKU ID")
    product_id: str = Field(..., description="Product ID")
    MRP: float = Field(..., description="Maximum Retail Price")
    MOP: float = Field(..., description="Market Operating Price")
    selling_price: float = Field(..., description="Selling price")
    mop_cost: float = Field(..., description="MOP cost (selling_price * 0.979)")
    selling_price_cost: float = Field(..., description="Selling price cost")
    coins: int = Field(default=2000, description="Coins")


class CampaignFilter(BaseModel):
    """Filter criteria for campaigns"""
    campaign_types: Optional[List[str]] = Field(None, description="List of campaign types to filter")
    start_date: Optional[datetime] = Field(None, description="Filter campaigns starting after this date")
    end_date: Optional[datetime] = Field(None, description="Filter campaigns ending before this date")
    segment: Optional[str] = Field(None, description="Segment filter")
    brand: Optional[str] = Field(None, description="Brand filter")
    active_only: bool = Field(default=True, description="Only return active campaigns")


class ProcessedCampaignData(BaseModel):
    """Processed campaign data with both raw and formatted versions"""
    raw_data: RawCampaignData
    falcon_data: FalconFormattedData
    processed_at: datetime = Field(default_factory=datetime.now)


class CampaignResponse(BaseModel):
    """Response model for campaign data"""
    total_count: int = Field(..., description="Total number of campaigns")
    processed_count: int = Field(..., description="Number of successfully processed campaigns")
    failed_count: int = Field(..., description="Number of failed campaigns")
    campaigns: List[ProcessedCampaignData] = Field(..., description="List of processed campaigns")
    filters_applied: Optional[CampaignFilter] = Field(None, description="Filters that were applied") 