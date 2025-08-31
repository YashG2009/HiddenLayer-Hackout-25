#!/usr/bin/env python3
"""
Simple test to verify Flask app works with blockchain integration.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_flask_app():
    """Test basic Flask app functionality."""
    try:
        # Import the Flask app
        from proto_v3_migrated import app, load_data, APP_DATA
        
        print("✅ Flask app imported successfully")
        
        # Test data loading
        load_data()
        print(f"✅ Data loaded: {len(APP_DATA.get('users', {}))} users")
        
        # Test app configuration
        app.config['TESTING'] = True
        client = app.test_client()
        
        # Test login page
        response = client.get('/login')
        if response.status_code == 200:
            print("✅ Login page loads successfully")
        else:
            print(f"❌ Login page failed: {response.status_code}")
            return False
        
        # Test service status (requires login)
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'GovtAdmin'
            sess['role'] = 'Government'
        
        response = client.get('/service-status')
        if response.status_code == 200:
            print("✅ Service status endpoint works")
            import json
            data = json.loads(response.data)
            print(f"   - AI Service: {'Available' if data['ai_service']['available'] else 'Unavailable'}")
            print(f"   - Blockchain: {data['blockchain_service']['backend']} backend")
        else:
            print(f"❌ Service status failed: {response.status_code}")
            return False
        
        # Test dashboard
        response = client.get('/')
        if response.status_code == 200:
            print("✅ Dashboard loads successfully")
        else:
            print(f"❌ Dashboard failed: {response.status_code}")
            return False
        
        print("\n🎉 All Flask app tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_flask_app()
    sys.exit(0 if success else 1)