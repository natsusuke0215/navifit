from nicegui import ui
import httpx
import asyncio

def add_aqi_scripts():
    ui.add_head_html('''
    <script>
    if (typeof window.aqiLayers === 'undefined') {
        window.aqiLayers = {};
        window.aqiBadges = {};

        window.showAQIOverlay = function(mapId, spotId, lat, lng, color, aqiVal, category, isUser) {
            var mapObj = window[mapId + '_instance'];
            if (!mapObj) {
                console.warn("Map instance not found for", mapId);
                return;
            }
            
            var layerId = mapId + '_' + spotId;
            if (window.aqiLayers[layerId]) {
                mapObj.removeLayer(window.aqiLayers[layerId]);
            }
            
            window.aqiLayers[layerId] = L.circle([lat, lng], {
                radius: 3000, 
                color: color, 
                fillColor: color, 
                fillOpacity: 0.07, 
                weight: 1,
                interactive: false
            }).addTo(mapObj);
            
            // Chỉ hiển thị Badge chính cho vị trí user
            if (isUser) {
                var badge = document.getElementById('aqi-badge-' + mapId);
                if (!badge) {
                    badge = document.createElement('div');
                    badge.id = 'aqi-badge-' + mapId;
                    badge.style = 'position:absolute;top:10px;left:50px;z-index:1000;padding:4px 10px;border-radius:20px;font-size:12px;font-weight:600;box-shadow:0 2px 6px rgba(0,0,0,0.3)';
                    var mapContainer = document.getElementById(mapId);
                    if (mapContainer && mapContainer.parentElement) {
                        mapContainer.parentElement.style.position = 'relative';
                        mapContainer.parentElement.appendChild(badge);
                    }
                }
                if (badge) {
                    badge.style.background = color;
                    badge.style.color = (aqiVal <= 100) ? '#000' : '#fff';
                    badge.textContent = `AQI Vị trí của bạn: ${aqiVal} — ${category}`;
                }
            } else {
                // Với các phòng tập, gán Tooltip tĩnh để thấy số AQI
                window.aqiLayers[layerId].bindTooltip(`AQI: ${aqiVal}`, {
                    permanent: true,
                    direction: 'bottom',
                    opacity: 0.9,
                    className: 'aqi-small-tooltip'
                }).openTooltip();
            }
        };

        window.hideAQIOverlay = function(mapId) {
            var mapObj = window[mapId + '_instance'];
            if (mapObj) {
                for (var key in window.aqiLayers) {
                    if (key.startsWith(mapId + '_')) {
                        mapObj.removeLayer(window.aqiLayers[key]);
                        delete window.aqiLayers[key];
                    }
                }
            }
            var badge = document.getElementById('aqi-badge-' + mapId);
            if (badge) badge.remove();
        };
    }
    </script>
    <style>
    .aqi-small-tooltip {
        background: rgba(255, 255, 255, 0.9);
        border: none;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        border-radius: 10px;
        padding: 2px 6px;
        font-weight: bold;
        font-size: 10px;
        color: #333;
    }
    </style>
    ''')

def add_aqi_button(map_id: str = 'map'):
    """Thêm nút AQI toggle vào header, khi bật thì vẽ overlay lên map có id=map_id"""
    add_aqi_scripts()
    
    aqi_active = {'value': False}
    
    async def toggle_aqi():
        if aqi_active['value']:
            # Tắt overlay
            await ui.run_javascript(f"hideAQIOverlay('{map_id}')")
            aqi_active['value'] = False
            aqi_btn.classes(remove='bg-blue-500 text-white', add='bg-gray-100')
            return
        
        # Bật overlay: Lấy tất cả các tọa độ cần vẽ
        try:
            coords_js = await ui.run_javascript('''
                var coords = [];
                // 1. Vị trí user
                var uLat = window.userLat || window.currentLat;
                var uLng = window.userLng || window.currentLng;
                if (uLat && uLng) {
                    coords.push({id: 'user', lat: uLat, lng: uLng, isUser: true});
                }
                
                // 2. Các điểm phòng tập (từ search.py hoặc home.py)
                var pList = window.places || window.map_places;
                if (pList && Array.isArray(pList)) {
                    pList.forEach(p => {
                        coords.push({id: p.id.toString(), lat: p.lat, lng: p.lng, isUser: false});
                    });
                }
                return coords;
            ''', timeout=5.0)
            
            if not coords_js:
                ui.notify('Không tìm thấy vị trí nào trên bản đồ', type='warning')
                return
                
            # Hàm gọi API song song cho 1 tọa độ
            async def fetch_aqi(client, c):
                try:
                    resp = await client.get(f'http://127.0.0.1:8081/api/aqi?lat={c["lat"]}&lng={c["lng"]}')
                    if resp.status_code == 200:
                        data = resp.json()
                        c['data'] = data
                        return c
                except Exception:
                    pass
                return None
                
            async with httpx.AsyncClient(timeout=15.0) as client:
                tasks = [fetch_aqi(client, c) for c in coords_js]
                results = await asyncio.gather(*tasks)
            
            success_count = 0
            for r in results:
                if r and 'data' in r:
                    d = r['data']
                    is_user = 'true' if r['isUser'] else 'false'
                    await ui.run_javascript(f"""
                        showAQIOverlay('{map_id}', '{r['id']}', {r['lat']}, {r['lng']},
                            '{d["color_code"]}', {d["aqi_value"]}, '{d["category"]}', {is_user});
                    """)
                    success_count += 1
            
            if success_count > 0:
                aqi_active['value'] = True
                aqi_btn.classes(remove='bg-gray-100', add='bg-blue-500 text-white')
            else:
                ui.notify('Không có dữ liệu AQI cho các khu vực này', type='warning')
                
        except Exception as e:
            print("Lỗi AQI Toggle:", e)
            ui.notify('Lỗi khi lấy dữ liệu AQI', type='negative')
    
    aqi_btn = ui.button('AQI', on_click=toggle_aqi)
    aqi_btn.classes('bg-gray-100 rounded-full px-3 py-1 text-sm font-medium')
    return aqi_btn
