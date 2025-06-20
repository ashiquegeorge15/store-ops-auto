import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.connection import get_db
from app.models.campaign import RawCampaignData, CampaignFilter

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for database operations"""
    
    def __init__(self):
        pass
    
    def get_campaigns(self, db: Session, filters: Optional[CampaignFilter] = None) -> List[RawCampaignData]:
        """
        Fetch campaign data from database with optional filters
        
        Args:
            db: Database session
            filters: Optional filter criteria
            
        Returns:
            List of RawCampaignData objects
        """
        try:
            # Base query - adjust table name based on your actual database schema
            base_query = """
            SELECT 
                issue_type,
                live_date,
                segment,
                slot,
                end_date,
                request_type,
                monetary_type,
                cpc,
                product_id,
                akeneo_product_name,
                akeneo_brand_name,
                selling_price,
                projected_inventory,
                brand,
                preferred_landing_sku_id,
                property,
                funnel,
                mv,
                top_bet_date,
                campaign_name,
                top_bet,
                article_type,
                akeneo_family,
                MRP,
                segment_in,
                remarks,
                price_remarks,
                user_email,
                impressions,
                tacos,
                `index`,
                available_inventory
            FROM campaigns
            WHERE 1=1
            """
            
            params = {}
            conditions = []
            
            if filters:
                # Filter by campaign types
                if filters.campaign_types:
                    placeholders = ','.join([f':campaign_type_{i}' for i in range(len(filters.campaign_types))])
                    conditions.append(f"issue_type IN ({placeholders})")
                    for i, campaign_type in enumerate(filters.campaign_types):
                        params[f'campaign_type_{i}'] = campaign_type
                
                # Filter by segment
                if filters.segment:
                    conditions.append("segment = :segment")
                    params['segment'] = filters.segment
                
                # Filter by brand
                if filters.brand:
                    conditions.append("brand = :brand")
                    params['brand'] = filters.brand
                
                # Filter by date range
                if filters.start_date:
                    conditions.append("STR_TO_DATE(live_date, '%d/%m/%Y') >= :start_date")
                    params['start_date'] = filters.start_date.strftime('%Y-%m-%d')
                
                if filters.end_date:
                    conditions.append("STR_TO_DATE(end_date, '%d/%m/%Y') <= :end_date")
                    params['end_date'] = filters.end_date.strftime('%Y-%m-%d')
                
                # Filter for active campaigns only
                if filters.active_only:
                    conditions.append("""
                        STR_TO_DATE(live_date, '%d/%m/%Y') <= CURDATE() 
                        AND STR_TO_DATE(end_date, '%d/%m/%Y') >= CURDATE()
                    """)
            
            # Add conditions to query
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            
            # Add ordering
            base_query += " ORDER BY STR_TO_DATE(live_date, '%d/%m/%Y') DESC"
            
            # Execute query
            result = db.execute(text(base_query), params)
            rows = result.fetchall()
            
            # Convert to RawCampaignData objects
            campaigns = []
            for row in rows:
                try:
                    campaign = RawCampaignData(
                        issue_type=row.issue_type or "",
                        live_date=row.live_date or "",
                        segment=row.segment or "",
                        slot=row.slot,
                        end_date=row.end_date or "",
                        request_type=row.request_type or "",
                        monetary_type=row.monetary_type,
                        cpc=row.cpc,
                        product_id=row.product_id or "",
                        akeneo_product_name=row.akeneo_product_name,
                        akeneo_brand_name=row.akeneo_brand_name,
                        selling_price=float(row.selling_price) if row.selling_price else 0.0,
                        projected_inventory=row.projected_inventory,
                        brand=row.brand,
                        preferred_landing_sku_id=row.preferred_landing_sku_id,
                        property=row.property,
                        funnel=row.funnel,
                        mv=row.mv,
                        top_bet_date=row.top_bet_date,
                        campaign_name=row.campaign_name,
                        top_bet=row.top_bet,
                        article_type=row.article_type,
                        akeneo_family=row.akeneo_family,
                        MRP=float(row.MRP) if row.MRP else None,
                        segment_in=row.segment_in,
                        remarks=row.remarks,
                        price_remarks=row.price_remarks,
                        user_email=row.user_email,
                        impressions=row.impressions,
                        tacos=float(row.tacos) if row.tacos else None,
                        index=row.index,
                        available_inventory=row.available_inventory
                    )
                    campaigns.append(campaign)
                    
                except Exception as e:
                    logger.error(f"Error parsing campaign row: {e}")
                    continue
            
            logger.info(f"Fetched {len(campaigns)} campaigns from database")
            return campaigns
            
        except Exception as e:
            logger.error(f"Error fetching campaigns from database: {e}")
            raise
    
    def get_campaign_types(self, db: Session) -> List[str]:
        """
        Get all available campaign types
        
        Args:
            db: Database session
            
        Returns:
            List of unique campaign types
        """
        try:
            query = "SELECT DISTINCT issue_type FROM campaigns WHERE issue_type IS NOT NULL ORDER BY issue_type"
            result = db.execute(text(query))
            campaign_types = [row.issue_type for row in result.fetchall()]
            return campaign_types
            
        except Exception as e:
            logger.error(f"Error fetching campaign types: {e}")
            return []
    
    def get_segments(self, db: Session) -> List[str]:
        """
        Get all available segments
        
        Args:
            db: Database session
            
        Returns:
            List of unique segments
        """
        try:
            query = "SELECT DISTINCT segment FROM campaigns WHERE segment IS NOT NULL ORDER BY segment"
            result = db.execute(text(query))
            segments = [row.segment for row in result.fetchall()]
            return segments
            
        except Exception as e:
            logger.error(f"Error fetching segments: {e}")
            return []
    
    def get_brands(self, db: Session) -> List[str]:
        """
        Get all available brands
        
        Args:
            db: Database session
            
        Returns:
            List of unique brands
        """
        try:
            query = "SELECT DISTINCT brand FROM campaigns WHERE brand IS NOT NULL ORDER BY brand"
            result = db.execute(text(query))
            brands = [row.brand for row in result.fetchall()]
            return brands
            
        except Exception as e:
            logger.error(f"Error fetching brands: {e}")
            return []
    
    def get_campaign_by_product_id(self, db: Session, product_id: str) -> Optional[RawCampaignData]:
        """
        Get campaign data for a specific product
        
        Args:
            db: Database session
            product_id: Product identifier
            
        Returns:
            RawCampaignData object or None if not found
        """
        try:
            query = """
            SELECT 
                issue_type,
                live_date,
                segment,
                slot,
                end_date,
                request_type,
                monetary_type,
                cpc,
                product_id,
                akeneo_product_name,
                akeneo_brand_name,
                selling_price,
                projected_inventory,
                brand,
                preferred_landing_sku_id,
                property,
                funnel,
                mv,
                top_bet_date,
                campaign_name,
                top_bet,
                article_type,
                akeneo_family,
                MRP,
                segment_in,
                remarks,
                price_remarks,
                user_email,
                impressions,
                tacos,
                `index`,
                available_inventory
            FROM campaigns
            WHERE product_id = :product_id
            LIMIT 1
            """
            
            result = db.execute(text(query), {"product_id": product_id})
            row = result.fetchone()
            
            if row:
                return RawCampaignData(
                    issue_type=row.issue_type or "",
                    live_date=row.live_date or "",
                    segment=row.segment or "",
                    slot=row.slot,
                    end_date=row.end_date or "",
                    request_type=row.request_type or "",
                    monetary_type=row.monetary_type,
                    cpc=row.cpc,
                    product_id=row.product_id or "",
                    akeneo_product_name=row.akeneo_product_name,
                    akeneo_brand_name=row.akeneo_brand_name,
                    selling_price=float(row.selling_price) if row.selling_price else 0.0,
                    projected_inventory=row.projected_inventory,
                    brand=row.brand,
                    preferred_landing_sku_id=row.preferred_landing_sku_id,
                    property=row.property,
                    funnel=row.funnel,
                    mv=row.mv,
                    top_bet_date=row.top_bet_date,
                    campaign_name=row.campaign_name,
                    top_bet=row.top_bet,
                    article_type=row.article_type,
                    akeneo_family=row.akeneo_family,
                    MRP=float(row.MRP) if row.MRP else None,
                    segment_in=row.segment_in,
                    remarks=row.remarks,
                    price_remarks=row.price_remarks,
                    user_email=row.user_email,
                    impressions=row.impressions,
                    tacos=float(row.tacos) if row.tacos else None,
                    index=row.index,
                    available_inventory=row.available_inventory
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching campaign for product {product_id}: {e}")
            return None 