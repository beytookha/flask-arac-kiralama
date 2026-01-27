# 🚗 Rent A Car - Araç Kiralama Sistemi

Modern, kullanıcı dostu ve kapsamlı bir Araç Kiralama Web Uygulaması. Flask altyapısı ile geliştirilen bu proje, hem müşteriler hem de yöneticiler için gelişmiş özellikler sunar.


## 🌟 Özellikler

### 👤 Müşteri Paneli
- **Araç Kiralama:** Tarih ve saat seçimi ile kolay rezervasyon.
- **Gelişmiş Filtreleme:** Şehir, vites tipi, yakıt türü ve fiyat aralığına göre araç arama.
- **Dinamik Fiyatlandırma:** Gün sayısı ve seçilen ekstra hizmetlere (Sigorta, Bebek Koltuğu vb.) göre otomatik hesaplama.
- **Kullanıcı Hesabı:** Profil düzenleme, şifre değiştirme ve geçmiş kiralamaları görüntüleme.
- **Favoriler:** Beğenilen araçları favorilere ekleme.
- **Yorum Sistemi:** Kiralanan araçlara puan ve yorum bırakma.

### 🛡️ Yönetici (Admin) Paneli
- **Dashboard:** Anlık ciro, aktif kiralama, araç sayısı ve doluluk oranları.
- **Araç Yönetimi:** Yeni araç ekleme, resim yükleme ve bilgilerini güncelleme.
- **Rezervasyon Yönetimi:** Gelen talepleri onaylama, red etme veya teslim alma.
- **Takvim Görünümü:** Kiradaki araçların takvim üzerinde takibi.
- **Finansal Raporlar:** Aylık ciro analizi ve Excel olarak rapor indirme.
- **Sigorta Takibi:** Araç sigorta sürelerinin takibi ve uyarı sistemi.

## 🛠️ Teknolojiler

- **Backend:** Python, Flask
- **Veritabanı:** SQLite (Geliştirme aşamasında), SQLAlchemy (ORM gerekirse)
- **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript (ES6)
- **Diğer:** Pandas (Excel Raporlama), Chart.js (Grafikler), Leaflet (Harita)

## 🚀 Kurulum ve Çalıştırma

Projenin bilgisayarınızda çalışması için aşağıdaki adımları izleyin:

### 1. Projeyi Klonlayın
```bash
git clone https://github.com/kullaniciadi/flask-rent-a-car.git
cd flask-rent-a-car
```

### 2. Sanal Ortam Oluşturun (Önerilen)
```bash
# Mac/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Gerekli Kütüphaneleri Yükleyin
```bash
pip install -r requirements.txt
```

### 4. Veritabanını Hazırlayın
Projeyi ilk kez çalıştırıyorsanız veritabanını ve örnek verileri oluşturun:
```bash
python setup_db.py  # Tabloları oluşturur
python seed.py      # Örnek araç ve kullanıcı verilerini ekler
```

### 5. Uygulamayı Başlatın
```bash
python app.py
```
Tarayıcınızda `http://127.0.0.1:5000` adresine giderek projeyi görüntüleyebilirsiniz.

## 📂 Proje Yapısı

```
FlaskProjem/
├── app.py              # Ana uygulama dosyası
├── blueprints/         # Modüler yapı (Auth, Admin, Customer, Main, API)
├── db_manager.py       # Veritabanı sorgu ve bağlantı işlemleri
├── static/             # CSS, JS, Resimler
├── templates/          # HTML Dosyaları
├── requirements.txt    # Kütüphane listesi
└── schema.sql          # Veritabanı şeması
```

## 🔑 Varsayılan Hesaplar (Seed Çalıştırıldıysa)

- **Admin Hesabı:** `admin@rentacar.com` / `1234`

## 📄 Lisans

Bu proje eğitim ve portföy amaçlı geliştirilmiştir. Kaynak göstererek kullanabilirsiniz.

---
*Geliştirici: [Beytullah/beytookha]*
