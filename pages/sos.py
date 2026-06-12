import httpx
from nicegui import ui
from fastapi import Request

@ui.page('/sos')
async def sos_page(request: Request):
    ui.page_title('NaviFit — 緊急連絡')
    ICON_MAP = {"police":"🚔", "hospital":"🏥", "embassy":"🏛️", "other":"📞"}

    with ui.column().classes('max-w-lg mx-auto p-4 gap-4 w-full'):
        # Header
        with ui.row().classes('items-center gap-3 w-full'):
            ui.button('←', on_click=ui.navigate.back).classes('text-gray-500').props('flat round dense')
            ui.label('緊急連絡').classes('text-xl font-bold text-red-600 flex-1')

        ui.label('状況に応じて適切な連絡先を選択してください').classes('text-gray-500 text-sm')

        # Danh sách kênh
        channels = []
        try:
            resp = await httpx.AsyncClient(base_url=str(request.base_url), timeout=10.0).get('/api/sos/channels')
            resp.raise_for_status()
            channels = resp.json()
        except httpx.HTTPStatusError as e:
            ui.notify(f'サーバーエラー: {e.response.status_code}', type='negative')
        except httpx.RequestError:
            ui.notify('サーバーに接続できません。ネットワークを確認してください。', type='negative')
        except Exception as e:
            print("Error fetching SOS channels:", e)
            ui.notify('緊急連絡先を読み込めませんでした', type='negative')
        
        for ch in channels:
            icon = ICON_MAP.get(ch['type'], '📞')
            display_name = ch.get('name_ja') or ch.get('name') or ''
            sub_name = ch.get('name') if ch.get('name_ja') else ''
            with ui.card().classes('w-full p-4 shadow-sm border'):
                with ui.row().classes('items-center gap-3 w-full flex-nowrap'):
                    ui.label(icon).classes('text-3xl')
                    with ui.column().classes('flex-1 gap-0'):
                        ui.label(display_name).classes('font-semibold text-base leading-tight')
                        if sub_name:
                            ui.label(sub_name).classes('text-gray-400 text-sm')
                        ui.label(ch['phone']).classes('text-blue-600 font-bold text-lg mt-1')
                    with ui.column().classes('gap-2 items-end'):
                        ui.link('📞 電話', target=f"tel:{ch['phone']}").classes('bg-green-500 text-white px-3 py-1 rounded-lg text-sm no-underline font-medium')
                        ui.link('💬 SMS', target=f"sms:{ch['phone']}").classes('bg-blue-500 text-white px-3 py-1 rounded-lg text-sm no-underline font-medium')
