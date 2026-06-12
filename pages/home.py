import httpx
from nicegui import ui

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
    1: ('安全',      '#4CAF50', 'white'),
    2: ('まあ安全',   '#FFC107', '#333'),
    3: ('かなり安全', '#FF9800', 'white'),
    4: ('危険',      '#F44336', 'white'),
}

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

def _aqi_badge(v: int) -> tuple:
    if v <= 50:    return 'AQI いい', '#4CAF50', 'white'
    elif v <= 100: return 'AQI 普通', '#FFC107', '#333'
    elif v <= 150: return 'AQI 悪い', '#FF9800', 'white'
    else:          return 'AQI 最悪', '#F44336', 'white'

@ui.page('/')
async def home_page():
    ui.page_title('NaviFit — Trang chủ')
    # 1. Header cố định
    with ui.header().classes('items-center justify-between bg-white text-black shadow-md px-6 py-3'):
        ui.html('<a href="/"><img src="/static/Logo.png" style="height:48px;width:auto;display:block;cursor:pointer"></a>')

        async def handle_search(e):
            q = search_input.value
            if not q:
                return
            lat = await ui.run_javascript('window.currentLat || null')
            lng = await ui.run_javascript('window.currentLng || null')
            if lat and lng:
                ui.navigate.to(f'/search?q={q}&lat={lat}&lng={lng}')
            else:
                ui.navigate.to(f'/search?q={q}')

        import asyncio
        with ui.column().classes('relative w-2/5 gap-0'):
            search_state = {'task': None}

            async def perform_search(q):
                if not q:
                    suggestions_box.set_visibility(False)
                    return
                lat, lng = 21.006847, 105.843058
                try:
                    lat_js = await ui.run_javascript('window.currentLat || null', timeout=0.5)
                    lng_js = await ui.run_javascript('window.currentLng || null', timeout=0.5)
                    if lat_js and lng_js:
                        lat, lng = float(lat_js), float(lng_js)
                except Exception:
                    pass

                # AQI cho khu vực (fetch 1 lần)
                aqi_label, aqi_color, aqi_tc = 'AQI いい', '#4CAF50', 'white'
                try:
                    async with httpx.AsyncClient(timeout=3.0) as client:
                        r = await client.get(f'http://127.0.0.1:8080/api/aqi?lat={lat}&lng={lng}')
                        if r.status_code == 200:
                            aqi_label, aqi_color, aqi_tc = _aqi_badge(r.json().get('aqi_value', 0))
                except Exception:
                    pass

                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        res = await client.get(
                            f'http://127.0.0.1:8080/api/places/nearby'
                            f'?lat={lat}&lng={lng}&radius=20000')
                        res.raise_for_status()
                        all_places = res.json()

                    q_lower = q.lower().strip()
                    target_cat = CAT_KEYWORDS.get(q_lower)
                    matched = [
                        p for p in all_places
                        if not p.get('is_separator') and (
                            (target_cat and p.get('category') == target_cat)
                            or q_lower in p.get('name', '').lower()
                            or q_lower in (p.get('name_ja') or '').lower()
                            or q_lower in p.get('address', '').lower()
                        )
                    ]

                    suggestions_list.clear()
                    if matched:
                        suggestions_box.set_visibility(True)
                        with suggestions_list:
                            for place in matched:
                                has_jp  = place.get('has_japanese_support', False)
                                s_level = place.get('safety_level', 2)
                                s_lbl, s_bg, s_tc = SAFETY_CONFIG.get(s_level, SAFETY_CONFIG[2])
                                dist_m  = place.get('distance', 0)
                                dist_str = f'{dist_m}m' if dist_m < 1000 else f'{dist_m/1000:.1f}km'
                                p_name  = place.get('name', '')
                                p_id    = place['id']

                                with ui.card().classes(
                                    'w-full p-2 cursor-pointer hover:bg-blue-50 '
                                    'hover:shadow-md transition-all rounded-xl'
                                ) as card:
                                    card.on('click', lambda n=p_name: (
                                        suggestions_box.set_visibility(False),
                                        ui.navigate.to(f'/search?q={n}&lat={lat}&lng={lng}')
                                    ))
                                    with ui.row().classes('items-center gap-1 w-full flex-nowrap'):
                                        with ui.column().classes('gap-1 flex-shrink-0 items-center'):
                                            ui.html(
                                                f'<span style="display:block;background:{s_bg};'
                                                f'color:{s_tc};padding:2px 5px;border-radius:5px;'
                                                f'font-size:9px;font-weight:bold;white-space:nowrap">'
                                                f'{s_lbl}</span>'
                                            )
                                            ui.html(
                                                f'<span style="display:block;background:{aqi_color};'
                                                f'color:{aqi_tc};padding:2px 5px;border-radius:5px;'
                                                f'font-size:9px;font-weight:bold;white-space:nowrap">'
                                                f'{aqi_label}</span>'
                                            )
                                        if has_jp:
                                            ui.html(
                                                f'<div style="flex-shrink:0;width:22px;height:28px;'
                                                f'display:flex;align-items:center;justify-content:center">'
                                                f'{JP_WOMAN_SVG}</div>'
                                            )
                                        else:
                                            ui.html('<div style="flex-shrink:0;width:22px"></div>')
                                        ui.html(
                                            f'<span style="color:#555;font-size:10px;'
                                            f'flex-shrink:0;white-space:nowrap">📍{dist_str}</span>'
                                        )
                                        with ui.column().classes('flex-1 min-w-0 gap-0'):
                                            ui.label(p_name).classes(
                                                'font-semibold text-gray-800 text-xs leading-tight'
                                            ).style('overflow:hidden;text-overflow:ellipsis;white-space:nowrap')
                                            if place.get('address'):
                                                ui.label(place['address']).classes(
                                                    'text-gray-400 text-xs'
                                                ).style('overflow:hidden;text-overflow:ellipsis;white-space:nowrap')
                    else:
                        suggestions_box.set_visibility(False)
                except Exception as e:
                    print("Error autocomplete:", e)
                    suggestions_box.set_visibility(False)

            async def on_input(e):
                if search_state['task']:
                    search_state['task'].cancel()
                q = e.value
                async def debounced():
                    try:
                        await asyncio.sleep(0.3)
                        await perform_search(q)
                    except asyncio.CancelledError:
                        pass
                search_state['task'] = asyncio.create_task(debounced())

            with ui.row().classes('items-center w-full bg-white rounded-full px-3 py-1 gap-1').style(
                'border:1.5px solid #d1d5db;box-shadow:0 1px 4px rgba(0,0,0,0.06)'
            ):
                ui.icon('search').classes('text-xl flex-shrink-0').style('color:#111;font-weight:900')
                search_input = ui.input(
                    placeholder='トレーニング場所を検索...',
                    on_change=on_input
                ).classes('flex-1').props('borderless dense clearable')
            search_input.on('keydown.enter', handle_search)

            with ui.card().classes('absolute top-full left-0 w-full z-[9999] p-2 mt-1 shadow-xl bg-white').style(
                'max-height:420px;overflow-y:auto;border-radius:12px'
            ) as suggestions_box:
                suggestions_list = ui.column().classes('w-full gap-1')
            suggestions_box.set_visibility(False)

        with ui.row().classes('gap-3'):
            from components.aqi_button import add_aqi_button
            from components.safety_button import add_safety_button
            add_aqi_button('map')
            add_safety_button('map')

    # Nhúng Leaflet CSS & JS
    ui.add_head_html('''
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    ''')

    # 2. Bản đồ bằng thẻ div
    ui.html('<div id="map" style="height:80vh;width:100%;z-index:0;border-radius:12px;box-shadow:0 4px 6px -1px rgb(0 0 0 / 0.1);"></div>').classes('w-full px-4 mt-4')

    # 3. Khởi tạo map bằng script
    ui.add_body_html('''
    <script>
    var map = null;

    function initLeaflet() {
        var mapDiv = document.getElementById('map');
        if (!mapDiv) {
            setTimeout(initLeaflet, 100);
            return;
        }

        // Khởi tạo bản đồ với tọa độ trung tâm Hà Nội
        map = L.map('map').setView([21.006847, 105.843058], 15);
        window.map_instance = map;

        // Tile layer OpenStreetMap
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(map);

        // Icon theo category (dùng string concat, không dùng template literal)
        var CATEGORY_ICON = {
            'gym':        { emoji: '🏋️', bg: '#E3F2FD', border: '#1976D2' },
            'park':       { emoji: '🌳', bg: '#E8F5E9', border: '#388E3C' },
            'pool':       { emoji: '🏊', bg: '#E0F7FA', border: '#0097A7' },
            'badminton':  { emoji: '🏸', bg: '#FFF3E0', border: '#F57C00' },
            'tennis':     { emoji: '🎾', bg: '#F3E5F5', border: '#7B1FA2' },
            'pickleball': { emoji: '🏓', bg: '#FFF8E1', border: '#F9A825' },
            'hospital':   { emoji: '🏥', bg: '#FFEBEE', border: '#C62828' },
            'police':     { emoji: '👮', bg: '#E8EAF6', border: '#283593' }
        };

        function makePlaceIcon(category) {
            var cfg = CATEGORY_ICON[category] || { emoji: '📍', bg: '#F5F5F5', border: '#9E9E9E' };
            var html = '<div style="width:36px;height:36px;background:' + cfg.bg +
                       ';border:2.5px solid ' + cfg.border +
                       ';border-radius:50% 50% 50% 0;transform:rotate(-45deg);' +
                       'display:flex;align-items:center;justify-content:center;' +
                       'box-shadow:0 2px 6px rgba(0,0,0,0.25);">' +
                       '<span style="transform:rotate(45deg);font-size:18px;line-height:1;">' +
                       cfg.emoji + '</span></div>';
            return L.divIcon({
                className: '',
                html: html,
                iconSize: [36, 36],
                iconAnchor: [18, 36],
                popupAnchor: [0, -36]
            });
        }

        window.mapPlaceMarkers = [];

        // Hàm load địa điểm gần đây từ API
        async function fetchNearbyPlaces(lat, lng) {
            try {
                window.mapPlaceMarkers.forEach(function(marker) {
                    map.removeLayer(marker);
                });
                window.mapPlaceMarkers = [];
                var res = await fetch('/api/places/nearby?lat=' + lat + '&lng=' + lng + '&radius=20000');
                var places = await res.json();
                window.map_places = places;
                places.forEach(function(place) {
                    // Ẩn cảnh sát/bệnh viện mặc định — chỉ hiện khi bật nút An toàn (vùng vuông nét đứt)
                    if (place.category === 'police' || place.category === 'hospital') return;
                    var icon = makePlaceIcon(place.category);
                    var japanBadge = place.has_japanese_support
                        ? '<span style="background:#E3F2FD;color:#1565C0;border:1px solid #90CAF9;border-radius:4px;padding:2px 6px;font-size:11px;font-weight:bold;">🇯🇵 日本語対応</span>'
                        : '';
                    var popup =
                        '<div style="font-family:sans-serif;min-width:190px;">' +
                        '<h3 style="margin:0 0 3px 0;color:#1a73e8;font-size:15px;font-weight:700;">' + place.name + '</h3>' +
                        (place.name_ja ? '<p style="margin:0 0 6px 0;color:#666;font-size:12px;">' + place.name_ja + '</p>' : '') +
                        '<div style="display:flex;gap:8px;margin-bottom:6px;font-size:13px;">' +
                        '<span>📍 <strong>' + (place.distance / 1000).toFixed(1) + ' km</strong></span>' +
                        '<span>⭐ <strong>' + place.rating + '</strong></span>' +
                        '</div>' +
                        (japanBadge ? '<div style="margin-bottom:8px;">' + japanBadge + '</div>' : '') +
                        '<a href="/detail/' + place.id + '?ulat=' + lat + '&ulng=' + lng + '" ' +
                        'style="display:inline-block;background:#1a73e8;color:#fff;text-decoration:none;' +
                        'font-weight:600;font-size:12px;padding:5px 12px;border-radius:6px;">詳細を見る →</a>' +
                        '</div>';
                    window.mapPlaceMarkers.push(L.marker([place.lat, place.lng], { icon: icon })
                        .addTo(map)
                        .bindPopup(popup));
                });
            } catch(e) {
                console.error('Loi load dia diem:', e);
            }
        }

        // Dùng tọa độ Hà Nội làm mặc định, sau đó cập nhật bằng GPS nếu trình duyệt cho phép.
        var defaultLat = 21.006847;
        var defaultLng = 105.843058;
        window.currentLat = defaultLat;
        window.currentLng = defaultLng;

        // Marker chấm xanh vị trí hiện tại
        var userIcon = L.divIcon({
            className: '',
            html: '<div style="width:18px;height:18px;background:#4285F4;border:3px solid white;border-radius:50%;box-shadow:0 2px 8px rgba(66,133,244,0.6);"></div>',
            iconSize: [18, 18],
            iconAnchor: [9, 9]
        });
        var userMarker = L.marker([defaultLat, defaultLng], {icon: userIcon})
            .addTo(map)
            .bindPopup('<b>現在地</b><br><small>B1棟 - ハノイ工科大学</small>')
            .openPopup();

        fetchNearbyPlaces(defaultLat, defaultLng);

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(pos) {
                    window.currentLat = pos.coords.latitude;
                    window.currentLng = pos.coords.longitude;
                    userMarker.setLatLng([window.currentLat, window.currentLng]);
                    userMarker.bindPopup('<b>現在地</b>');
                    map.setView([window.currentLat, window.currentLng], 15);
                    fetchNearbyPlaces(window.currentLat, window.currentLng);
                },
                function(err) {
                    console.warn('Could not get current location:', err);
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
            );
        }
    }

    setTimeout(initLeaflet, 100);
    </script>
    ''')

    from components.sos_button import add_sos_button
    add_sos_button()
