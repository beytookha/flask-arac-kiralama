import os  
import pandas as pd
import io
from datetime import datetime
from flask import Flask, make_response, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from werkzeug.utils import secure_filename 
from werkzeug.security import generate_password_hash
from fpdf import FPDF 
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from config import Config
from extensions import mail

# SQL kodları yerine db_manager'ı çağırıyoruz
import db_manager as db

app = Flask(__name__)
app.config.from_object(Config)

# Eklentileri başlat
mail.init_app(app)
serializer = URLSafeTimedSerializer(app.secret_key)

# Blueprint Kayıt
from blueprints.auth import auth_bp
app.register_blueprint(auth_bp)

# --- YARDIMCI: MAIL GÖNDERME ---
# (Bu fonksiyon artık auth.py içinde, ancak app.py'de de kullanılıyor olabilir. 
# Eğer app.py'de hala mail atan yerler varsa kalmalı veya shared bir yere taşınmalı.
# Şimdilik burada kalsın ama send_eamil auth.py'de de var. Kod tekrarı oldu ama Refactor sonra yapacağız.)
def send_email(to, subject, template):
    try:
        msg = Message(subject, recipients=[to], html=template)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Mail Hatası: {e}")
        return False

# --- DOSYA YÜKLEME AYARLARI ---
UPLOAD_FOLDER = 'static/img'
PROFILE_UPLOAD_FOLDER = 'static/img/profiles'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROFILE_UPLOAD_FOLDER'] = PROFILE_UPLOAD_FOLDER

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROFILE_UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==========================================
#               SAYFA ROTALARI
# ==========================================

# --- ANA SAYFA (FİLTRELEME HATASI DÜZELTİLDİ) ---
@app.route('/')
def index():
    # Filtre Parametrelerini Al
    sehir_id = request.args.get('sehir_id')
    baslangic = request.args.get('baslangic')
    bitis = request.args.get('bitis')
    vites = request.args.get('vites')
    yakit = request.args.get('yakit')
    
    # [DÜZELTME] Fiyatlar boş gelirse hata vermesin diye varsayılan değer ata
    try:
        min_fiyat = request.args.get('min_fiyat')
        min_fiyat = int(min_fiyat) if min_fiyat else 0
    except ValueError:
        min_fiyat = 0

    try:
        max_fiyat = request.args.get('max_fiyat')
        max_fiyat = int(max_fiyat) if max_fiyat else 100000
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
    
    yorumlar = db.get_onayli_yorumlar()
    
    fav_ids = []
    if 'user_id' in session:
        fav_ids = db.get_user_favori_ids(session['user_id'])
    
    return render_template('index.html', araclar=araclar, sehirler=sehirler, 
                           secilen_sehir_id=sehir_id, yorumlar=yorumlar, 
                           fav_ids=fav_ids)

# --- ŞİFRE VE GİRİŞ İŞLEMLERİ (Moved to blueprints/auth.py) ---
# Routes: /forgot-password, /reset-password, /login, /register, /logout, /admin/login 
# Artık Auth Blueprint tarafından yönetiliyor.

