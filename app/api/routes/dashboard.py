from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database.connection import get_db
from app.services.database_service import DatabaseService
from app.services.campaign_service import CampaignService

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Initialize services
db_service = DatabaseService()
campaign_service = CampaignService()


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, db: Session = Depends(get_db)):
    """
    Main dashboard page
    """
    try:
        # Get available filter options
        campaign_types = db_service.get_campaign_types(db)
        segments = db_service.get_segments(db)
        brands = db_service.get_brands(db)
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "campaign_types": campaign_types,
            "segments": segments,
            "brands": brands,
            "title": "Store Operations Dashboard"
        })
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e),
            "title": "Dashboard Error"
        })


@router.get("/campaigns", response_class=HTMLResponse)
async def campaigns_page(
    request: Request,
    campaign_type: Optional[str] = None,
    segment: Optional[str] = None,
    brand: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Campaigns listing page with filters
    """
    try:
        # Build filters
        from app.models.campaign import CampaignFilter
        
        filters = CampaignFilter(
            campaign_types=[campaign_type] if campaign_type else None,
            segment=segment,
            brand=brand,
            active_only=active_only
        )
        
        # Fetch and process campaigns
        raw_campaigns = db_service.get_campaigns(db, filters)
        response = campaign_service.process_campaign_data(raw_campaigns)
        
        # Get filter options for dropdowns
        campaign_types = db_service.get_campaign_types(db)
        segments = db_service.get_segments(db)
        brands = db_service.get_brands(db)
        
        # Get summary
        summary = campaign_service.get_campaign_summary(response.campaigns)
        
        return templates.TemplateResponse("campaigns.html", {
            "request": request,
            "campaigns": response.campaigns,
            "summary": summary,
            "processing_stats": {
                "total_fetched": response.total_count,
                "successfully_processed": response.processed_count,
                "failed": response.failed_count
            },
            "filters": {
                "campaign_type": campaign_type,
                "segment": segment,
                "brand": brand,
                "active_only": active_only
            },
            "filter_options": {
                "campaign_types": campaign_types,
                "segments": segments,
                "brands": brands
            },
            "title": "Campaign Management"
        })
        
    except Exception as e:
        logger.error(f"Error loading campaigns page: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e),
            "title": "Campaigns Error"
        }) 