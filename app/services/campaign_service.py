import logging
from typing import List, Optional
from datetime import datetime
import pandas as pd

from app.core.config import settings
from app.models.campaign import (
    RawCampaignData, 
    FalconFormattedData, 
    ProcessedCampaignData, 
    CampaignFilter,
    CampaignResponse
)
from app.services.akeneo_service import AkeneoService

logger = logging.getLogger(__name__)


class CampaignService:
    """Service for processing campaign data"""
    
    def __init__(self):
        self.akeneo_service = AkeneoService()
    
    def transform_to_falcon_format(self, raw_data: RawCampaignData) -> Optional[FalconFormattedData]:
        """
        Transform raw campaign data to Falcon format
        
        Args:
            raw_data: Raw campaign data from database
            
        Returns:
            FalconFormattedData object or None if transformation fails
        """
        try:
            # Get SKU ID from Akeneo using preferred_landing_sku_id or product_id
            sku_id = raw_data.preferred_landing_sku_id
            if not sku_id:
                sku_id = self.akeneo_service.get_product_sku_mapping(raw_data.product_id)
            
            if not sku_id:
                logger.warning(f"Could not find SKU for product {raw_data.product_id}")
                sku_id = raw_data.product_id  # Fallback to product_id
            
            # Get MRP from Akeneo or use from raw data
            mrp = raw_data.MRP
            if not mrp:
                mrp = self.akeneo_service.get_product_mrp(raw_data.product_id)
            
            if not mrp:
                logger.warning(f"Could not find MRP for product {raw_data.product_id}")
                mrp = raw_data.selling_price * 1.5  # Fallback calculation
            
            # Calculate MOP cost (selling_price * 0.979)
            mop_cost = raw_data.selling_price * settings.DEFAULT_MOP_MULTIPLIER
            
            # For now, MOP = selling_price (this might need adjustment based on business logic)
            mop = raw_data.selling_price
            
            return FalconFormattedData(
                sku_id=sku_id,
                product_id=raw_data.product_id,
                MRP=mrp,
                MOP=mop,
                selling_price=raw_data.selling_price,
                mop_cost=mop_cost,
                selling_price_cost=raw_data.selling_price,  # Assuming same as selling_price
                coins=settings.DEFAULT_COINS
            )
            
        except Exception as e:
            logger.error(f"Error transforming campaign data for product {raw_data.product_id}: {e}")
            return None
    
    def process_campaign_data(self, raw_campaigns: List[RawCampaignData]) -> CampaignResponse:
        """
        Process a list of raw campaign data
        
        Args:
            raw_campaigns: List of raw campaign data
            
        Returns:
            CampaignResponse with processed data
        """
        processed_campaigns = []
        failed_count = 0
        
        for raw_campaign in raw_campaigns:
            try:
                falcon_data = self.transform_to_falcon_format(raw_campaign)
                
                if falcon_data:
                    processed_campaigns.append(
                        ProcessedCampaignData(
                            raw_data=raw_campaign,
                            falcon_data=falcon_data
                        )
                    )
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing campaign for product {raw_campaign.product_id}: {e}")
                failed_count += 1
        
        return CampaignResponse(
            total_count=len(raw_campaigns),
            processed_count=len(processed_campaigns),
            failed_count=failed_count,
            campaigns=processed_campaigns
        )
    
    def export_to_excel(self, campaigns: List[ProcessedCampaignData], filename: str = None) -> str:
        """
        Export processed campaigns to Excel format
        
        Args:
            campaigns: List of processed campaign data
            filename: Optional filename, defaults to timestamp-based name
            
        Returns:
            Path to created Excel file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"campaign_data_{timestamp}.xlsx"
        
        # Convert to DataFrame
        falcon_data = [campaign.falcon_data.dict() for campaign in campaigns]
        df = pd.DataFrame(falcon_data)
        
        # Save to Excel
        try:
            df.to_excel(filename, index=False)
            logger.info(f"Campaign data exported to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            raise
    
    def validate_campaign_data(self, raw_data: RawCampaignData) -> List[str]:
        """
        Validate raw campaign data
        
        Args:
            raw_data: Raw campaign data to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check required fields
        if not raw_data.product_id:
            errors.append("Product ID is required")
        
        if not raw_data.selling_price or raw_data.selling_price <= 0:
            errors.append("Valid selling price is required")
        
        if not raw_data.live_date:
            errors.append("Live date is required")
        
        if not raw_data.end_date:
            errors.append("End date is required")
        
        # Check date format and validity
        try:
            live_date = datetime.strptime(raw_data.live_date, "%d/%m/%Y")
            end_date = datetime.strptime(raw_data.end_date, "%d/%m/%Y")
            
            if end_date <= live_date:
                errors.append("End date must be after live date")
                
        except ValueError:
            errors.append("Invalid date format. Expected DD/MM/YYYY")
        
        return errors
    
    def filter_active_campaigns(self, campaigns: List[RawCampaignData]) -> List[RawCampaignData]:
        """
        Filter campaigns to only include active ones
        
        Args:
            campaigns: List of raw campaign data
            
        Returns:
            List of active campaigns
        """
        active_campaigns = []
        current_date = datetime.now()
        
        for campaign in campaigns:
            try:
                live_date = datetime.strptime(campaign.live_date, "%d/%m/%Y")
                end_date = datetime.strptime(campaign.end_date, "%d/%m/%Y")
                
                if live_date <= current_date <= end_date:
                    active_campaigns.append(campaign)
                    
            except ValueError:
                logger.warning(f"Invalid date format for campaign {campaign.product_id}")
                continue
        
        return active_campaigns
    
    def get_campaign_summary(self, campaigns: List[ProcessedCampaignData]) -> dict:
        """
        Get summary statistics for campaigns
        
        Args:
            campaigns: List of processed campaign data
            
        Returns:
            Dictionary with summary statistics
        """
        if not campaigns:
            return {"total_campaigns": 0}
        
        # Extract data for analysis
        selling_prices = [c.falcon_data.selling_price for c in campaigns]
        mrps = [c.falcon_data.MRP for c in campaigns]
        campaign_types = [c.raw_data.issue_type for c in campaigns]
        
        summary = {
            "total_campaigns": len(campaigns),
            "campaign_types": list(set(campaign_types)),
            "avg_selling_price": sum(selling_prices) / len(selling_prices),
            "min_selling_price": min(selling_prices),
            "max_selling_price": max(selling_prices),
            "avg_mrp": sum(mrps) / len(mrps),
            "total_potential_revenue": sum(selling_prices),
            "campaign_type_counts": {
                camp_type: campaign_types.count(camp_type) 
                for camp_type in set(campaign_types)
            }
        }
        
        return summary 