# --- REZERVASYON ÖZETİ ---
@app.route('/rezervasyon/<int:arac_id>', methods=['GET', 'POST'])
def rezervasyon(arac_id):
    if 'user_id' not in session:
        flash('Rezervasyon yapmak için önce giriş yapmalısınız.', 'danger')
        return redirect(url_for('login', next=request.url))

    arac = db.get_arac_by_id(arac_id)
    ekstra_hizmetler = db.get_ekstra_hizmetler() 

    url_baslangic = request.args.get('baslangic')
    url_bitis = request.args.get('bitis')

    if request.method == 'POST':
        baslangic = request.form['baslangic_tarihi']
        bitis = request.form['bitis_tarihi']
        
        d1 = datetime.strptime(baslangic, "%Y-%m-%d")
        d2 = datetime.strptime(bitis, "%Y-%m-%d")
        gun_sayisi = (d2 - d1).days

        if gun_sayisi <= 0:
            flash('Bitiş tarihi başlangıç tarihinden sonra olmalıdır!', 'danger')
        else:
            arac_ucret = gun_sayisi * float(arac['gunluk_ucret'])
            secilen_ekstralar_ids = request.form.getlist('ekstra')
            ekstra_toplam = 0
            
            secilen_ekstralar_ids = [int(x) for x in secilen_ekstralar_ids]

            for e in ekstra_hizmetler:
                if e['ekstra_id'] in secilen_ekstralar_ids:
                    ekstra_toplam += float(e['gunluk_ucret']) * gun_sayisi
            
            toplam_ucret = arac_ucret + ekstra_toplam

            session['rezervasyon_bilgi'] = {
                'musteri_id': session['user_id'],
                'arac_id': arac_id,
                'baslangic_tarihi': baslangic,
                'bitis_tarihi': bitis,
                'alis_saati': request.form['alis_saati'],
                'teslim_saati': request.form['teslim_saati'],
                'gun_sayisi': gun_sayisi,
                'toplam_ucret': toplam_ucret,
                'ekstralar': secilen_ekstralar_ids
            }
            return redirect(url_for('odeme_yap'))

    return render_template('rezervasyon.html', arac=arac, ekstralar=ekstra_hizmetler,
                           url_baslangic=url_baslangic, url_bitis=url_bitis)

# --- ÖDEME ---
@app.route('/odeme', methods=['GET', 'POST'])
def odeme_yap():
    if 'rezervasyon_bilgi' not in session:
        return redirect(url_for('index'))

    arac = db.get_arac_by_id(session['rezervasyon_bilgi']['arac_id'])

    if request.method == 'POST':
        kullanilan_kod = request.form.get('uygulanan_kod')
        final_tutar_str = request.form.get('final_tutar')
        
        try:
            final_tutar = float(final_tutar_str)
        except (ValueError, TypeError):
            final_tutar = float(session['rezervasyon_bilgi']['toplam_ucret'])
        
        session['rezervasyon_bilgi']['toplam_ucret'] = final_tutar
        session['rezervasyon_bilgi']['indirim_kodu'] = kullanilan_kod

        odeme_bilgisi = {
            'sahip': request.form['kart_sahibi'],
            'no': request.form['kart_no'],
            'tur': request.form['odeme_turu']
        }
        
        if db.add_rezervasyon(session['rezervasyon_bilgi'], odeme_bilgisi):
            # Müşteriye Onay Maili Gönder
            musteri = db.get_musteri_by_id(session['user_id'])
            try:
                html_body = render_template('email_confirmation.html', 
                                            musteri=musteri, 
                                            arac=arac, 
                                            rez=session['rezervasyon_bilgi'])
                send_email(musteri['eposta'], "Rezervasyon Onayı - Rent A Car", html_body)
            except:
                pass 

            session.pop('rezervasyon_bilgi', None)
            flash(f'✅ Ödeme Başarılı! Rezervasyonunuz oluşturuldu.', 'success')
            return redirect(url_for('kiralamalarim'))
        else:
            flash('Bir hata oluştu.', 'danger')

    return render_template('odeme.html', arac=arac)

# --- MÜŞTERİ KİRALAMALARI ---
@app.route('/kiralamalarim')
def kiralamalarim():
    if 'user_id' not in session: return redirect(url_for('login'))
    kiralamalar = db.get_musteri_rezervasyonlari(session['user_id'])
    return render_template('kiralamalarim.html', kiralamalar=kiralamalar)

# --- YORUM YAPMA  ---
@app.route('/yorum-yap', methods=['POST'])
def yorum_yap():
    if 'user_id' not in session or session.get('role') != 'musteri':
        flash("Yorum yapmak için müşteri girişi yapmalısınız.", "warning")
        return redirect(url_for('login'))
    
    metin = request.form.get('yorum_metni')
    puan = request.form.get('puan')
    
    if db.add_yorum(session['user_id'], metin, puan):
        flash("Yorumunuz alındı! Yönetici onayından sonra yayınlanacaktır.", "success")
    else:
        flash("Bir hata oluştu.", "danger")
        
    return redirect(url_for('index'))

