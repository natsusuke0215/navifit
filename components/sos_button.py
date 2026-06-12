import httpx
from nicegui import ui

def add_sos_button(base_url: str = ''):
    dialog = ui.dialog()

    with dialog, ui.card().classes('w-full max-w-md p-4 bg-white rounded-2xl'):
        with ui.row().classes('items-center justify-between w-full mb-2'):
            ui.label('緊急連絡').classes('text-xl font-bold text-red-600')
            ui.button(icon='close', on_click=dialog.close).props('flat round dense text-color=gray')

        ui.label('状況に応じて適切な連絡先を選択してください').classes('text-gray-500 text-sm mb-4')
        container = ui.column().classes('w-full gap-3')

    async def open_sos():
        container.clear()
        with container:
            ui.spinner(size='lg').classes('self-center')
        dialog.open()

        try:
            resp = await httpx.AsyncClient(base_url=base_url).get('/api/sos/channels')
            if resp.status_code == 200:
                channels = resp.json()
            else:
                channels = []
        except Exception as e:
            print("Error fetching SOS channels:", e)
            channels = []
            
        container.clear()
        ICON_MAP = {"police":"🚔", "hospital":"🏥", "embassy":"🏛️", "other":"📞"}
        
        with container:
            if not channels:
                ui.label('緊急連絡先を読み込めませんでした').classes('text-red-500 text-center w-full')

            for ch in channels:
                icon = ICON_MAP.get(ch['type'], '📞')
                phone = ch['phone']
                display_name = ch.get('name_ja') or ch.get('name') or ''
                sub_name = ch.get('name') if ch.get('name_ja') else ''

                async def copy_phone(p=phone):
                    await ui.run_javascript(f"navigator.clipboard.writeText('{p}')")
                    ui.notify(f'コピーしました: {p}', type='positive', position='top')

                with ui.card().classes('w-full p-3 shadow-sm border'):
                    with ui.row().classes('items-center gap-3 w-full flex-nowrap'):
                        ui.label(icon).classes('text-3xl')
                        with ui.column().classes('flex-1 gap-0'):
                            ui.label(display_name).classes('font-semibold text-base leading-tight')
                            if sub_name:
                                ui.label(sub_name).classes('text-gray-400 text-sm')
                            ui.label(phone).classes('text-blue-600 font-bold text-lg mt-1')
                        with ui.column().classes('gap-1 items-end'):
                            ui.button('📋 コピー', on_click=copy_phone) \
                                .props('color=grey-6 dense no-caps').classes('text-sm px-3')
            
    # Ép z-index cho wrapper sticky để nổi trên Leaflet map
    ui.add_head_html('<style>.q-page-sticky { z-index: 9999 !important; }</style>')

    with ui.page_sticky(position='bottom-right', x_offset=20, y_offset=20):
        ui.button('SOS', on_click=open_sos) \
            .classes('rounded-full w-16 h-16 text-white font-bold text-lg shadow-xl hover:scale-110 transition-transform flex items-center justify-center') \
            .style('background: #DC2626; border: none;')
