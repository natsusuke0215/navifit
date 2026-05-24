from nicegui import ui
import json

# 7 vùng an toàn cố định — phủ các khu vực có mật độ cảnh sát + bệnh viện cao tại Hà Nội.
# Vòng tròn màu xanh lá, nét đứt, kích cỡ theo mật độ.
SAFETY_ZONES = [
    {"name": "Hoàn Kiếm – Hai Bà Trưng", "lat": 21.0200, "lng": 105.8510, "radius": 1800},  # mật độ cao nhất
    {"name": "Ba Đình – Đống Đa",         "lat": 21.0250, "lng": 105.8360, "radius": 2000},  # nhiều BV lớn
    {"name": "Cầu Giấy",                 "lat": 21.0380, "lng": 105.8000, "radius": 1400},
    {"name": "Tây Hồ",                   "lat": 21.0530, "lng": 105.8280, "radius": 1100},
    {"name": "Thanh Xuân",               "lat": 20.9950, "lng": 105.8150, "radius": 1200},
    {"name": "Hoàng Mai",                "lat": 20.9880, "lng": 105.8620, "radius": 1200},
    {"name": "Long Biên",                "lat": 21.0330, "lng": 105.8920, "radius": 1000},
]


def add_safety_scripts():
    zones_json = json.dumps(SAFETY_ZONES)
    ui.add_head_html(f'''
    <script>
    if (typeof window.safetyZones === 'undefined') {{
        window.safetyZones = {zones_json};
        window.safetyLayersByMap = {{}};

        window.showSafetyOverlay = function(mapId) {{
            var mapObj = window[mapId + '_instance'];
            if (!mapObj) {{ console.warn("Map not found:", mapId); return; }}
            window.hideSafetyOverlay(mapId);
            window.safetyLayersByMap[mapId] = [];

            // 1. Vòng tròn xanh cố định
            window.safetyZones.forEach(function(zone) {{
                var circle = L.circle([zone.lat, zone.lng], {{
                    radius: zone.radius,
                    color: '#2E7D32',
                    fillColor: '#4CAF50',
                    fillOpacity: 0.12,
                    weight: 2.5,
                    dashArray: '10, 7',
                    interactive: false
                }}).addTo(mapObj);

                var label = L.tooltip({{
                    permanent: true,
                    direction: 'center',
                    className: 'safety-zone-tooltip',
                    opacity: 1
                }})
                .setLatLng([zone.lat, zone.lng])
                .setContent(
                    '<div style="background:#2E7D32;color:#fff;padding:3px 9px;' +
                    'border-radius:6px;font-weight:bold;font-size:11px;' +
                    'box-shadow:0 1px 3px rgba(0,0,0,0.4);white-space:nowrap;">' +
                    '🛡️ ' + zone.name + '</div>'
                )
                .addTo(mapObj);

                window.safetyLayersByMap[mapId].push(circle);
                window.safetyLayersByMap[mapId].push(label);
            }});

            // 2. Marker cảnh sát + bệnh viện
            var places = window.map_places || window.places || [];
            places.forEach(function(p) {{
                if (p.category !== 'police' && p.category !== 'hospital') return;

                var emoji = (p.category === 'police') ? '👮' : '🏥';
                var color = (p.category === 'police') ? '#1565C0' : '#C62828';
                var label = (p.category === 'police') ? '警察' : '病院';

                var iconHtml =
                    '<div style="font-size:26px;line-height:1;' +
                    'filter:drop-shadow(0 2px 4px rgba(0,0,0,0.4));' +
                    'text-align:center;">' + emoji + '</div>';

                var icon = L.divIcon({{
                    className: '',
                    html: iconHtml,
                    iconSize: [30, 30],
                    iconAnchor: [15, 15],
                    popupAnchor: [0, -15]
                }});

                var popup =
                    '<div style="font-family:sans-serif;min-width:170px">' +
                    '<div style="color:' + color + ';font-weight:700;font-size:13px">' +
                        emoji + ' ' + label + '</div>' +
                    '<div style="font-weight:600;color:#222;margin-top:2px">' + p.name + '</div>' +
                    (p.name_ja ? '<div style="color:#888;font-size:12px">' + p.name_ja + '</div>' : '') +
                    (p.address ? '<div style="font-size:12px;margin-top:3px">📍 ' + p.address + '</div>' : '') +
                    '</div>';

                var marker = L.marker([p.lat, p.lng], {{ icon: icon, zIndexOffset: 600 }})
                    .addTo(mapObj).bindPopup(popup);
                window.safetyLayersByMap[mapId].push(marker);
            }});
        }};

        window.hideSafetyOverlay = function(mapId) {{
            var mapObj = window[mapId + '_instance'];
            if (!mapObj) return;
            var layers = window.safetyLayersByMap[mapId];
            if (layers) {{
                layers.forEach(function(l) {{ mapObj.removeLayer(l); }});
                window.safetyLayersByMap[mapId] = [];
            }}
        }};
    }}
    </script>
    <style>
    .safety-zone-tooltip {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }}
    .safety-zone-tooltip:before {{ display: none !important; }}
    </style>
    ''')


def add_safety_button(map_id: str = 'map'):
    """Toggle An toàn: không chuyển trang, chỉ bật/tắt vòng xanh + marker cảnh sát/bệnh viện."""
    add_safety_scripts()

    active = {'value': False}

    async def toggle():
        if active['value']:
            await ui.run_javascript(f"hideSafetyOverlay('{map_id}')")
            active['value'] = False
            btn.props('outline')          # viền xanh, chữ xanh, nền trắng
        else:
            await ui.run_javascript(f"showSafetyOverlay('{map_id}')")
            active['value'] = True
            btn.props(remove='outline')   # nền xanh, chữ trắng

    btn = ui.button('安全', on_click=toggle)
    btn.props('outline rounded-full color=green').classes('px-4 text-sm font-bold')
    return btn