# --- PROFIL SAYFASI ---
@app.route('/profil', methods=['GET', 'POST'])
def profil():
    if 'user_id' not in session or session.get('role') != 'musteri':
        return redirect(url_for('login'))

    musteri_id = session['user_id']
    kullanici = db.get_musteri_by_id(musteri_id)

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'bilgi_guncelle':
            resim_yolu = None
            if 'profil_resim' in request.files:
                file = request.files['profil_resim']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(f"user_{musteri_id}_{file.filename}")
                    file.save(os.path.join(app.config['PROFILE_UPLOAD_FOLDER'], filename))
                    resim_yolu = filename
            
            if db.update_musteri_profil(musteri_id, request.form['ad'], request.form['soyad'], 
                                        request.form['telefon'], request.form['adres'], resim_yolu):
                session['user_name'] = f"{request.form['ad']} {request.form['soyad']}"
                if resim_yolu: session['user_img'] = resim_yolu # Session'ı güncelle
                flash("Profil güncellendi.", "success")
            return redirect(url_for('profil'))

        elif action == 'sifre_degistir':
            if not db.check_current_password(musteri_id, request.form['eski_sifre']):
                flash("Mevcut şifre yanlış.", "danger")
            elif request.form['yeni_sifre'] != request.form['yeni_sifre_tekrar']:
                flash("Yeni şifreler uyuşmuyor.", "warning")
            else:
                yeni_hash = generate_password_hash(request.form['yeni_sifre'])
                if db.update_musteri_sifre(musteri_id, yeni_hash): flash("Şifre değiştirildi.", "success")
            return redirect(url_for('profil'))

    return render_template('profil.html', user=kullanici)

# --- FAVORİLERİM SAYFASI ---
@app.route('/favorilerim')
def favorilerim():
    if 'user_id' not in session:
        flash("Favorilerinizi görmek için giriş yapmalısınız.", "warning")
        return redirect(url_for('login'))
    favori_araclar = db.get_user_favoriler_detayli(session['user_id'])
    return render_template('favorilerim.html', araclar=favori_araclar)

# --- FAVORİ EKLE/ÇIKAR (AJAX) ---
@app.route('/toggle-favori/<int:arac_id>', methods=['POST'])
def toggle_favori_api(arac_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Giriş yapmalısınız'}), 401
    sonuc = db.toggle_favori(session['user_id'], arac_id)
    return jsonify(sonuc)

# --- KUPON KONTROL (AJAX) ---
@app.route('/check-coupon', methods=['POST'])
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

# --- GİRİŞ / ÇIKIŞ / KAYIT (Moved to auth blueprint) ---

# ==========================================
#               ADMIN ROTALARI
# ==========================================

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('login'))
    istatistik = db.get_dashboard_stats()
    rezervasyonlar, musteriler, uyarilar = db.get_dashboard_tables()
    return render_template('admin_dashboard.html', istatistik=istatistik, rezervasyonlar=rezervasyonlar, 
                           musteriler=musteriler, uyarilar=uyarilar,
                           marka_isimleri=istatistik['marka_isimleri'], 
                           marka_sayilari=istatistik['marka_sayilari'],
                           ay_isimleri=istatistik['ay_isimleri'], 
                           aylik_kazanclar=istatistik['aylik_kazanclar'])

# --- DB MASTER ---
@app.route('/admin/database', methods=['GET', 'POST'])
def admin_database():
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('login'))
    tables = db.get_all_table_names()
    secilen_tablo = request.args.get('tablo')
    columns, rows = [], []
    if secilen_tablo:
        columns, rows = db.get_table_data(secilen_tablo)
    return render_template('admin_database.html', tables=tables, secilen_tablo=secilen_tablo, columns=columns, rows=rows)

@app.route('/admin/run-sql', methods=['POST'])
def admin_run_sql():
    if 'user_id' not in session or session.get('role') != 'admin': return jsonify({'status': 'error', 'message': 'Yetkisiz işlem'})
    result = db.run_custom_sql(request.form.get('query'))
    return jsonify(result)

