from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import os

from app.database.connection import get_db
from app.models.campaign import CampaignFilter, CampaignResponse, ProcessedCampaignData
from app.services.database_service import DatabaseService
from app.services.campaign_service import CampaignService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
db_service = DatabaseService()
campaign_service = CampaignService()


@router.get("/campaigns", response_model=CampaignResponse)
async def get_campaigns(
    campaign_types: Optional[List[str]] = Query(None, description="Filter by campaign types (e.g., DOD, SPIN_WHEEL)"),
    segment: Optional[str] = Query(None, description="Filter by segment"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    active_only: bool = Query(True, description="Only return active campaigns"),
    db: Session = Depends(get_db)
):
    """
    Get campaigns with optional filters
    """
    try:
        # Create filter object
        filters = CampaignFilter(
            campaign_types=campaign_types,
            segment=segment,
            brand=brand,
            active_only=active_only
        )
        
        # Fetch raw campaign data
        raw_campaigns = db_service.get_campaigns(db, filters)
        
        if not raw_campaigns:
            return CampaignResponse(
                total_count=0,
                processed_count=0,
                failed_count=0,
                campaigns=[],
                filters_applied=filters
            )
        
        # Process campaigns
        response = campaign_service.process_campaign_data(raw_campaigns)
        response.filters_applied = filters
        
        return response
        
    except Exception as e:
        logger.error(f"Error fetching campaigns: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching campaigns: {str(e)}")


@router.get("/campaigns/active", response_model=CampaignResponse)
async def get_active_campaigns(
    campaign_types: Optional[List[str]] = Query(None, description="Filter by campaign types"),
    db: Session = Depends(get_db)
):
    """
    Get only currently active campaigns
    """
    try:
        filters = CampaignFilter(
            campaign_types=campaign_types,
            active_only=True
        )
        
        raw_campaigns = db_service.get_campaigns(db, filters)
        
        if not raw_campaigns:
            return CampaignResponse(
                total_count=0,
                processed_count=0,
                failed_count=0,
                campaigns=[],
                filters_applied=filters
            )
        
        # Filter for truly active campaigns
        active_campaigns = campaign_service.filter_active_campaigns(raw_campaigns)
        
        # Process campaigns
        response = campaign_service.process_campaign_data(active_campaigns)
        response.filters_applied = filters
        
        return response
        
    except Exception as e:
        logger.error(f"Error fetching active campaigns: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching active campaigns: {str(e)}")


@router.get("/campaigns/types")
async def get_campaign_types(db: Session = Depends(get_db)):
    """
    Get all available campaign types
    """
    try:
        campaign_types = db_service.get_campaign_types(db)
        return {"campaign_types": campaign_types}
        
    except Exception as e:
        logger.error(f"Error fetching campaign types: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching campaign types: {str(e)}")


@router.get("/campaigns/segments")
async def get_segments(db: Session = Depends(get_db)):
    """
    Get all available segments
    """
    try:
        segments = db_service.get_segments(db)
        return {"segments": segments}
        
    except Exception as e:
        logger.error(f"Error fetching segments: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching segments: {str(e)}")


@router.get("/campaigns/brands")
async def get_brands(db: Session = Depends(get_db)):
    """
    Get all available brands
    """
    try:
        brands = db_service.get_brands(db)
        return {"brands": brands}
        
    except Exception as e:
        logger.error(f"Error fetching brands: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching brands: {str(e)}")


@router.get("/campaigns/export")
async def export_campaigns(
    campaign_types: Optional[List[str]] = Query(None, description="Filter by campaign types"),
    segment: Optional[str] = Query(None, description="Filter by segment"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    active_only: bool = Query(True, description="Only export active campaigns"),
    db: Session = Depends(get_db)
):
    """
    Export campaigns to Excel file
    """
    try:
        # Create filter object
        filters = CampaignFilter(
            campaign_types=campaign_types,
            segment=segment,
            brand=brand,
            active_only=active_only
        )
        
        # Fetch and process campaigns
        raw_campaigns = db_service.get_campaigns(db, filters)
        
        if not raw_campaigns:
            raise HTTPException(status_code=404, detail="No campaigns found with the given filters")
        
        # Process campaigns
        response = campaign_service.process_campaign_data(raw_campaigns)
        
        if not response.campaigns:
            raise HTTPException(status_code=404, detail="No valid campaigns to export")
        
        # Export to Excel
        filename = campaign_service.export_to_excel(response.campaigns)
        
        if not os.path.exists(filename):
            raise HTTPException(status_code=500, detail="Error creating export file")
        
        return FileResponse(
            path=filename,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting campaigns: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting campaigns: {str(e)}")


@router.get("/campaigns/summary")
async def get_campaign_summary(
    campaign_types: Optional[List[str]] = Query(None, description="Filter by campaign types"),
    segment: Optional[str] = Query(None, description="Filter by segment"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    active_only: bool = Query(True, description="Only include active campaigns"),
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for campaigns
    """
    try:
        # Create filter object
        filters = CampaignFilter(
            campaign_types=campaign_types,
            segment=segment,
            brand=brand,
            active_only=active_only
        )
        
        # Fetch and process campaigns
        raw_campaigns = db_service.get_campaigns(db, filters)
        
        if not raw_campaigns:
            return {"summary": {"total_campaigns": 0}, "filters_applied": filters.dict()}
        
        # Process campaigns
        response = campaign_service.process_campaign_data(raw_campaigns)
        
        # Get summary
        summary = campaign_service.get_campaign_summary(response.campaigns)
        
        return {
            "summary": summary,
            "processing_stats": {
                "total_fetched": response.total_count,
                "successfully_processed": response.processed_count,
                "failed": response.failed_count
            },
            "filters_applied": filters.dict()
        }
        
    except Exception as e:
        logger.error(f"Error getting campaign summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting campaign summary: {str(e)}")


@router.get("/campaigns/product/{product_id}")
async def get_campaign_by_product(
    product_id: str,
    db: Session = Depends(get_db)
):
    """
    Get campaign data for a specific product
    """
    try:
        # Fetch raw campaign data
        raw_campaign = db_service.get_campaign_by_product_id(db, product_id)
        
        if not raw_campaign:
            raise HTTPException(status_code=404, detail=f"No campaign found for product {product_id}")
        
        # Process campaign
        response = campaign_service.process_campaign_data([raw_campaign])
        
        if not response.campaigns:
            raise HTTPException(status_code=500, detail=f"Error processing campaign for product {product_id}")
        
        return {
            "product_id": product_id,
            "campaign": response.campaigns[0],
            "processing_stats": {
                "total_fetched": response.total_count,
                "successfully_processed": response.processed_count,
                "failed": response.failed_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching campaign for product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching campaign: {str(e)}")


@router.post("/campaigns/validate")
async def validate_campaigns(
    campaign_types: Optional[List[str]] = Query(None, description="Filter by campaign types"),
    segment: Optional[str] = Query(None, description="Filter by segment"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    db: Session = Depends(get_db)
):
    """
    Validate campaign data without processing
    """
    try:
        # Create filter object
        filters = CampaignFilter(
            campaign_types=campaign_types,
            segment=segment,
            brand=brand,
            active_only=False  # Validate all campaigns, not just active ones
        )
        
        # Fetch raw campaign data
        raw_campaigns = db_service.get_campaigns(db, filters)
        
        if not raw_campaigns:
            return {
                "total_campaigns": 0,
                "valid_campaigns": 0,
                "invalid_campaigns": 0,
                "validation_errors": [],
                "filters_applied": filters.dict()
            }
        
        valid_count = 0
        invalid_count = 0
        all_errors = []
        
        for campaign in raw_campaigns:
            errors = campaign_service.validate_campaign_data(campaign)
            if errors:
                invalid_count += 1
                all_errors.extend([
                    {
                        "product_id": campaign.product_id,
                        "errors": errors
                    }
                ])
            else:
                valid_count += 1
        
        return {
            "total_campaigns": len(raw_campaigns),
            "valid_campaigns": valid_count,
            "invalid_campaigns": invalid_count,
            "validation_errors": all_errors,
            "filters_applied": filters.dict()
        }
        
    except Exception as e:
        logger.error(f"Error validating campaigns: {e}")
        raise HTTPException(status_code=500, detail=f"Error validating campaigns: {str(e)}") 