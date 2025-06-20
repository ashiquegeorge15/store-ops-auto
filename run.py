#!/usr/bin/env python3
"""
Run script for Store Operations Automation
"""
import os
import sys
import uvicorn
from app.core.config import settings
from app.database.connection import test_connection, init_db

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME',
        'AKENEO_URL', 'AKENEO_CLIENT_ID_SECRET', 'AKENEO_USERNAME', 'AKENEO_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please create a .env file with the required configuration.")
        print("See env.example for reference.")
        return False
    
    print("✅ Environment variables configured")
    return True

def check_database():
    """Test database connection"""
    print("🔍 Testing database connection...")
    try:
        if test_connection():
            print("✅ Database connection successful")
            
            # Initialize database tables
            print("🏗️  Initializing database tables...")
            init_db()
            print("✅ Database tables initialized")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    """Main function to run the application"""
    print("🚀 Starting Store Operations Automation")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Check database
    if not check_database():
        print("\n💡 Troubleshooting tips:")
        print("- Ensure MySQL server is running")
        print("- Check database credentials in .env file")
        print("- Verify network connectivity to database")
        sys.exit(1)
    
    print("\n🎯 All checks passed! Starting application...")
    print(f"🌐 Dashboard: http://localhost:8000/dashboard/")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print(f"❤️  Health Check: http://localhost:8000/health")
    print("=" * 50)
    
    # Start the application
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=settings.DEBUG,
            log_level=settings.LOG_LEVEL.lower()
        )
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 