# ... (Diğer Admin Rotaları) ...
@app.route('/admin/arac-ekle', methods=['GET', 'POST'])
def admin_arac_ekle():
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('login'))
    if request.method == 'GET': return render_template('admin_arac_ekle.html', sehirler=db.get_sehirler(), kategoriler=db.get_kategoriler())
    if request.method == 'POST':
        resim_url = 'default_car.jpg'
        if 'resim' in request.files:
            file = request.files['resim']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                resim_url = filename
        arac_bilgi = {'plaka': request.form['plaka'], 'marka': request.form['marka'], 'model': request.form['model'], 'yil': request.form['yil'], 'yakit': request.form['yakit_turu'], 'vites': request.form['vites_turu'], 'ucret': request.form['gunluk_ucret'], 'sehir': request.form['sehir_id'], 'kategori': request.form['kategori_id'], 'resim': resim_url}
        sigorta_bilgi = {'sirket': request.form['sigorta_sirketi'], 'police': request.form['police_no'], 'baslangic': request.form['sigorta_baslangic'], 'bitis': request.form['sigorta_bitis']}
        if db.add_arac_ve_sigorta(arac_bilgi, sigorta_bilgi): flash("Araç eklendi!", 'success')
        else: flash("Hata!", 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/teslim-al/<int:rezervasyon_id>')
def admin_teslim_al(rezervasyon_id):
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('login'))
    if db.teslim_al_arac(rezervasyon_id): flash('Araç teslim alındı.', 'success')
    else: flash('Hata!', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/sigortalar')
def admin_sigortalar():
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('login'))
    return render_template('admin_sigortalar.html', sigortalar=db.get_all_sigortalar())

@app.route('/admin/sigorta-guncelle/<int:sigorta_id>', methods=['GET', 'POST'])
def admin_sigorta_guncelle(sigorta_id):
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('login'))
    if request.method == 'POST':
        if db.update_sigorta(sigorta_id, {'sirket': request.form['sigorta_sirketi'], 'baslangic': request.form['baslangic_tarihi'], 'bitis': request.form['bitis_tarihi'], 'police': request.form['police_no']}):
            flash('Güncellendi.', 'success')
            return redirect(url_for('admin_sigortalar'))
    return render_template('admin_sigorta_duzenle.html', sigorta=db.get_sigorta_by_id(sigorta_id))

@app.route('/admin/kampanyalar', methods=['GET', 'POST'])
def admin_kampanyalar():
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('login'))
    if request.method == 'POST':
        if db.add_kampanya(request.form.get('kod').upper(), request.form.get('oran'), request.form.get('tarih')):
            flash(f"Kampanya oluşturuldu.", "success")
        else: flash("Hata.", "danger")
    return render_template('admin_kampanyalar.html', kampanyalar=db.get_all_kampanyalar())

@app.route('/admin/kampanya-sil/<int:id>')
def admin_kampanya_sil(id):
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('login'))
    db.delete_kampanya(id)
    flash("Silindi.", "success")
    return redirect(url_for('admin_kampanyalar'))

@app.route('/admin/bakim', methods=['GET', 'POST'])
def admin_bakim():
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('login'))
    if request.method == 'POST':
        if db.add_bakim(request.form.get('arac_id'), request.form.get('neden'), request.form.get('maliyet'), request.form.get('tarih')):
            flash("Bakım kaydı oluşturuldu.", "success")
        else: flash("Hata.", "danger")
        return redirect(url_for('admin_bakim'))
    return render_template('admin_bakim.html', bakimlar=db.get_bakim_listesi(), araclar=db.get_tum_araclar())

@app.route('/admin/bakim-bitir/<int:bakim_id>')
def admin_bakim_bitir(bakim_id):
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('login'))
    if db.finish_bakim(bakim_id): flash("Bakım tamamlandı.", "success")
    else: flash("Hata.", "danger")
    return redirect(url_for('admin_bakim'))

@app.route('/admin/takvim')
def admin_takvim():
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('login'))
    return render_template('admin_takvim.html')

