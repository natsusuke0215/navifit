import httpx
from nicegui import ui
from datetime import datetime

@ui.page('/detail/{place_id}')
async def detail_page(place_id: int, ulat: float = 21.006847, ulng: float = 105.843058, gps: int = 0):
    ui.page_title('NaviFit — 詳細')

    # ── 1. Fetch data ──────────────────────────────────────────────────────────
    place = None
    best_times = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r1 = await client.get(f'http://127.0.0.1:8080/api/places/{place_id}/detail')
            r1.raise_for_status()
            place = r1.json()
            r2 = await client.get(f'http://127.0.0.1:8080/api/places/{place_id}/best-times?type=week')
            if r2.status_code == 200:
                best_times = r2.json()
    except httpx.HTTPStatusError as e:
        ui.notify(f'Lỗi server: {e.response.status_code}', type='negative')
    except httpx.RequestError:
        ui.notify('Không thể kết nối server. Kiểm tra kết nối mạng.', type='negative')
    except Exception as e:
        print(f"Error fetching detail for place {place_id}: {e}")

    if not place:
        with ui.column().classes('w-full items-center p-8'):
            ui.label('❌ Không tìm thấy địa điểm').classes('text-red-500 text-2xl font-bold')
            ui.button('← Quay lại', on_click=ui.navigate.back).classes('mt-4')
        return

    # ── Leaflet CSS/JS ─────────────────────────────────────────────────────────
    ui.page_title(f'NaviFit — {place.get("name", "詳細")}')
    ui.add_head_html('''
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    ''')

    place_lat = place.get('lat')
    place_lng = place.get('lng')
    place_name = place.get('name', '').replace("'", "\\'")

    # ── 2. Header ──────────────────────────────────────────────────────────────
    with ui.header().classes('items-center bg-white text-black shadow-md px-4 py-3 justify-between'):
        with ui.row().classes('items-center gap-2 flex-1 mr-4'):
            ui.html('<a href="/"><img src="/static/Logo.png" style="height:40px;width:auto;display:block;cursor:pointer;flex-shrink:0"></a>')
            ui.button(icon='arrow_back', on_click=ui.navigate.back).props('flat round dense')
            with ui.row().classes('items-center flex-1 bg-gray-100 rounded-full px-3 py-1 gap-1'):
                ui.icon('search').classes('text-xl').style('color:#111;font-weight:900')
                detail_search = ui.input(
                    placeholder='トレーニング場所を検索...'
                ).props('borderless dense').classes('flex-1 text-sm bg-transparent')
                detail_search.on('keydown.enter', lambda: ui.navigate.to(
                    f'/search?q={detail_search.value}&lat={ulat}&lng={ulng}'))
        if place.get('has_japanese_support'):
            ui.badge('日本語対応').classes('bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full')

    # ── 3. Body ────────────────────────────────────────────────────────────────
    with ui.column().classes('max-w-2xl mx-auto w-full p-4 gap-4 pb-10'):

        # ── Route info bar ─────────────────────────────────────────────────────
        ui.html('<div id="route-info" style="padding:8px 14px;font-size:13px;font-weight:600;color:#1565C0;background:#E3F2FD;border-radius:10px;">🗺️ ルートを計算中...</div>').classes('w-full')

        # ── Mini map ───────────────────────────────────────────────────────────
        ui.html('<div id="detail-map" style="height:260px;width:100%;border-radius:14px;box-shadow:0 4px 12px rgba(0,0,0,0.12);"></div>').classes('w-full')

        # ── Basic info card ────────────────────────────────────────────────────
        with ui.card().classes('w-full p-4 gap-2 rounded-2xl shadow-sm'):
            # Name & Japanese name
            ui.label(place.get('name', '')).classes('text-2xl font-bold text-gray-800')
            if place.get('name_ja'):
                ui.label(place.get('name_ja', '')).classes('text-gray-400 text-sm')

            ui.separator()

            # Address
            ui.label(f"📍 {place.get('address', '住所未登録')}").classes('text-gray-600 text-sm')

            # Rating stars
            rating = place.get('rating', 0)
            filled = round(rating)
            stars = '★' * filled + '☆' * (5 - filled)
            with ui.row().classes('items-center gap-2'):
                ui.label(stars).classes('text-yellow-400 text-lg')
                ui.label(f'{rating} / 5').classes('text-gray-600 text-sm font-medium')

            # Category badge
            cat_labels = {'gym': '🏋️ ジム', 'park': '🌳 公園', 'pool': '🏊 プール', 'badminton': '🏸 バドミントン'}
            cat_key = place.get('category', '')
            with ui.row().classes('gap-2 flex-wrap mt-1'):
                ui.badge(cat_labels.get(cat_key, cat_key.upper())).classes('bg-indigo-100 text-indigo-700 text-xs px-2 py-1 rounded-full')
                if place.get('is_indoor'):
                    ui.badge('🏠 屋内').classes('bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full')
                if place.get('has_japanese_support'):
                    ui.badge('🇯🇵 日本語対応').classes('bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full')

            # Opening hours
            hours = place.get('opening_hours') or {}
            if hours:
                ui.separator()
                day_map = {0:'月', 1:'火', 2:'水', 3:'木', 4:'金', 5:'土', 6:'日'}
                today_label = day_map.get(datetime.now().weekday(), '')
                ui.label('🕐 営業時間').classes('font-semibold text-sm text-gray-700')
                with ui.grid(columns=2).classes('w-full gap-x-4 gap-y-0'):
                    for day, time in hours.items():
                        is_today = (day == today_label)
                        cls = 'text-blue-600 font-bold text-sm' if is_today else 'text-gray-500 text-sm'
                        ui.label(day).classes(cls)
                        ui.label(time).classes(cls)

            # Phone
            if place.get('phone'):
                ui.separator()
                ui.link(f"📞 {place['phone']}", target=f"tel:{place['phone']}").classes('text-blue-500 font-medium text-sm')

        # ── Best-times chart ───────────────────────────────────────────────────
        with ui.card().classes('w-full p-4 rounded-2xl shadow-sm'):
            ui.label('⏰ おすすめの利用時間').classes('font-bold text-gray-800 mb-1')
            ui.label('棒グラフを押すと時間帯ごとの詳細を表示します').classes('text-xs text-gray-400 mb-3')

            chart_mode = {'mode': 'week'}

            week_scores  = [t.get('avg_score', 0) for t in best_times]
            week_colors  = ['#4CAF50' if s >= 70 else '#FFC107' if s >= 40 else '#F44336' for s in week_scores]
            week_labels  = [t.get('label', '') for t in best_times]

            back_btn = ui.button('← 週間グラフに戻る').classes('text-sm text-blue-500 mb-2 self-start')
            back_btn.set_visibility(False)

            chart = ui.echart({
                'xAxis': {'data': week_labels, 'axisLabel': {'fontSize': 11}},
                'yAxis': {'max': 100, 'axisLabel': {'formatter': '{value}%', 'fontSize': 10}},
                'series': [{
                    'type': 'bar', 'data': week_scores,
                    'itemStyle': {'color': {'type': 'data', 'default': '#4CAF50'}},
                    'emphasis': {'itemStyle': {'opacity': 0.75}}
                }],
                'tooltip': {'trigger': 'axis', 'formatter': '{b}: {c}%'},
                'grid': {'left': '3%', 'right': '4%', 'bottom': '3%', 'top': '10%', 'containLabel': True}
            }).classes('w-full h-48')

            # Color each bar individually
            chart.options['series'][0]['data'] = [
                {'value': week_scores[i], 'itemStyle': {'color': week_colors[i]}}
                for i in range(len(week_scores))
            ]
            chart.update()

            async def on_chart_click(e):
                if chart_mode['mode'] != 'week':
                    return
                day_index = e.args.get('dataIndex', 0)
                try:
                    async with httpx.AsyncClient(timeout=10.0) as cl:
                        r = await cl.get(f'http://127.0.0.1:8080/api/places/{place_id}/best-times?type=day&day_of_week={day_index}')
                        day_data = r.json()
                except Exception:
                    return

                hour_scores = [d.get('score', 0) for d in day_data]
                hour_colors = ['#4CAF50' if s >= 70 else '#FFC107' if s >= 40 else '#F44336' for s in hour_scores]
                hour_labels = [d.get('label', '') for d in day_data]

                chart.options['xAxis']['data'] = hour_labels
                chart.options['series'][0]['data'] = [
                    {'value': hour_scores[i], 'itemStyle': {'color': hour_colors[i]}}
                    for i in range(len(hour_scores))
                ]
                chart.update()
                back_btn.set_visibility(True)
                chart_mode['mode'] = 'day'

            def load_week_chart():
                chart.options['xAxis']['data'] = week_labels
                chart.options['series'][0]['data'] = [
                    {'value': week_scores[i], 'itemStyle': {'color': week_colors[i]}}
                    for i in range(len(week_scores))
                ]
                chart.update()
                back_btn.set_visibility(False)
                chart_mode['mode'] = 'week'

            back_btn.on_click(load_week_chart)
            chart.on('click', on_chart_click)

        # ── Reviews ────────────────────────────────────────────────────────────
        with ui.card().classes('w-full p-4 rounded-2xl shadow-sm'):
            ui.label('💬 ユーザーレビュー').classes('font-bold text-gray-800 mb-3')
            reviews_container = ui.column().classes('gap-3 w-full')
            page_state = {'page': 1, 'has_more': False}

            async def load_reviews(page: int = 1):
                try:
                    async with httpx.AsyncClient(timeout=10.0) as cl:
                        r = await cl.get(f'http://127.0.0.1:8080/api/places/{place_id}/reviews?page={page}&limit=10')
                        data = r.json()
                except Exception:
                    return {'reviews': [], 'total': 0, 'page': 1, 'total_pages': 1}

                with reviews_container:
                    revs = data.get('reviews', [])
                    if not revs and page == 1:
                        ui.label('まだレビューはありません。最初のレビューを書いてみましょう。').classes('text-gray-400 text-sm italic')
                    for rev in revs:
                        stars_str = '★' * rev['rating'] + '☆' * (5 - rev['rating'])
                        with ui.card().classes('w-full bg-gray-50 p-3 rounded-xl'):
                            with ui.row().classes('items-center gap-2 mb-1'):
                                ui.label(rev.get('user_name', '匿名')).classes('font-semibold text-sm')
                                ui.label(stars_str).classes('text-yellow-400 text-sm')
                            if rev.get('comment'):
                                ui.label(rev['comment']).classes('text-gray-600 text-sm leading-relaxed')
                return data

            first_data = await load_reviews(1)
            page_state['has_more'] = first_data.get('page', 1) < first_data.get('total_pages', 1)

            load_more_btn_container = ui.column().classes('w-full')
            if page_state['has_more']:
                with load_more_btn_container:
                    async def load_more():
                        page_state['page'] += 1
                        data = await load_reviews(page_state['page'])
                        if data.get('page', 1) >= data.get('total_pages', 1):
                            load_more_btn_container.clear()
                    ui.button('レビューをもっと見る', on_click=load_more).classes('w-full mt-2').props('outline color=primary')

        # ── Write review dialog ────────────────────────────────────────────────
        with ui.dialog() as review_dialog, ui.card().classes('w-80 p-5 gap-3 rounded-2xl'):
            ui.label('✏️ レビューを書く').classes('font-bold text-lg text-gray-800')
            name_input    = ui.input('お名前').classes('w-full')
            rating_radio  = ui.radio([1, 2, 3, 4, 5], value=5).props('inline')
            comment_input = ui.textarea('コメント', placeholder='体験を共有してください...').classes('w-full')

            async def submit_review():
                if not name_input.value.strip():
                    ui.notify('お名前を入力してください', type='warning')
                    return
                try:
                    async with httpx.AsyncClient(timeout=10.0) as cl:
                        await cl.post(f'http://127.0.0.1:8080/api/places/{place_id}/reviews', json={
                            'user_name': name_input.value.strip(),
                            'rating': rating_radio.value,
                            'comment': comment_input.value.strip()
                        })
                    review_dialog.close()
                    ui.notify('🎉 レビューありがとうございます！', type='positive')
                    # Reload reviews
                    reviews_container.clear()
                    await load_reviews(1)
                except Exception as e:
                    ui.notify('レビューの送信に失敗しました', type='negative')
                    print("Submit review error:", e)

            with ui.row().classes('w-full gap-2 mt-2'):
                ui.button('キャンセル', on_click=review_dialog.close).props('flat').classes('flex-1')
                ui.button('送信', on_click=submit_review).classes('flex-1 bg-blue-500 text-white')

        ui.button('✏️ レビューを書く', on_click=review_dialog.open).classes('w-full').props('color=primary')

        # ── Similar places section ───────────────────────────────────────
        cat_key = place.get('category', '')
        cat_labels = {'gym': '🏋️ ジム', 'park': '🌳 公園', 'pool': '🏊 プール', 'badminton': '🏸 バドミントン'}
        similar_places = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as cl:
                r_similar = await cl.get(
                    f'http://127.0.0.1:8080/api/places/nearby?lat={ulat}&lng={ulng}&radius=20000'
                )
                if r_similar.status_code == 200:
                    all_nearby = r_similar.json()
                    similar_places = [
                        p for p in all_nearby
                        if not p.get('is_separator')
                        and p.get('category') == cat_key
                        and p.get('id') != place_id
                    ][:5]
        except Exception as e:
            print('Similar places error:', e)

        if similar_places:
            with ui.card().classes('w-full p-4 rounded-2xl shadow-sm'):
                ui.label(f'📍 近くの{cat_labels.get(cat_key, "同じカテゴリの場所")}').classes('font-bold text-gray-800 mb-3')
                for sp in similar_places:
                    dist_km = round(sp.get('distance', 0) / 1000, 1)
                    has_jp  = sp.get('has_japanese_support', False)
                    with ui.card().classes('w-full p-3 cursor-pointer hover:bg-blue-50 hover:shadow transition-all rounded-xl') \
                            .on('click', lambda pid=sp['id']: ui.navigate.to(f"/detail/{pid}?ulat={ulat}&ulng={ulng}")):
                        with ui.row().classes('items-center justify-between gap-2 w-full'):
                            with ui.column().classes('flex-1 gap-0'):
                                ui.label(sp.get('name', '')).classes('font-semibold text-sm text-gray-800')
                                if sp.get('name_ja'):
                                    ui.label(sp['name_ja']).classes('text-gray-400 text-xs')
                                with ui.row().classes('gap-3 mt-1'):
                                    ui.label(f'📍 {dist_km} km').classes('text-xs text-gray-500')
                                    ui.label(f'⭐ {sp.get("rating", "N/A")}').classes('text-xs text-yellow-600 font-bold')
                            with ui.column().classes('items-end gap-1 flex-shrink-0'):
                                if has_jp:
                                    ui.badge('🇯🇵 日本語').classes('bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full')
                                ui.label('詳細 →').classes('text-blue-500 text-xs font-medium')

    # ── Map JS (inject after body renders) ───────────────────────────────────
    ui.add_body_html(f'''
    <script>
    function initDetailMap() {{
        var mapDiv = document.getElementById('detail-map');
        if (!mapDiv || typeof L === 'undefined') {{
            setTimeout(initDetailMap, 100);
            return;
        }}
        if (mapDiv._leaflet_id) return;

        var detailMap = L.map('detail-map');
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap'
        }}).addTo(detailMap);

        var destIcon = L.divIcon({{
            html: '<div style="background:#E53935;width:14px;height:14px;border-radius:50%;border:2px solid white;box-shadow:0 2px 4px rgba(0,0,0,.4)"></div>',
            iconSize:[14,14], iconAnchor:[7,7], className:''
        }});
        L.marker([{place_lat},{place_lng}], {{icon:destIcon}})
            .addTo(detailMap).bindPopup('{place_name}');

        var uLat = {ulat};
        var uLng = {ulng};
        var currentRouteLayer = null;
        var routeRequestId = 0;

        function distanceMeters(lat1, lng1, lat2, lng2) {{
            const R = 6371000;
            const toRad = d => d * Math.PI / 180;
            const dLat = toRad(lat2 - lat1);
            const dLng = toRad(lng2 - lng1);
            const a = Math.sin(dLat / 2) ** 2 +
                Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
                Math.sin(dLng / 2) ** 2;
            return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        }}

        var userIcon = L.divIcon({{
            html: '<div style="background:#4285F4;width:12px;height:12px;border-radius:50%;border:2px solid white;box-shadow:0 2px 4px rgba(0,0,0,.4)"></div>',
            iconSize:[12,12], iconAnchor:[6,6], className:''
        }});
        var userMarker = L.marker([uLat, uLng], {{icon:userIcon}})
            .addTo(detailMap).bindPopup('現在地');

        function drawRouteFrom(userLat, userLng) {{
            var requestId = ++routeRequestId;
            var fromLat = Number(userLat);
            var fromLng = Number(userLng);
            var toLat = Number({place_lat});
            var toLng = Number({place_lng});
            if (![fromLat, fromLng, toLat, toLng].every(Number.isFinite)) return;
            var osrmUrl = 'https://router.project-osrm.org/route/v1/driving/'
                + fromLng + ',' + fromLat + ';'
                + toLng + ',' + toLat
                + '?overview=full&geometries=geojson&steps=false&alternatives=false';

            fetch(osrmUrl).then(r => r.json()).then(data => {{
                if (requestId !== routeRequestId) return;
                if (data.routes && data.routes[0]) {{
                    var route  = data.routes[0];
                    var dist   = (route.distance / 1000).toFixed(1);
                    var dur    = Math.round(route.duration / 60);

                    if (currentRouteLayer) detailMap.removeLayer(currentRouteLayer);
                    currentRouteLayer = L.geoJSON(route.geometry, {{
                        style: {{color:'#1976D2', weight:4, opacity:0.85}}
                    }}).addTo(detailMap);

                    detailMap.fitBounds(currentRouteLayer.getBounds(), {{padding:[25,25]}});

                    var el = document.getElementById('route-info');
                    if (el) el.innerHTML = '🚗 ' + dist + ' km &nbsp;·&nbsp; ⏱ 車で約' + dur + '分';
                }} else {{
                    var el = document.getElementById('route-info');
                    if (el) el.innerHTML = '⚠️ ルートを計算できませんでした。';
                }}
            }}).catch(() => {{
                if (requestId !== routeRequestId) return;
                detailMap.setView([{place_lat},{place_lng}], 15);
                var el = document.getElementById('route-info');
                if (el) el.innerHTML = '⚠️ ルートを計算できませんでした。';
            }});
        }}

        drawRouteFrom(uLat, uLng);

        if (navigator.geolocation) {{
            navigator.geolocation.getCurrentPosition(
                function(pos) {{
                    uLat = pos.coords.latitude;
                    uLng = pos.coords.longitude;
                    userMarker.setLatLng([uLat, uLng]);
                    var params = new URLSearchParams(window.location.search);
                    var alreadyGps = params.get('gps') === '1';
                    var urlLat = Number(params.get('ulat') || {ulat});
                    var urlLng = Number(params.get('ulng') || {ulng});
                    if (!alreadyGps && distanceMeters(urlLat, urlLng, uLat, uLng) > 50) {{
                        params.set('ulat', uLat.toFixed(6));
                        params.set('ulng', uLng.toFixed(6));
                        params.set('gps', '1');
                        window.location.replace(window.location.pathname + '?' + params.toString());
                        return;
                    }}
                    drawRouteFrom(uLat, uLng);
                }},
                function(err) {{
                    console.warn('Could not get current location:', err);
                }},
                {{ enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }}
            );
        }}
    }}
    setTimeout(initDetailMap, 100);
    </script>
    ''')
