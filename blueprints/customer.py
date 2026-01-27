import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, make_response, current_app
from werkzeug.utils import secure_filename
from fpdf import FPDF
from extensions import mail
from flask_mail import Message
import db_manager as db

customer_bp = Blueprint('customer', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def send_email(to, subject, template):
    try:
        msg = Message(subject, recipients=[to], html=template)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Mail Hatası: {e}")
        return False

# --- REZERVASYON ÖZETİ ---
@customer_bp.route('/rezervasyon/<int:arac_id>', methods=['GET', 'POST'])
def rezervasyon(arac_id):
    if 'user_id' not in session:
        flash('Rezervasyon yapmak için önce giriş yapmalısınız.', 'danger')
        return redirect(url_for('auth.login', next=request.url))

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
            return redirect(url_for('customer.odeme_yap'))

    return render_template('customer/rezervasyon.html', arac=arac, ekstralar=ekstra_hizmetler,
                           url_baslangic=url_baslangic, url_bitis=url_bitis)

# --- ÖDEME ---
@customer_bp.route('/odeme', methods=['GET', 'POST'])
def odeme_yap():
    if 'rezervasyon_bilgi' not in session:
        return redirect(url_for('main.index'))

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
                html_body = render_template('customer/email_confirmation.html', 
                                            musteri=musteri, 
                                            arac=arac, 
                                            rez=session['rezervasyon_bilgi'])
                send_email(musteri['eposta'], "Rezervasyon Onayı - Rent A Car", html_body)
            except:
                pass 

            session.pop('rezervasyon_bilgi', None)
            flash(f'✅ Ödeme Başarılı! Rezervasyonunuz oluşturuldu.', 'success')
            return redirect(url_for('customer.kiralamalarim'))
        else:
            flash('Bir hata oluştu.', 'danger')

    return render_template('customer/odeme.html', arac=arac)

# --- MÜŞTERİ KİRALAMALARI ---
@customer_bp.route('/kiralamalarim')
def kiralamalarim():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    kiralamalar = db.get_musteri_rezervasyonlari(session['user_id'])
    return render_template('customer/kiralamalarim.html', kiralamalar=kiralamalar)

# --- YORUM YAPMA  ---
@customer_bp.route('/yorum-yap', methods=['POST'])
def yorum_yap():
    if 'user_id' not in session or session.get('role') != 'musteri':
        flash("Yorum yapmak için müşteri girişi yapmalısınız.", "warning")
        return redirect(url_for('auth.login'))
    
    metin = request.form.get('yorum_metni')
    puan = request.form.get('puan')
    
    if db.add_yorum(session['user_id'], metin, puan):
        flash("Yorumunuz alındı! Yönetici onayından sonra yayınlanacaktır.", "success")
    else:
        flash("Bir hata oluştu.", "danger")
        
    return redirect(url_for('main.index'))

# --- PROFIL SAYFASI ---
@customer_bp.route('/profil', methods=['GET', 'POST'])
def profil():
    if 'user_id' not in session or session.get('role') != 'musteri':
        return redirect(url_for('auth.login'))

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
                    file.save(os.path.join(current_app.config['PROFILE_UPLOAD_FOLDER'], filename))
                    resim_yolu = filename
            
            if db.update_musteri_profil(musteri_id, request.form['ad'], request.form['soyad'], 
                                        request.form['telefon'], request.form['adres'], resim_yolu):
                session['user_name'] = f"{request.form['ad']} {request.form['soyad']}"
                if resim_yolu: session['user_img'] = resim_yolu 
                flash("Profil güncellendi.", "success")
            return redirect(url_for('customer.profil'))

        elif action == 'sifre_degistir':
            if not db.check_current_password(musteri_id, request.form['eski_sifre']):
                flash("Mevcut şifre yanlış.", "danger")
            elif request.form['yeni_sifre'] != request.form['yeni_sifre_tekrar']:
                flash("Yeni şifreler uyuşmuyor.", "warning")
            else:
                from werkzeug.security import generate_password_hash
                yeni_hash = generate_password_hash(request.form['yeni_sifre'])
                if db.update_musteri_sifre(musteri_id, yeni_hash): flash("Şifre değiştirildi.", "success")
            return redirect(url_for('customer.profil'))

    return render_template('customer/profil.html', user=kullanici)

# --- FAVORİLERİM SAYFASI ---
@customer_bp.route('/favorilerim')
def favorilerim():
    if 'user_id' not in session:
        flash("Favorilerinizi görmek için giriş yapmalısınız.", "warning")
        return redirect(url_for('auth.login'))
    favori_araclar = db.get_user_favoriler_detayli(session['user_id'])
    return render_template('customer/favorilerim.html', araclar=favori_araclar)

# --- PDF SÖZLEŞME İNDİRME ---
@customer_bp.route('/sozlesme-indir/<int:rezervasyon_id>')
def sozlesme_indir(rezervasyon_id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    data = db.get_rezervasyon_detay_pdf(rezervasyon_id)
    
    if not data or (session.get('role') != 'admin' and data['musteri_id'] != session['user_id']):
        flash("Bu sözleşmeye erişim hakkınız yok.", "danger")
        return redirect(url_for('main.index'))

    # Türkçe Karakter Düzeltme
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

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # --- 1. BAŞLIK VE LOGO ---
    pdf.set_font("Arial", 'B', 24)
    pdf.set_text_color(33, 37, 41)
    pdf.cell(0, 15, txt=tr("RENT A CAR"), ln=True, align='C')
    
    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, txt=tr("ARAÇ KİRALAMA SÖZLEŞMESİ"), ln=True, align='C')
    
    tarih_str = datetime.now().strftime('%d.%m.%Y')
    pdf.cell(0, 8, txt=tr(f"Sözleşme No: #RZ-{data['rezervasyon_id']}  |  Tarih: {tarih_str}"), ln=True, align='C')
    
    pdf.ln(8)

    # --- 2. TARAFLAR (Müşteri ve Şirket) ---
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, txt=tr("1. TARAFLAR VE BİLGİLER"), ln=True, fill=True)
    pdf.ln(4)

    pdf.set_font("Arial", '', 10)
    
    # Sol Sütun ve Sağ Sütun Ayarları
    y_before_parties = pdf.get_y()
    
    # SOL SÜTUN (KİRACI)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(95, 6, txt=tr("KİRACI (MÜŞTERİ)"), ln=True)
    pdf.set_font("Arial", '', 9)
    pdf.cell(95, 5, txt=tr(f"Ad Soyad: {data['ad']} {data['soyad']}"), ln=True)
    pdf.cell(95, 5, txt=tr(f"TC/Pasaport: {data.get('tc_no', '-------')}"), ln=True)
    pdf.cell(95, 5, txt=tr(f"Telefon: {data['telefon']}"), ln=True)
    pdf.cell(95, 5, txt=tr(f"E-Posta: {data['eposta']}"), ln=True)
    pdf.multi_cell(90, 5, txt=tr(f"Adres: {data['adres']}"))
    
    y_after_left = pdf.get_y()

    # SAĞ SÜTUN (KİRALAYAN) - En başa dön, sağa kay
    pdf.set_xy(110, y_before_parties)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(90, 6, txt=tr("KİRALAYAN (FİRMA)"), ln=True)
    pdf.set_font("Arial", '', 9)
    # Sağ sütun hücrelerinde x'i manuel set etmemiz lazım çünkü ln=True solu sıfırlar
    
    def right_col(text):
        pdf.set_x(110)
        pdf.cell(90, 5, txt=tr(text), ln=True)

    right_col("Firma Adı: RENT A CAR OTO. A.Ş.")
    right_col("Vergi No: 1234567890")
    right_col("Telefon: +90 850 123 45 67")
    right_col("Adres: İstanbul, Türkiye")

    # İki sütundan hangisi daha aşağıda bittiyse oraya git
    y_after_right = pdf.get_y()
    pdf.set_y(max(y_after_left, y_after_right) + 5)

    # --- 3. ARAÇ BİLGİLERİ ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt=tr("2. KİRALANAN ARAÇ BİLGİLERİ"), ln=True, fill=True)
    pdf.ln(2)

    pdf.set_font("Arial", 'B', 9)
    # Tablo Genişlikleri (Toplam ~190 olmalı)
    w_marka = 50
    w_plaka = 35
    w_yil = 25
    w_yakit = 35
    w_sigorta = 45

    pdf.cell(w_marka, 8, txt=tr("Marka / Model"), border=1)
    pdf.cell(w_plaka, 8, txt=tr("Plaka"), border=1)
    pdf.cell(w_yil, 8, txt=tr("Yıl"), border=1)
    pdf.cell(w_yakit, 8, txt=tr("Yakıt / Vites"), border=1)
    pdf.cell(w_sigorta, 8, txt=tr("Sigorta / Poliçe"), border=1, ln=True)

    pdf.set_font("Arial", '', 9)
    pdf.cell(w_marka, 8, txt=tr(f"{data['marka']} {data['model']}"), border=1)
    pdf.cell(w_plaka, 8, txt=tr(f"{data['plaka']}"), border=1)
    pdf.cell(w_yil, 8, txt=tr(f"{data['yil']}"), border=1)
    pdf.cell(w_yakit, 8, txt=tr(f"{data['yakit_turu']}"), border=1)
    pdf.cell(w_sigorta, 8, txt=tr(f"{data.get('sigorta_sirketi', '-')} / {data.get('police_no', '-')}"), border=1, ln=True)
    
    pdf.ln(8)

    # --- 4. KİRALAMA DETAYLARI VE ÜCRET ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt=tr("3. KİRALAMA VE ÖDEME DETAYLARI"), ln=True, fill=True)
    pdf.ln(2)

    pdf.set_font("Arial", '', 9)
    
    # 3 Hücreli Bilgi
    pdf.cell(63, 8, txt=tr(f"Alış Tarihi: {data['baslangic_tarihi']}"), border=1)
    pdf.cell(63, 8, txt=tr(f"İade Tarihi: {data['bitis_tarihi']}"), border=1)
    
    d1 = datetime.strptime(str(data['baslangic_tarihi']), "%Y-%m-%d")
    d2 = datetime.strptime(str(data['bitis_tarihi']), "%Y-%m-%d")
    gun = (d2 - d1).days
    pdf.cell(64, 8, txt=tr(f"Toplam Süre: {gun} Gün"), border=1, ln=True)
    
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(190, 8, txt=tr("EKSTRA HİZMETLER:"), ln=True, border='B')
    
    pdf.set_font("Arial", '', 9)
    if data.get('ekstralar'):
        ekstra_str = ", ".join([f"{e['ad']} ({e['gunluk_ucret']} TL)" for e in data['ekstralar']])
        pdf.multi_cell(190, 6, txt=tr(ekstra_str))
    else:
        pdf.cell(190, 6, txt=tr("Ekstra hizmet alınmamıştır."), ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    if data.get('indirim_kodu'):
        pdf.cell(0, 10, txt=tr(f"TOPLAM TUTAR: {data['toplam_ucret']} TL (İndirim Kodu: {data['indirim_kodu']})"), ln=True, align='R')
    else:
        pdf.cell(0, 10, txt=tr(f"TOPLAM TUTAR: {data['toplam_ucret']} TL"), ln=True, align='R')
    
    pdf.ln(10)

    # --- 5. ŞARTLAR VE İMZA ---
    if pdf.get_y() > 220: pdf.add_page() # Sayfa sonunda yer kalmadıysa yeni sayfa

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt=tr("4. GENEL ŞARTLAR VE İMZA"), ln=True, fill=True)
    pdf.ln(2)
    
    pdf.set_font("Arial", '', 8)
    sartlar = (
        "1. Kiracı, aracı karayolları trafik kanununa uygun olarak özenle kullanmayı kabul eder.\n"
        "2. Aracın kira süresi içinde karışacağı her türlü kaza, hasar ve trafik cezalarından kiracı sorumludur.\n"
        "3. Araç, sözleşmede belirtilen tarihte ve saatte, yakıt seviyesi aynı şekilde teslim edilmelidir.\n"
        "4. Kiralayan, aracın teknik bakımlarını eksiksiz yaptığını beyan eder.\n"
        "5. İşbu sözleşme ihtilaf vukuunda İstanbul Mahkemeleri ve İcra Daireleri yetkilidir.\n"
        "6. Kiracı, aracı üçüncü şahıslara kullandıramaz, devredemez.\n"
        "7. Geç teslimlerde her saat için günlük kira bedelinin 1/3'ü kadar ceza uygulanır."
    )
    pdf.multi_cell(0, 5, txt=tr(sartlar))
    
    pdf.ln(15)
    
    # İmzalar
    y_sig = pdf.get_y()
    pdf.set_font("Arial", 'B', 10)
    # Sol imza
    pdf.cell(90, 6, txt=tr("TESLİM EDEN (FİRMA YETKİLİSİ)"), align='C')
    # Sağ imza
    pdf.set_x(110)
    pdf.cell(90, 6, txt=tr("TESLİM ALAN (KİRACI)"), align='C', ln=True)
    
    pdf.set_font("Arial", '', 9)
    # Sol boşluk
    pdf.cell(90, 20, txt="", border=1) # İmza kutusu
    # Sağ boşluk
    pdf.set_x(110)
    pdf.cell(90, 20, txt="", border=1, ln=True) # İmza kutusu
    
    # Altbilgi
    pdf.set_y(-20)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, txt=tr("Bu belge elektronik ortamda oluşturulmuştur. Islak imza gerektirir."), align='C')

    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Sozlesme_{rezervasyon_id}.pdf'
    
    return response
