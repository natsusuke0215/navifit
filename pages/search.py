import httpx
import json
from nicegui import ui, app

# SVG icon phụ nữ mặc kimono Nhật Bản
JP_WOMAN_SVG = '''<svg width="22" height="28" viewBox="0 0 22 28" xmlns="http://www.w3.org/2000/svg">
  <path d="M5 9 Q5 3 11 3 Q17 3 17 9 Q17 6 11 7.5 Q5 6 5 9Z" fill="#2d1b0e"/>
  <ellipse cx="11" cy="9" rx="4.5" ry="5" fill="#f5cba7"/>
  <circle cx="8" cy="4.5" r="1.3" fill="#c0392b"/>
  <rect x="7.5" y="3.5" width="3" height="1" rx="0.5" fill="#c0392b"/>
  <path d="M2 28 L6 14 L11 12 L16 14 L20 28Z" fill="#c0392b"/>
  <path d="M9 13.5 L11 12 L13 13.5 L11 21Z" fill="white"/>
  <rect x="6" y="18.5" width="10" height="2.5" rx="1.25" fill="#8B0000"/>
  <rect x="15" y="17.5" width="4" height="4" rx="1" fill="#8B0000"/>
</svg>'''

SAFETY_CONFIG = {
    1: ('安全',       '#4CAF50', 'white'),
    2: ('まあ安全',    '#FFC107', '#333'),
    3: ('かなり安全',  '#FF9800', 'white'),
    4: ('危険',       '#F44336', 'white'),
}

def aqi_to_badge(aqi_value: int) -> tuple:
    if aqi_value <= 50:
        return 'AQI いい', '#4CAF50', 'white'
    elif aqi_value <= 100:
        return 'AQI 普通', '#FFC107', '#333'
    elif aqi_value <= 150:
        return 'AQI 悪い', '#FF9800', 'white'
    else:
        return 'AQI 最悪', '#F44336', 'white'


