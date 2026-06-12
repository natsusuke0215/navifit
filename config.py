import os

# API Base URL configuration
# On Railway: Set API_BASE_URL environment variable to your app domain
# Example: API_BASE_URL=https://navifit-production.up.railway.app
# If not set, defaults to localhost for local development
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")
