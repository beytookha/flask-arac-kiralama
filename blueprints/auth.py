from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.security import generate_password_hash
from itsdangerous import URLSafeTimedSerializer
from extensions import mail
from flask_mail import Message
import db_manager as db

# Blueprint Tanımlama
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def send_email(to, subject, template):
    """Yardımcı e-posta gönderme fonksiyonu."""
    try:
        msg = Message(subject, recipients=[to], html=template)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Mail Hatası: {e}")
        return False

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        eposta = request.form['eposta']
        sifre = request.form['sifre']
        sonuc = db.check_user_login(eposta, sifre)
        if sonuc:
            session.clear()
            user = sonuc['data']
            if sonuc['type'] == 'admin':
                session['user_id'] = user['personel_id']
                session['ad'] = user['ad']
                session['role'] = 'admin'
                session['gorev'] = user['gorev']
                flash(f"Hoşgeldin {user['ad']} (Yönetici)", "success")
                # Admin dashboard blueprint'i henüz yapılmadı, şimdilik app.py'deki rotaya gider
                # İlerde 'admin.dashboard' olacak
                return redirect(url_for('admin.dashboard')) 
            else:
                session['user_id'] = user['musteri_id']
                session['user_name'] = f"{user['ad']} {user['soyad']}"
                session['user_img'] = user.get('ProfilResim', 'default_user.png')
                session['role'] = 'musteri'
                flash(f"Hoşgeldin {user['ad']}", "success")
                return redirect(url_for('main.index'))
        else:
            flash("E-posta veya şifre hatalı!", "danger")
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        sifre = request.form.get('sifre')
        if sifre != request.form.get('confirm_sifre'):
            flash("Şifreler uyuşmuyor!", "danger")
            return redirect(url_for('auth.register'))
        bilgiler = {
            'ad': request.form.get('ad'), 'soyad': request.form.get('soyad'),
            'eposta': request.form.get('eposta'), 'telefon': request.form.get('telefon'),
            'dogum': request.form.get('dogum_tarihi'), 'ehliyet': request.form.get('ehliyet_no'),
            'adres': request.form.get('adres'), 'sifre': sifre
        }
        if db.register_musteri(bilgiler):
            flash("Kayıt başarılı! Giriş yapabilirsiniz.", "success")
            return redirect(url_for('auth.login'))
        else:
            flash("E-posta zaten kayıtlı!", "warning")
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Çıkış yapıldı.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        eposta = request.form['eposta']
        user = db.check_email_exists(eposta)
        
        if user:
            # Serializer'ı current_app üzerinden alıyoruz
            serializer = URLSafeTimedSerializer(current_app.secret_key)
            token = serializer.dumps(eposta, salt='password-reset-salt')
            link = url_for('auth.reset_password', token=token, _external=True)
            
            html_body = f"""
            <h3>Şifre Sıfırlama İsteği</h3>
            <p>Merhaba {user['ad']}, şifrenizi sıfırlamak için aşağıdaki linke tıklayın:</p>
            <a href="{link}" style="background:#ffc107; padding:10px 20px; color:#000; text-decoration:none; font-weight:bold;">Şifremi Sıfırla</a>
            """
            
            if send_email(eposta, "Şifre Sıfırlama", html_body):
                flash("Sıfırlama linki e-posta adresinize gönderildi.", "info")
            else:
                flash("E-posta gönderilemedi (SMTP Ayarlarını kontrol edin).", "warning")
        else:
            flash("Bu e-posta adresiyle kayıtlı kullanıcı bulunamadı.", "warning")
            
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    serializer = URLSafeTimedSerializer(current_app.secret_key)
    try:
        eposta = serializer.loads(token, salt='password-reset-salt', max_age=1800)
    except:
        flash("Sıfırlama linki geçersiz veya süresi dolmuş.", "danger")
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        yeni_sifre = request.form['yeni_sifre']
        if db.update_password_by_email(eposta, yeni_sifre):
            flash("Şifreniz başarıyla güncellendi! Giriş yapabilirsiniz.", "success")
            return redirect(url_for('auth.login'))
        else:
            flash("Hata oluştu.", "danger")
            
    return render_template('auth/reset_password.html', token=token)

# Admin login alias
@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    return login()