@ui.page('/search')
async def search_page(q: str = '', lat: float = 21.006847, lng: float = 105.843058):
    ui.page_title('NaviFit — Tìm kiếm')

    japanese_filter = bool(app.storage.user.get('japanese_only', False))

    # Lấy AQI một lần cho toàn khu vực
    aqi_label, aqi_color, aqi_text_color = 'AQI いい', '#4CAF50', 'white'
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            aqi_res = await client.get(f'http://127.0.0.1:8081/api/aqi?lat={lat}&lng={lng}')
            if aqi_res.status_code == 200:
                aqi_data = aqi_res.json()
                aqi_label, aqi_color, aqi_text_color = aqi_to_badge(aqi_data.get('aqi_value', 0))
    except Exception:
        pass

    CAT_LABELS = {
        'gym': '🏋️ Phòng gym',
        'park': '🌳 Công viên',
        'pool': '🏊 Hồ bơi',
        'badminton': '🏸 Cầu lông',
        'tennis': '🎾 Tennis',
        'pickleball': '🏓 Pickleball',
        'hospital': '🏥 Bệnh viện',
        'police': '👮 Công an',
    }

    # Từ khóa → category
    CAT_KEYWORDS = {
        'gym': 'gym', 'phòng gym': 'gym', 'phòng tập': 'gym', 'thể hình': 'gym', 'fitness': 'gym',
        'park': 'park', 'công viên': 'park', 'vườn hoa': 'park',
        'pool': 'pool', 'hồ bơi': 'pool', 'bể bơi': 'pool', 'bơi': 'pool',
        'badminton': 'badminton', 'cầu lông': 'badminton', 'sân cầu': 'badminton',
        'tennis': 'tennis', 'sân tennis': 'tennis',
        'pickleball': 'pickleball', 'sân pickleball': 'pickleball', 'pickball': 'pickleball',
        'hospital': 'hospital', 'bệnh viện': 'hospital',
        'police': 'police', 'công an': 'police', 'trụ sở công an': 'police', 'đồn công an': 'police',
    }

    async def fetch_places(japanese_only: bool = False) -> tuple:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                japanese_str = 'true' if japanese_only else 'false'
                url = f'http://127.0.0.1:8081/api/places/nearby?lat={lat}&lng={lng}&radius=20000&japanese_only={japanese_str}'
                res = await client.get(url)
                res.raise_for_status()
                all_places = res.json()

                all_real = [p for p in all_places
                            if not p.get('is_separator')
                            and (not japanese_only or p.get('has_japanese_support'))]

                if q:
                    q_lower = q.lower().strip()
                    target_cat = CAT_KEYWORDS.get(q_lower)

                    matched = []
                    for p in all_real:
                        by_cat  = target_cat and p.get('category') == target_cat
                        by_text = (q_lower in p.get('name', '').lower()
                                   or q_lower in (p.get('name_ja') or '').lower()
                                   or q_lower in p.get('address', '').lower())
                        if by_cat or by_text:
                            matched.append(p)

                    suggestions = []
                    if matched:
                        cat = matched[0].get('category')
                        if cat:
                            matched_ids = {p['id'] for p in matched}
                            suggestions = [p for p in all_real
                                           if p.get('category') == cat
                                           and p['id'] not in matched_ids][:6]
                    return matched, suggestions

                return all_real, []
        except httpx.HTTPStatusError as e:
            ui.notify(f'Lỗi server: {e.response.status_code}', type='negative')
        except httpx.RequestError:
            ui.notify('Không thể kết nối server.', type='negative')
        except Exception as e:
            ui.notify(f'Lỗi: {str(e)}', type='negative')
        return [], []

    places, suggestions = await fetch_places(japanese_filter)

    CAT_DISPLAY = {
        'gym': 'phòng gym', 'park': 'công viên', 'pool': 'hồ bơi',
        'badminton': 'sân cầu lông', 'tennis': 'sân tennis',
        'pickleball': 'sân pickleball', 'hospital': 'bệnh viện', 'police': 'công an',
    }

    def build_display(matched: list, suggs: list) -> list:
        result = list(matched)
        if suggs:
            cat = matched[0].get('category', '') if matched else ''
            lbl = f"Một số {CAT_DISPLAY.get(cat, 'địa điểm')} khác"
            result.append({'is_separator': True, 'label': lbl})
            result.extend(suggs)
        return result

    display_places = build_display(places, suggestions)
    all_map_places = places + suggestions
    places_json = json.dumps(all_map_places)

    # ── Header ────────────────────────────────────────────────────────────────
    with ui.header().classes('items-center bg-white text-black shadow-md px-4 py-3 justify-between'):
        with ui.row().classes('items-center gap-2 flex-1 mr-4'):
            ui.html('<a href="/"><img src="/static/Logo.png" style="height:40px;width:auto;display:block;cursor:pointer;flex-shrink:0"></a>')
            with ui.row().classes('items-center flex-1 bg-gray-100 rounded-full px-3 py-1 gap-1'):
                ui.icon('search').classes('text-xl').style('color:#111;font-weight:900')
                search_input = ui.input(
                    value=q,
                    placeholder='Tìm địa điểm tập luyện...'
                ).props('borderless dense').classes('flex-1 text-sm bg-transparent')
                search_input.on('keydown.enter', lambda: ui.navigate.to(
                    f'/search?q={search_input.value}&lat={lat}&lng={lng}'))
        with ui.row().classes('items-center gap-2'):
            from components.aqi_button import add_aqi_button
            add_aqi_button('search-map')

            # Nút lọc tiếng Nhật ở header (số 5 trong mockup)
            jp_active_cls   = 'bg-green-600 text-white'
            jp_inactive_cls = 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            jp_base_cls = 'text-xs font-bold px-3 py-1 rounded-full cursor-pointer select-none border-0 transition-colors'
            jp_header_btn = ui.label('日本語対応').classes(
                f'{jp_base_cls} {jp_active_cls if japanese_filter else jp_inactive_cls}'
            )

    # ── Layout chính ──────────────────────────────────────────────────────────
    with ui.row().classes('w-full h-[calc(100vh-64px)] m-0 p-0 overflow-hidden flex-nowrap'):

        # ── Cột trái: Danh sách ───────────────────────────────────────────────
        with ui.column().classes('w-1/3 h-full overflow-y-auto p-4 border-r bg-gray-50 flex-shrink-0 gap-0'):

            ui.label(f'Kết quả: "{q}"' if q else 'Địa điểm xung quanh').classes('text-lg font-bold mb-3')

            results_container = ui.column().classes('w-full gap-1')
            selected = {'card': None}  # card đang được chọn

            def render_places(pl: list):
                results_container.clear()
                selected['card'] = None  # reset khi render lại
                real = [p for p in pl if not p.get('is_separator')]
                with results_container:
                    if not real:
                        with ui.column().classes('items-center p-8 text-gray-400 gap-2 w-full'):
                            ui.label('🔍').classes('text-4xl')
                            ui.label('Không tìm thấy địa điểm nào').classes('font-medium text-gray-500')
                            ui.label('Thử tìm kiếm với từ khóa khác').classes('text-sm text-center text-gray-400')
                        return

                    for place in pl:
                        if place.get('is_separator'):
                            ui.label(place.get('label', '──')).classes(
                                'text-gray-400 text-xs text-center py-2 w-full')
                            continue

                        has_jp = place.get('has_japanese_support', False)
                        safety_level = place.get('safety_level', 2)
                        safety_lbl, safety_bg, safety_tc = SAFETY_CONFIG.get(safety_level, SAFETY_CONFIG[2])

                        p_id   = place['id']
                        p_lat  = place['lat']
                        p_lng  = place['lng']
                        dist_m = place.get('distance', 0)
                        dist_str = f'{dist_m}m' if dist_m < 1000 else f'{dist_m / 1000:.1f}km'

                        SEL_ADD = 'bg-blue-100 shadow-md ring-2 ring-blue-400'
                        SEL_REM = 'hover:bg-blue-50 hover:shadow-md'

                        with ui.card().classes(
                            'w-full p-2 cursor-pointer hover:bg-blue-50 hover:shadow-md transition-all rounded-xl'
                        ) as card:
                            async def _card_click(pid=p_id, c=card):
                                if selected['card'] and selected['card'] != c:
                                    selected['card'].classes(remove=SEL_ADD, add=SEL_REM)
                                selected['card'] = c
                                c.classes(remove=SEL_REM, add=SEL_ADD)
                                await ui.run_javascript(f'highlightMarker({pid})')
                            card.on('click', _card_click)

                            with ui.row().classes('items-center gap-2 w-full flex-nowrap'):

                                # Cột badges (an toàn + AQI, xếp dọc)
                                with ui.column().classes('gap-1 flex-shrink-0 items-center'):
                                    ui.html(
                                        f'<span style="display:block;background:{safety_bg};color:{safety_tc};'
                                        f'padding:2px 7px;border-radius:5px;font-size:10px;font-weight:bold;'
                                        f'white-space:nowrap;text-align:center">{safety_lbl}</span>'
                                    )
                                    ui.html(
                                        f'<span style="display:block;background:{aqi_color};color:{aqi_text_color};'
                                        f'padding:2px 7px;border-radius:5px;font-size:10px;font-weight:bold;'
                                        f'white-space:nowrap;text-align:center">{aqi_label}</span>'
                                    )

                                # Icon phụ nữ Nhật (hiện nếu có hỗ trợ tiếng Nhật)
                                if has_jp:
                                    ui.html(
                                        f'<div style="flex-shrink:0;width:24px;height:30px;'
                                        f'display:flex;align-items:center;justify-content:center">'
                                        f'{JP_WOMAN_SVG}</div>'
                                    )
                                else:
                                    ui.html('<div style="flex-shrink:0;width:24px"></div>')

                                # Khoảng cách
                                ui.html(
                                    f'<span style="color:#555;font-size:11px;flex-shrink:0;white-space:nowrap">'
                                    f'📍 {dist_str}</span>'
                                )

                                # Tên + địa chỉ
                                with ui.column().classes('flex-1 min-w-0 gap-0'):
                                    ui.label(place.get('name', '')).classes(
                                        'font-semibold text-gray-800 text-sm leading-tight'
                                    ).style('overflow:hidden;text-overflow:ellipsis;white-space:nowrap')
                                    if place.get('address'):
                                        ui.label(place['address']).classes('text-gray-400 text-xs').style(
                                            'overflow:hidden;text-overflow:ellipsis;white-space:nowrap')

                                # Link chi tiết
                                ui.link('→', target=f'/detail/{p_id}').classes(
                                    'text-blue-500 font-bold text-sm flex-shrink-0 no-underline')

            render_places(display_places)

            # ── Handler toggle Japanese filter ────────────────────────────────
            async def toggle_jp_filter():
                nonlocal japanese_filter
                japanese_filter = not japanese_filter
                app.storage.user['japanese_only'] = japanese_filter

                if japanese_filter:
                    jp_header_btn.classes(remove=jp_inactive_cls)
                    jp_header_btn.classes(add=jp_active_cls)
                else:
                    jp_header_btn.classes(remove=jp_active_cls)
                    jp_header_btn.classes(add=jp_inactive_cls)

                new_matched, new_suggestions = await fetch_places(japanese_filter)
                render_places(build_display(new_matched, new_suggestions))
                await ui.run_javascript(f'updateMapMarkers({json.dumps(new_matched + new_suggestions)})')

            jp_header_btn.on('click', toggle_jp_filter)

        # ── Cột phải: Bản đồ ──────────────────────────────────────────────────
        with ui.column().classes('w-2/3 h-full p-4 flex-grow relative bg-white'):
            ui.add_head_html('''
                <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
                <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            ''')
            ui.html('<div id="route-info" style="padding:8px 12px;font-size:13px;color:#1565C0;'
                    'background:#E3F2FD;border-radius:8px;margin-bottom:6px;font-weight:600;">'
                    'Đang tải bản đồ...</div>')
            ui.html('<div id="search-map" style="height:calc(100vh - 150px);width:100%;'
                    'border-radius:12px;box-shadow:0 4px 6px -1px rgb(0 0 0 / 0.1);"></div>').classes('w-full')

            ui.add_body_html(f'''
            <script>
            function initSearchMap() {{
                var mapDiv = document.getElementById('search-map');
                if (!mapDiv) {{ setTimeout(initSearchMap, 100); return; }}

                var searchMap = L.map('search-map').setView([{lat}, {lng}], 14);
                window['search-map_instance'] = searchMap;

                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '© OpenStreetMap'
                }}).addTo(searchMap);

                window.userLat = {lat};
                window.userLng = {lng};
                window.currentDestLat = null;
                window.currentDestLng = null;

                window.userMarker = L.circleMarker([window.userLat, window.userLng], {{
                    radius: 8, color: '#4285F4', fillColor: '#4285F4', fillOpacity: 1, zIndexOffset: 1000
                }}).addTo(searchMap).bindPopup('Vị trí của bạn');

                window.markers = {{}};
                window.currentRouteLayer = null;
                window.places = {places_json};

                var CATEGORY_ICON = {{
                    'gym':        {{ emoji: '🏋️', bg: '#E3F2FD', border: '#1976D2' }},
                    'park':       {{ emoji: '🌳', bg: '#E8F5E9', border: '#388E3C' }},
                    'pool':       {{ emoji: '🏊', bg: '#E0F7FA', border: '#0097A7' }},
                    'badminton':  {{ emoji: '🏸', bg: '#FFF3E0', border: '#F57C00' }},
                    'tennis':     {{ emoji: '🎾', bg: '#F3E5F5', border: '#7B1FA2' }},
                    'pickleball': {{ emoji: '🏓', bg: '#FFF8E1', border: '#F9A825' }},
                    'hospital':   {{ emoji: '🏥', bg: '#FFEBEE', border: '#C62828' }},
                    'police':     {{ emoji: '👮', bg: '#E8EAF6', border: '#283593' }}
                }};

                function makePlaceIcon(category) {{
                    var cfg = CATEGORY_ICON[category] || {{ emoji: '📍', bg: '#F5F5F5', border: '#9E9E9E' }};
                    var html = '<div style="width:36px;height:36px;background:' + cfg.bg +
                               ';border:2.5px solid ' + cfg.border +
                               ';border-radius:50% 50% 50% 0;transform:rotate(-45deg);' +
                               'display:flex;align-items:center;justify-content:center;' +
                               'box-shadow:0 2px 6px rgba(0,0,0,0.25);">' +
                               '<span style="transform:rotate(45deg);font-size:18px;line-height:1;">' +
                               cfg.emoji + '</span></div>';
                    return L.divIcon({{
                        className: '',
                        html: html,
                        iconSize: [36, 36],
                        iconAnchor: [18, 36],
                        popupAnchor: [0, -36]
                    }});
                }}

                function addMarkers(places) {{
                    for (var k in window.markers) {{ searchMap.removeLayer(window.markers[k]); }}
                    window.markers = {{}};
                    window.places = places;
                    places.forEach(function(p) {{
                        var icon = makePlaceIcon(p.category);
                        window.markers[p.id] = L.marker([p.lat, p.lng], {{icon: icon}})
                            .addTo(searchMap)
                            .bindPopup(`<div style="font-family:sans-serif;min-width:140px">
                                <b>${{p.name}}</b><br>
                                <span style="color:#666;font-size:12px">${{p.name_ja || ''}}</span><br>
                                <span>📍 ${{(p.distance/1000).toFixed(1)}} km · ⭐ ${{p.rating}}</span><br>
                                <a href="/detail/${{p.id}}" style="color:#1976D2;font-weight:bold;font-size:12px">Xem chi tiết →</a>
                            </div>`);
                    }});
                }}
                addMarkers(window.places);

                window.updateMapMarkers = function(newPlaces) {{
                    addMarkers(newPlaces);
                    if (newPlaces.length > 0) window.drawRoute(newPlaces[0].lat, newPlaces[0].lng);
                }};

                window.drawRoute = async function(destLat, destLng) {{
                    window.currentDestLat = destLat;
                    window.currentDestLng = destLng;
                    if (!destLat || !destLng) return;
                    try {{
                        const url = `https://router.project-osrm.org/route/v1/driving/${{window.userLng}},${{window.userLat}};${{destLng}},${{destLat}}?overview=full&geometries=geojson`;
                        const res = await fetch(url);
                        const data = await res.json();
                        if (data.routes && data.routes[0]) {{
                            const route = data.routes[0];
                            if (window.currentRouteLayer) searchMap.removeLayer(window.currentRouteLayer);
                            window.currentRouteLayer = L.geoJSON(route.geometry, {{
                                style: {{ color: '#1976D2', weight: 4, opacity: 0.85 }}
                            }}).addTo(searchMap);
                            searchMap.fitBounds(window.currentRouteLayer.getBounds(), {{ padding: [40, 40] }});
                            const km = (route.distance / 1000).toFixed(1);
                            const min = Math.round(route.duration / 60);
                            document.getElementById('route-info').innerHTML = `🚗 ${{km}} km &nbsp;·&nbsp; ⏱ ${{min}} phút lái xe`;
                        }}
                    }} catch(e) {{
                        document.getElementById('route-info').innerHTML = 'Lỗi tính đường đi.';
                    }}
                }};

                if (window.places.length > 0) {{
                    window.drawRoute(window.places[0].lat, window.places[0].lng);
                }} else {{
                    document.getElementById('route-info').innerHTML = 'Không có địa điểm để vẽ đường.';
                }}

                window.highlightMarker = function(placeId) {{
                    if (window.markers[placeId]) {{
                        window.markers[placeId].openPopup();
                        let p = window.places.find(x => x.id === placeId);
                        if (p) window.drawRoute(p.lat, p.lng);
                    }}
                }};
            }}
            setTimeout(initSearchMap, 100);
            </script>
            ''')

    from components.sos_button import add_sos_button
    add_sos_button()