@app.route('/api/calendar-events')
def api_calendar_events():
    if 'user_id' not in session or session.get('role') != 'admin': return jsonify([])
    events = db.get_calendar_events()
    formatted = [{'title': f"{e['plaka']} - {e['ad']}", 'start': str(e['baslangic_tarihi']), 'end': str(e['bitis_tarihi']), 'color': '#ffc107' if e['durum']=='Onaylandı' else '#198754'} for e in events]
    return jsonify(formatted)

@app.route('/admin/rapor-indir/<tur>')
def admin_rapor_indir(tur):
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('login'))
    data = db.get_tum_musteriler_excel() if tur == 'musteriler' else db.get_aylik_ciro_excel()
    if not data: flash("Veri yok.", "warning"); return redirect(url_for('admin_dashboard'))
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer: df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, download_name=f"{tur}_raporu.xlsx", as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/admin/yorumlar')
def admin_yorumlar():
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('login'))
    return render_template('admin_yorumlar.html', yorumlar=db.get_tum_yorumlar_admin())

@app.route('/admin/yorum-islem/<int:yorum_id>/<islem>')
def admin_yorum_islem(yorum_id, islem):
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('login'))
    if db.yorum_durum_degistir(yorum_id, islem): flash("İşlem başarılı.", "success")
    else: flash("Hata.", "danger")
    return redirect(url_for('admin_yorumlar'))

