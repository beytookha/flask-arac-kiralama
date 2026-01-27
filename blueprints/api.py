from flask import Blueprint, jsonify, request, session
import db_manager as db

api_bp = Blueprint('api', __name__, url_prefix='/api')

def admin_required_api():
    if not session.get('logged_in') or session.get('rol') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    return None

@api_bp.route('/calendar-events')
def calendar_events():
    """Takvim için JSON verisi döndürür."""
    auth_check = admin_required_api()
    if auth_check: return auth_check

    events = db.get_calendar_events()
    event_list = []
    
    for e in events:
        color = '#28a745'
        if e['durum'] == 'Kirada': color = '#007bff'
        elif e['durum'] == 'Bekliyor': color = '#ffc107'
        
        event_list.append({
            'title': f"{e['plaka']} - {e['ad']} {e['soyad']}",
            'start': str(e['baslangic_tarihi']),
            'end': str(e['bitis_tarihi']),
            'color': color,
            'url': f"/admin/teslim-al/{e['rezervasyon_id']}" if e['durum'] == 'Kirada' else '#'
        })
        
    return jsonify(event_list)

@api_bp.route('/run-sql', methods=['POST'])
def run_sql():
    """SQL Konsolu için uç nokta."""
    auth_check = admin_required_api()
    if auth_check: return auth_check

    query = request.form.get('query')
    if not query:
        return jsonify({'status': 'error', 'message': 'Sorgu boş olamaz.'})
        
    result = db.run_custom_sql(query)
    return jsonify(result)

@api_bp.route('/stats/dashboard')
def dashboard_stats():
    """Dashboard grafik verilerini JSON olarak döndürür."""
    auth_check = admin_required_api()
    if auth_check: return auth_check
    
    stats = db.get_dashboard_stats()
    return jsonify(stats)
