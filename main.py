from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from nicegui import app as nicegui_app, ui

# 1. Tạo FastAPI app
fastapi_app = FastAPI(title="NaviFit API")

# 4. Setup CORS cho FastAPI để browser có thể gọi API
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@fastapi_app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "detail": "Lỗi server, vui lòng thử lại"}
    )

# 2. Tạo router cơ bản cho FastAPI
@fastapi_app.get("/health")
def health_check():
    return {"status": "ok"}

from api.places import router as places_router
from api.aqi import router as aqi_router
from api.sos import router as sos_router
fastapi_app.include_router(places_router, prefix="/places")
fastapi_app.include_router(aqi_router)
fastapi_app.include_router(sos_router)

# Mount FastAPI app vào NiceGUI app tại đường dẫn /api
nicegui_app.mount('/api', fastapi_app)

# Serve static files (logo, ảnh...)
nicegui_app.add_static_files('/static', 'static')

# 3. Cấu trúc trang NiceGUI
def header():
    """Header component dùng chung"""
    with ui.header().classes('items-center justify-between bg-blue-600 text-white p-4'):
        ui.label('NaviFit').classes('text-2xl font-bold cursor-pointer').on('click', lambda: ui.navigate.to('/'))
        
        with ui.row().classes('gap-2'):
            ui.button('Trang chủ', on_click=lambda: ui.navigate.to('/')).props('flat color=white')
            ui.button('Tìm Địa Điểm', on_click=lambda: ui.navigate.to('/search')).props('flat color=white')
            ui.button('AQI', on_click=lambda: ui.navigate.to('/aqi')).props('flat color=white')
            ui.button('SOS', on_click=lambda: ui.navigate.to('/sos')).props('color=red text-white')

import pages.home
import pages.detail
import pages.search
import pages.sos
import pages.safe_area

@ui.page('/aqi')
def aqi_page():
    header()
    with ui.column().classes('w-full items-center p-8'):
        ui.label('Chất lượng không khí (AQI)').classes('text-2xl font-bold mb-4')
        ui.label('Bản đồ AQI sẽ hiển thị ở đây.')

from database import init_db, seed_data

@nicegui_app.on_startup
async def startup_db():
    try:
        await init_db()
        await seed_data()
        print("Database initialized and sample data seeded successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")


# Khởi chạy ứng dụng
if __name__ in {"__main__", "__mp_main__"}:
    # Do cổng 8080 của bạn bị báo lỗi [WinError 10013] (port đang được dùng), 
    # chúng ta chạy cả UI và API chung trên port 8081
    ui.run(title='NaviFit', port=8081, reload=True, storage_secret='navifit-secret-key-2025')
