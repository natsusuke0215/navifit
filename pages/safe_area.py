from nicegui import ui

@ui.page('/safe-area')
async def safe_area_page():
    ui.navigate.to('/')
