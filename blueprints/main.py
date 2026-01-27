from flask import Blueprint, render_template, request, session, jsonify
import db_manager as db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Filtre Parametrelerini Al
    sehir_id = request.args.get('sehir_id')
    baslangic = request.args.get('baslangic')
    bitis = request.args.get('bitis')
    vites = request.args.get('vites')
    yakit = request.args.get('yakit')
    
    try:
        min_fiyat = int(request.args.get('min_fiyat', 0))
    except ValueError:
        min_fiyat = 0

    try:
        max_fiyat = int(request.args.get('max_fiyat', 100000))
    except ValueError:
        max_fiyat = 100000
    
    sehirler = db.get_sehirler()
    
    # DB'den filtreli araçları çek
    araclar = db.get_tum_araclar(
        sehir_id=sehir_id, 
        baslangic=baslangic, 
        bitis=bitis,
        vites=vites,
        yakit=yakit,
        min_fiyat=min_fiyat,
        max_fiyat=max_fiyat
    )
    
    # Yorumlar
    yorumlar = db.get_onayli_yorumlar()
    
    # Favoriler
    fav_ids = []
    if 'user_id' in session:
        fav_ids = db.get_user_favori_ids(session['user_id'])
    
    return render_template('main/index.html', araclar=araclar, sehirler=sehirler, 
                           secilen_sehir_id=sehir_id, yorumlar=yorumlar, 
                           fav_ids=fav_ids)

# --- FAVORİ EKLE/ÇIKAR (AJAX) ---
@main_bp.route('/toggle-favori/<int:arac_id>', methods=['POST'])
def toggle_favori_api(arac_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Giriş yapmalısınız'}), 401
    
    # Müşteri değilse engelle (Opsiyonel)
    if session.get('role') != 'musteri':
        return jsonify({'status': 'error', 'message': 'Sadece müşteriler favorileyebilir'}), 403

    sonuc = db.toggle_favori(session['user_id'], arac_id)
    return jsonify(sonuc)

# --- KUPON KONTROL (AJAX) ---
@main_bp.route('/check-coupon', methods=['POST'])
def check_coupon():
    data = request.get_json()
    kod = data.get('kod')
    
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'mesaj': 'Giriş yapmalısınız!'})

    kampanya = db.get_kampanya_by_code(kod)
    if not kampanya:
        return jsonify({'status': 'error', 'mesaj': 'Geçersiz kod!'})

    if db.check_user_coupon_usage(session['user_id'], kod):
        return jsonify({'status': 'error', 'mesaj': 'Bu kuponu zaten kullandınız!'})
    
    return jsonify({
        'status': 'success',
        'oran': kampanya['indirim_orani'],
        'mesaj': f"Tebrikler! %{kampanya['indirim_orani']} indirim uygulandı."
    })
