import requests
import logging
from typing import Optional, List, Dict, Any

from app.core.config import settings
from app.models.akeneo import ProductDetails, Value, LinkedData, AkeneoTokenResponse, Asset

logger = logging.getLogger(__name__)


class AssetService:
    """Service for handling Akeneo assets"""
    
    def __init__(self):
        self.base_url = settings.AKENEO_URL
        self._access_token: Optional[str] = None
    
    def set_access_token(self, token: str):
        """Set access token for asset service"""
        self._access_token = token
    
    def get_assets_for_collection(self, asset_codes: List[str], asset_family_code: str) -> List[Dict[str, Any]]:
        """
        Get assets for a collection of asset codes
        
        Args:
            asset_codes: List of asset codes
            asset_family_code: Asset family code
            
        Returns:
            List of asset data
        """
        if not self._access_token:
            logger.warning("No access token available for asset service")
            return []
        
        assets = []
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._access_token}"
        }
        
        for asset_code in asset_codes:
            try:
                response = requests.get(
                    f"{self.base_url}/api/rest/v1/asset-families/{asset_family_code}/assets/{asset_code}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    assets.append(response.json())
                else:
                    logger.warning(f"Failed to fetch asset {asset_code}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error fetching asset {asset_code}: {e}")
                
        return assets


class AkeneoService:
    """Service for interacting with Akeneo PIM"""
    
    def __init__(self):
        self.base_url = settings.AKENEO_URL
        self._access_token: Optional[str] = None
        self.asset_service = AssetService()
    
    def _get_access_token(self) -> str:
        """
        Get access token from Akeneo
        
        Returns:
            Access token string
            
        Raises:
            Exception: If token retrieval fails
        """
        if self._access_token:
            return self._access_token
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {settings.AKENEO_CLIENT_ID_SECRET}"
        }
        
        data = {
            "grant_type": "password",
            "username": settings.AKENEO_USERNAME,
            "password": settings.AKENEO_PASSWORD
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/oauth/v1/token",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self._access_token = token_data.get("access_token")
                self.asset_service.set_access_token(self._access_token)
                return self._access_token
            else:
                raise Exception(f"Failed to get token: {response.status_code}, {response.text}")
                
        except Exception as e:
            logger.error(f"Error getting access token: {e}")
            raise
    
    def fetch_assets_for_value(self, value: Value) -> None:
        """
        Fetch assets for a value if it's an asset collection
        
        Args:
            value: The product value
        """
        if value.attribute_type == "pim_catalog_asset_collection" and isinstance(value.data, list):
            # Get the reference_data_name to use as asset_family_code
            asset_family_code = value.reference_data_name if value.reference_data_name else "pdp_scroll"
            
            # Fetch assets
            assets = self.asset_service.get_assets_for_collection(value.data, asset_family_code)
            
            # Set the assets in the value object
            value.assets = assets
    
    def get_product(self, product_id: str) -> ProductDetails:
        """
        Retrieve product details by ID
        
        Args:
            product_id: Product identifier
            
        Returns:
            ProductDetails object
            
        Raises:
            Exception: If product retrieval fails
        """
        logger.info(f"Getting product data for product_id: {product_id}")
        
        token = self._get_access_token()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/api/rest/v1/products/{product_id}?with_attribute_options=true",
                headers=headers
            )
            
            if response.status_code == 200:
                product_data = response.json()
                
                # Convert raw values to Value objects
                values_dict = {}
                for key, value_list in product_data["values"].items():
                    values_dict[key] = []
                    for val in value_list:
                        value = Value(
                            locale=val.get("locale"),
                            scope=val.get("scope"),
                            data=val.get("data"),
                            linked_data=LinkedData(**val.get("linked_data", {})) if "linked_data" in val else None,
                            reference_data_name=val.get("reference_data_name"),
                            attribute_type=val.get("attribute_type")
                        )
                        
                        # If this is an asset collection, fetch the assets
                        if val.get("attribute_type") == "pim_catalog_asset_collection":
                            self.fetch_assets_for_value(value)
                        
                        values_dict[key].append(value)
                
                return ProductDetails(
                    id=product_data["identifier"],
                    family=product_data.get("family", ""),
                    parent=product_data.get("parent", None),
                    values=values_dict
                )
            else:
                raise Exception(f"Failed to get product: {response.status_code}, {response.text}")
                
        except Exception as e:
            logger.error(f"Error getting product {product_id}: {e}")
            raise
    
    def get_product_sku_mapping(self, product_id: str) -> Optional[str]:
        """
        Get SKU ID for a product
        
        Args:
            product_id: Product identifier
            
        Returns:
            SKU ID if found, None otherwise
        """
        try:
            product = self.get_product(product_id)
            
            # Try to extract SKU from product values
            # This might need adjustment based on your Akeneo attribute structure
            if "sku" in product.values and product.values["sku"]:
                return product.values["sku"][0].data
            
            # Fallback to product ID if no specific SKU attribute
            return product_id
            
        except Exception as e:
            logger.error(f"Error getting SKU for product {product_id}: {e}")
            return None
    
    def get_product_mrp(self, product_id: str) -> Optional[float]:
        """
        Get MRP for a product from Akeneo
        
        Args:
            product_id: Product identifier
            
        Returns:
            MRP value if found, None otherwise
        """
        try:
            product = self.get_product(product_id)
            
            # Try to extract MRP from product values
            # Adjust these attribute names based on your Akeneo setup
            mrp_attributes = ["mrp", "MRP", "maximum_retail_price", "list_price"]
            
            for attr in mrp_attributes:
                if attr in product.values and product.values[attr]:
                    value = product.values[attr][0].data
                    if value is not None:
                        return float(value)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting MRP for product {product_id}: {e}")
            return None 