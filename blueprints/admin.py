import os
import io
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
import db_manager as db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# --- ADMIN PANELİ (Login Check Decorator could be useful here but explicit check is fine) ---

@admin_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('auth.login'))
    # istatistik = db.get_dashboard_stats()  <-- Moved to API
    rezervasyonlar, musteriler, uyarilar = db.get_dashboard_tables()
    return render_template('admin/dashboard.html', rezervasyonlar=rezervasyonlar, 
                           musteriler=musteriler, uyarilar=uyarilar)

# --- DB MASTER ---
@admin_bp.route('/database', methods=['GET', 'POST'])
def database():
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('auth.login'))
    tables = db.get_all_table_names()
    secilen_tablo = request.args.get('tablo')
    columns, rows = [], []
    if secilen_tablo:
        columns, rows = db.get_table_data(secilen_tablo)
    return render_template('admin/database.html', tables=tables, secilen_tablo=secilen_tablo, columns=columns, rows=rows)



@admin_bp.route('/arac-ekle', methods=['GET', 'POST'])
def arac_ekle():
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('auth.login'))
    if request.method == 'GET': return render_template('admin/arac_ekle.html', sehirler=db.get_sehirler(), kategoriler=db.get_kategoriler())
    if request.method == 'POST':
        resim_url = 'default_car.jpg'
        if 'resim' in request.files:
            file = request.files['resim']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                resim_url = filename
        arac_bilgi = {'plaka': request.form['plaka'], 'marka': request.form['marka'], 'model': request.form['model'], 'yil': request.form['yil'], 'yakit': request.form['yakit_turu'], 'vites': request.form['vites_turu'], 'ucret': request.form['gunluk_ucret'], 'sehir': request.form['sehir_id'], 'kategori': request.form['kategori_id'], 'resim': resim_url}
        sigorta_bilgi = {'sirket': request.form['sigorta_sirketi'], 'police': request.form['police_no'], 'baslangic': request.form['sigorta_baslangic'], 'bitis': request.form['sigorta_bitis']}
        
        if db.add_arac_ve_sigorta(arac_bilgi, sigorta_bilgi): 
            flash("Araç eklendi!", 'success')
        else: 
            flash("Hata!", 'danger')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/teslim-al/<int:rezervasyon_id>')
def teslim_al(rezervasyon_id):
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('auth.login'))
    if db.teslim_al_arac(rezervasyon_id): flash('Araç teslim alındı.', 'success')
    else: flash('Hata!', 'danger')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/sigortalar')
def sigortalar():
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('auth.login'))
    return render_template('admin/sigortalar.html', sigortalar=db.get_all_sigortalar())

@admin_bp.route('/sigorta-guncelle/<int:sigorta_id>', methods=['GET', 'POST'])
def sigorta_guncelle(sigorta_id):
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('auth.login'))
    if request.method == 'POST':
        if db.update_sigorta(sigorta_id, {'sirket': request.form['sigorta_sirketi'], 'baslangic': request.form['baslangic_tarihi'], 'bitis': request.form['bitis_tarihi'], 'police': request.form['police_no']}):
            flash('Güncellendi.', 'success')
            return redirect(url_for('admin.sigortalar'))
    return render_template('admin/sigorta_duzenle.html', sigorta=db.get_sigorta_by_id(sigorta_id))

@admin_bp.route('/kampanyalar', methods=['GET', 'POST'])
def kampanyalar():
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('auth.login'))
    if request.method == 'POST':
        if db.add_kampanya(request.form.get('kod').upper(), request.form.get('oran'), request.form.get('tarih')):
            flash(f"Kampanya oluşturuldu.", "success")
        else: flash("Hata.", "danger")
    return render_template('admin/kampanyalar.html', kampanyalar=db.get_all_kampanyalar())

@admin_bp.route('/kampanya-sil/<int:id>')
def kampanya_sil(id):
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('auth.login'))
    db.delete_kampanya(id)
    flash("Silindi.", "success")
    return redirect(url_for('admin.kampanyalar'))

@admin_bp.route('/bakim', methods=['GET', 'POST'])
def bakim():
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('auth.login'))
    if request.method == 'POST':
        if db.add_bakim(request.form.get('arac_id'), request.form.get('neden'), request.form.get('maliyet'), request.form.get('tarih')):
            flash("Bakım kaydı oluşturuldu.", "success")
        else: flash("Hata.", "danger")
        return redirect(url_for('admin.bakim'))
    return render_template('admin/bakim.html', bakimlar=db.get_bakim_listesi(), araclar=db.get_tum_araclar())

@admin_bp.route('/bakim-bitir/<int:bakim_id>')
def bakim_bitir(bakim_id):
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('auth.login'))
    if db.finish_bakim(bakim_id): flash("Bakım tamamlandı.", "success")
    else: flash("Hata.", "danger")
    return redirect(url_for('admin.bakim'))

@admin_bp.route('/takvim')
def takvim():
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('auth.login'))
    return render_template('admin/takvim.html')



@admin_bp.route('/rapor-indir/<tur>')
def rapor_indir(tur):
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('auth.login'))
    data = db.get_tum_musteriler_excel() if tur == 'musteriler' else db.get_aylik_ciro_excel()
    if not data: flash("Veri yok.", "warning"); return redirect(url_for('admin.dashboard'))
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer: df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, download_name=f"{tur}_raporu.xlsx", as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@admin_bp.route('/yorumlar')
def yorumlar():
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('auth.login'))
    return render_template('admin/yorumlar.html', yorumlar=db.get_tum_yorumlar_admin())

@admin_bp.route('/yorum-islem/<int:yorum_id>/<islem>')
def yorum_islem(yorum_id, islem):
    if 'user_id' not in session or session.get('role') != 'admin': return redirect(url_for('auth.login'))
    if db.yorum_durum_degistir(yorum_id, islem): flash("İşlem başarılı.", "success")
    else: flash("Hata.", "danger")
    return redirect(url_for('admin.yorumlar'))
