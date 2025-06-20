# Store Operations Automation

This FastAPI application automates the manual process of fetching campaign data from the database, transforming it with Akeneo product information, and formatting it for Falcon API integration.

## Overview

The system replaces the manual workflow where ops teams:
1. Download Excel sheets from Tableau/Databricks
2. Manually format and filter data
3. Calculate MOP costs (selling_price * 0.979)
4. Upload to Falcon dashboard at specific times

### Features

- **Milestone 1** ✅: Direct database integration for campaign data fetching
- **Milestone 2** 🚧: Falcon API integration (planned)
- Akeneo PIM integration for product details
- Automated price calculations
- Excel export functionality
- Web dashboard for ops team
- REST API for programmatic access

## Project Structure

```
store-ops-auto/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   └── config.py          # Application configuration
│   ├── models/
│   │   ├── campaign.py        # Campaign data models
│   │   └── akeneo.py          # Akeneo data models
│   ├── services/
│   │   ├── database_service.py # Database operations
│   │   ├── campaign_service.py # Campaign data processing
│   │   └── akeneo_service.py   # Akeneo integration
│   ├── api/
│   │   └── routes/
│   │       ├── campaigns.py    # Campaign API endpoints
│   │       └── dashboard.py    # Dashboard web routes
│   ├── database/
│   │   └── connection.py      # Database connection setup
│   └── templates/
│       ├── base.html          # Base template
│       ├── dashboard.html     # Main dashboard
│       └── error.html         # Error page
├── requirements.txt
├── pyproject.toml
├── env.example
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- MySQL database with campaign data
- Akeneo PIM access credentials
- `uv` package manager (recommended) or `pip`

### Installation

1. **Clone and setup environment:**
   ```bash
   cd store-ops-auto
   ```

2. **Install dependencies using uv:**
   ```bash
   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install dependencies
   uv sync
   ```

   **Or using pip:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your actual configuration
   ```

4. **Environment Variables:**
   ```env
   # Database Configuration
   DB_HOST=your_mysql_host
   DB_PORT=3306
   DB_NAME=your_database_name
   DB_USER=your_username
   DB_PASSWORD=your_password

   # Akeneo Configuration
   AKENEO_URL=https://your-akeneo-instance.com
   AKENEO_CLIENT_ID_SECRET=your_base64_encoded_credentials
   AKENEO_USERNAME=your_akeneo_username
   AKENEO_PASSWORD=your_akeneo_password

   # Falcon API (for Milestone 2)
   FALCON_API_URL=https://your-falcon-api.com
   FALCON_API_KEY=your_api_key
   ```

### Running the Application

1. **Start the development server:**
   ```bash
   # Using uv
   uv run uvicorn app.main:app --reload

   # Or with activated venv
   uvicorn app.main:app --reload
   ```

2. **Access the application:**
   - Web Dashboard: http://localhost:8000/dashboard/
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## Usage

### Web Dashboard

The web dashboard provides a user-friendly interface for ops teams:

1. **Main Dashboard** (`/dashboard/`):
   - Overview of available campaign types, segments, and brands
   - Quick actions for viewing active campaigns and exporting data
   - System information and API endpoints

2. **Campaign Management** (`/dashboard/campaigns`):
   - Filter campaigns by type, segment, brand
   - View active campaigns only
   - Process and export campaign data

### API Endpoints

#### Campaign Data

- `GET /api/v1/campaigns` - Get campaigns with optional filters
- `GET /api/v1/campaigns/active` - Get only active campaigns
- `GET /api/v1/campaigns/export` - Export campaigns to Excel
- `GET /api/v1/campaigns/summary` - Get campaign statistics
- `GET /api/v1/campaigns/product/{product_id}` - Get campaign for specific product

#### Filter Options

- `GET /api/v1/campaigns/types` - Get available campaign types
- `GET /api/v1/campaigns/segments` - Get available segments  
- `GET /api/v1/campaigns/brands` - Get available brands

#### Validation

- `POST /api/v1/campaigns/validate` - Validate campaign data

### Example API Usage

```bash
# Get active DOD campaigns
curl "http://localhost:8000/api/v1/campaigns/active?campaign_types=DOD"

# Export active campaigns to Excel
curl "http://localhost:8000/api/v1/campaigns/export?active_only=true" -o campaigns.xlsx

# Get campaign summary
curl "http://localhost:8000/api/v1/campaigns/summary"
```

## Data Flow

1. **Raw Campaign Data** (MySQL):
   ```
   issue_type, live_date, segment, end_date, product_id, 
   selling_price, preferred_landing_sku_id, property, etc.
   ```

2. **Akeneo Integration**:
   - Fetch product details and SKU mappings
   - Get MRP values from product catalog

3. **Transformation**:
   - Calculate MOP cost: `selling_price * 0.979`
   - Map product_id to sku_id
   - Format for Falcon API requirements

4. **Output Format** (Falcon-ready):
   ```
   sku_id, product_id, MRP, MOP, selling_price, 
   mop_cost, selling_price_cost, coins
   ```

## Configuration

### Database Schema

Ensure your MySQL database has a `campaigns` table with these columns:
- `issue_type`, `live_date`, `segment`, `end_date`
- `product_id`, `selling_price`, `MRP`
- `preferred_landing_sku_id`, `property`
- Other fields as per your data structure

### Akeneo Integration

The system expects Akeneo products to have:
- SKU attributes for product identification
- MRP/price attributes
- Asset collections for product images

## Development

### Adding New Features

1. **Models**: Add new Pydantic models in `app/models/`
2. **Services**: Implement business logic in `app/services/`
3. **Routes**: Add API endpoints in `app/api/routes/`
4. **Templates**: Create HTML templates in `app/templates/`

### Testing

```bash
# Run tests (when implemented)
uv run pytest

# Or with activated venv
pytest
```

## Deployment

### Production Setup

1. **Environment Configuration**:
   - Set `DEBUG=false`
   - Configure proper database credentials
   - Set up SSL certificates

2. **Using Docker** (recommended):
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY . .
   RUN pip install -r requirements.txt
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

3. **Using systemd**:
   ```bash
   # Create service file
   sudo cp store-ops.service /etc/systemd/system/
   sudo systemctl enable store-ops
   sudo systemctl start store-ops
   ```

## Roadmap

### Milestone 1 ✅
- [x] Database integration
- [x] Akeneo integration  
- [x] Data transformation
- [x] Excel export
- [x] Web dashboard
- [x] REST API

### Milestone 2 🚧
- [ ] Falcon API integration
- [ ] Automated campaign scheduling
- [ ] Real-time campaign status updates
- [ ] Email notifications
- [ ] Advanced filtering and search

### Future Enhancements
- [ ] Authentication and authorization
- [ ] Audit logging
- [ ] Performance monitoring
- [ ] Caching layer
- [ ] Batch processing
- [ ] Mobile-responsive dashboard

## Troubleshooting

### Common Issues

1. **Database Connection Failed**:
   - Check database credentials in `.env`
   - Ensure MySQL server is running
   - Verify network connectivity

2. **Akeneo Authentication Failed**:
   - Verify Akeneo credentials
   - Check if base64 encoding is correct
   - Ensure API permissions are granted

3. **Excel Export Failed**:
   - Check write permissions in application directory
   - Ensure openpyxl is installed correctly

### Logging

Application logs are available at the INFO level. Set `LOG_LEVEL=DEBUG` for detailed debugging.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For support and questions:
- Check the API documentation at `/docs`
- Review the troubleshooting section
- Create an issue in the repository 