# --- PDF SÖZLEŞME İNDİRME ---
@app.route('/sozlesme-indir/<int:rezervasyon_id>')
def sozlesme_indir(rezervasyon_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # Veriyi çek
    data = db.get_rezervasyon_detay_pdf(rezervasyon_id)
    
    # Güvenlik ve Veri Kontrolü
    if not data or (session.get('role') != 'admin' and data['musteri_id'] != session['user_id']):
        flash("Bu sözleşmeye erişim hakkınız yok.", "danger")
        return redirect(url_for('index'))

    # Türkçe Karakter Düzeltme Fonksiyonu 
    def tr(text):
        if text is None: return ""
        text = str(text)
        mapping = {
            'ş': 's', 'Ş': 'S', 'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G', 
            'ü': 'u', 'Ü': 'U', 'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C',
            '₺': 'TL' 
        }
        for k, v in mapping.items(): text = text.replace(k, v)
        return text

    # PDF Başlat
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # 1. BAŞLIK VE LOGO ALANI
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(33, 37, 41) # Koyu Gri
    pdf.cell(0, 10, txt=tr("ARAÇ KİRALAMA SÖZLEŞMESİ"), ln=True, align='C')
    
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(100, 100, 100)
    tarih_str = datetime.now().strftime('%d.%m.%Y %H:%M')
    pdf.cell(0, 5, txt=tr(f"Sözleşme No: #RZ-{data['rezervasyon_id']}  |  Düzenlenme Tarihi: {tarih_str}"), ln=True, align='C')
    pdf.ln(5)

    # Çizgi
    pdf.set_draw_color(255, 193, 7) # Sarı Çizgi
    pdf.set_line_width(1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # 2. TARAFLAR (TABLO YAPISI)
    pdf.set_draw_color(200, 200, 200) # Gri Çerçeve
    pdf.set_line_width(0.2)
    pdf.set_fill_color(245, 245, 245) # Hafif Gri Arka Plan

    # Başlıklar
    pdf.set_font("Arial", 'B', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(95, 8, txt=tr("  A) KİRALAYAN (FİRMA BİLGİLERİ)"), border=1, fill=True)
    pdf.cell(95, 8, txt=tr("  B) KİRACI (MÜŞTERİ BİLGİLERİ)"), border=1, ln=True, fill=True)

    # İçerik
    pdf.set_font("Arial", '', 9)
    x_start = pdf.get_x()
    y_start = pdf.get_y()

    # Sol Taraf (Firma)
    pdf.cell(95, 6, txt=tr("  Ünvan: PREMIUM RENT A CAR A.Ş."), border='LRT')
    pdf.ln()
    pdf.cell(95, 6, txt=tr("  Adres: Maslak Mah. Büyükdere Cad. No:1 İstanbul"), border='LR')
    pdf.ln()
    pdf.cell(95, 6, txt=tr("  Telefon: 0850 123 45 67"), border='LR')
    pdf.ln()
    pdf.cell(95, 6, txt=tr("  Vergi Dairesi: İstanbul / Şişli"), border='LR')
    pdf.ln()
    pdf.cell(95, 6, txt=tr("  Mersis No: 012345678900015"), border='LRB')
    
    # Sağ Taraf (Müşteri) - Koordinatları sıfırla
    pdf.set_xy(x_start + 95, y_start)
    pdf.cell(95, 6, txt=tr(f"  Ad Soyad: {data['ad']} {data['soyad']}"), border='LRT', ln=True)
    
    pdf.set_x(x_start + 95)
    pdf.cell(95, 6, txt=tr(f"  TC / Pasaport: {data.get('ehliyet_no', 'Belirtilmedi')}"), border='LR', ln=True)
    
    pdf.set_x(x_start + 95)
    pdf.cell(95, 6, txt=tr(f"  Telefon: {data['telefon']}"), border='LR', ln=True)
    
    pdf.set_x(x_start + 95)
    pdf.cell(95, 6, txt=tr(f"  E-Posta: {data['eposta']}"), border='LR', ln=True)
    
    pdf.set_x(x_start + 95)
    pdf.cell(95, 6, txt=tr(f"  Adres: {data['adres'][:40]}..."), border='LRB', ln=True)
    
    pdf.ln(5)

    # 3. ARAÇ VE KİRALAMA DETAYLARI
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, txt=tr("  C) ARAÇ VE KİRALAMA BİLGİLERİ"), border=1, ln=True, fill=True)

    pdf.set_font("Arial", '', 9)
    
    # Başlıklar
    pdf.cell(47.5, 6, txt=tr("MARKA / MODEL"), border=1, align='C', fill=False)
    pdf.cell(47.5, 6, txt=tr("PLAKA"), border=1, align='C', fill=False)
    pdf.cell(47.5, 6, txt=tr("YAKIT / VİTES"), border=1, align='C', fill=False)
    pdf.cell(47.5, 6, txt=tr("SİGORTA TİPİ"), border=1, ln=True, align='C', fill=False)
    
    # Veriler
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(47.5, 8, txt=tr(f"{data['marka']} {data['model']}"), border=1, align='C')
    pdf.cell(47.5, 8, txt=tr(data['plaka']), border=1, align='C')
    pdf.cell(47.5, 8, txt=tr(f"{data['yakit_turu']} / {data.get('vites_turu', 'Otomatik')}"), border=1, align='C')
    pdf.cell(47.5, 8, txt=tr(f"{data.get('sigorta_sirketi', 'Full')} Kasko"), border=1, ln=True, align='C')

    # Tarihler
    pdf.set_font("Arial", '', 9)
    pdf.cell(95, 6, txt=tr("ALIŞ TARİHİ VE SAATİ"), border=1, align='C', fill=False)
    pdf.cell(95, 6, txt=tr("İADE TARİHİ VE SAATİ"), border=1, ln=True, align='C', fill=False)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(95, 8, txt=tr(f"{data['baslangic_tarihi']} - {data.get('alis_saati', '09:00')}"), border=1, align='C')
    pdf.cell(95, 8, txt=tr(f"{data['bitis_tarihi']} - {data.get('teslim_saati', '09:00')}"), border=1, ln=True, align='C')

    pdf.ln(5)

    # 4. HESAP DÖKÜMÜ VE EKSTRALAR
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, txt=tr("  D) HESAP DÖKÜMÜ VE EKSTRA HİZMETLER"), border=1, ln=True, fill=True)
    
    pdf.set_font("Arial", '', 9)
    
    # Ekstralar varsa listele
    if 'ekstralar' in data and data['ekstralar']:
        pdf.cell(140, 6, txt=tr("HİZMET ADI"), border='B', align='L')
        pdf.cell(50, 6, txt=tr("TUTAR"), border='B', ln=True, align='R')
        
        for ek in data['ekstralar']:
            pdf.cell(140, 6, txt=tr(f" - {ek['ad']}"), border=0)
            pdf.cell(50, 6, txt=tr(f"{ek['gunluk_ucret']} TL / Gun"), border=0, ln=True, align='R')
        pdf.ln(2)
    else:
        pdf.cell(0, 8, txt=tr("  * Ekstra hizmet seçilmemiştir."), border='LR', ln=True)

    # Toplam Tutar Kutusu
    pdf.set_fill_color(33, 37, 41) # Siyah
    pdf.set_text_color(255, 193, 7) # Sarı Yazı
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(130, 10, txt="", border=0)
    pdf.cell(60, 10, txt=tr(f"TOPLAM: {data['toplam_ucret']} TL"), border=1, ln=True, align='C', fill=True)
    
    pdf.set_text_color(0, 0, 0) # Rengi Sıfırla
    pdf.ln(5)

    # 5. YASAL METİN (FINE PRINT)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 6, txt=tr("  E) GENEL KİRALAMA KOŞULLARI VE TAAHHÜTNAME"), ln=True)
    
    pdf.set_font("Arial", '', 7)
    sozlesme_metni = (
        "1. TARAFLAR VE KONU: Isbu sözlesme, yukarida detaylari belirtilen aracin, belirlenen süre ve sartlarda kiraciya kiralanmasini kapsar.\n"
        "2. KULLANIM: Kiraci, araci Karayollari Trafik Kanunu'na uygun kullanmayi, alkollü/uyusturucu etkisinde kullanmamayi, "
        "araci üçüncü sahislara kullandirmamayi taahhüt eder.\n"
        "3. KAZA VE HASAR: Kaza durumunda kiraci, araci hareket ettirmeden polis/jandarma raporu tutturmak zorundadir. "
        "Rapor alinmazsa veya kiraci alkollü ise sigorta gecersizdir ve tüm hasardan kiraci sorumludur.\n"
        "4. CEZALAR: Kiralama süresi icindeki tüm trafik cezalari (HGS, OGS, Park, Hiz) kiraciya aittir. Ceza sonradan gelse dahi rücu edilir.\n"
        "5. TESLIM VE GECIKME: Arac, deposu teslim alindigi seviyede iade edilmelidir. 3 saati asan gecikmelerde tam gün ücreti tahsil edilir.\n"
        "6. YAKIT: Arac dolu depo teslim edildiyse dolu, bos teslim edildiyse bos iade edilmelidir. Eksik yakit farki + %20 servis bedeli alinir.\n"
        "7. YURT DISI: Aracin yurt disina cikarilmasi kesinlikle yasaktir.\n"
        "8. YETKILI MAHKEME: Isbu sözlesmeden dogacak ihtilaflarda Istanbul Mahkemeleri ve Icra Daireleri yetkilidir."
    )
    pdf.multi_cell(0, 4, txt=tr(sozlesme_metni), border=1, align='J')
    pdf.ln(5)

    # 6. İMZALAR
    y_imza = pdf.get_y()
    
    # Kiralayan Kutusu
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(95, 5, txt=tr("TESLİM EDEN (FİRMA YETKİLİSİ)"), align='C')
    pdf.cell(95, 5, txt=tr("TESLİM ALAN (KİRACI)"), align='C', ln=True)
    
    pdf.set_font("Arial", '', 8)
    pdf.cell(95, 4, txt=tr("Premium Rent A Car Operasyon"), align='C')
    pdf.cell(95, 4, txt=tr("Okudum, anladim, araci eksiksiz teslim aldim."), align='C', ln=True)
    
    # İmza Boşluğu
    pdf.ln(15)
    pdf.cell(95, 5, txt="..........................................", align='C')
    pdf.cell(95, 5, txt="..........................................", align='C', ln=True)
    
    pdf.set_font("Arial", "I", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.ln(5)
    pdf.cell(0, 5, txt=tr("Bu belge elektronik ortamda oluşturulmuştur. Islak imza gerektirmez."), align='C')

    # PDF Çıktısı
    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Sozlesme_{rezervasyon_id}.pdf'
    
    return response

if __name__ == '__main__':
    app.run(debug=True)