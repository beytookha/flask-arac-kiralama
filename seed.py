import mysql.connector
from werkzeug.security import generate_password_hash
import random
from datetime import date, datetime, timedelta
import sys

# === VERİTABANI AYARLARI ===
DB_CONFIG = {
    'user': 'root',
    'password': '1234',  # Şifreni buraya yaz
    'host': 'localhost',
    'raise_on_warnings': True
}
DB_NAME = 'arac_kiralama'

# === AYARLAR ===
N_ARAC = 250        
N_MUSTERI = 100     
N_REZERVASYON = 300 

# === SABİT VERİ LİSTELERİ ===
SEHIRLER = [
    'İstanbul', 'Ankara', 'İzmir', 'Konya', 'Antalya', 'Bursa', 'Adana', 'Gaziantep', 
    'Kayseri', 'Eskişehir', 'Mersin', 'Samsun', 'Trabzon', 'Denizli', 'Diyarbakır', 
    'Şanlıurfa', 'Malatya', 'Aydın', 'Muğla', 'Tekirdağ'
]

KATEGORILER = ['Ekonomik', 'Orta Sınıf', 'SUV', 'Lüks', 'Minivan', 'Elektrikli']

EKSTRA_HIZMETLER = [
    ('Bebek Koltuğu', 50.00, 'fas fa-baby-carriage'),
    ('Navigasyon (GPS)', 30.00, 'fas fa-map-marked-alt'),
    ('Ek Sürücü', 100.00, 'fas fa-user-plus'),
    ('Kış Lastiği', 75.00, 'fas fa-snowflake'),
    ('Full Kasko Güvencesi', 200.00, 'fas fa-shield-alt'),
    ('HGS/OGS Paketi', 40.00, 'fas fa-road'),
    ('Wi-Fi Hotspot', 60.00, 'fas fa-wifi'),
    ('Premium Temizlik', 80.00, 'fas fa-broom')
]

KAMPANYALAR = [
    ('YAZ2025', 15, '2025-09-01'),
    ('HOSGELDIN', 10, '2030-12-31'),
    ('VIP20', 20, '2025-12-31'),
    ('KIS2025', 12, '2026-03-31'),
    ('WEEKEND', 8, '2026-12-31')
]

SIGORTA_SIRKETLERI = ['Allianz', 'AXA', 'Anadolu', 'Mapfre', 'Sompo', 'Aksigorta', 'HDI', 'Zurich']

ARAC_HAVUZU = {
    'Fiat': [('Egea', 'egea.jpg'), ('Egea Cross', 'egeacross.jpg')],
    'Renault': [('Clio', 'clio.jpg'), ('Megane', 'megane.jpg')],
    'Toyota': [('Corolla', 'corolla.jpg')],
    'Volkswagen': [('Passat', 'passat.jpg')],
    'Ford': [('Focus', 'focus.jpg')],
    'Hyundai': [('i20', 'i20.jpg')],
    'Peugeot': [('3008', 'peugeot3008.jpg')],
    'BMW': [('520i', 'bmw520.jpg')],
    'Mercedes': [('Vito', 'vito.jpg')],
    'Audi': [('A3', 'a3.jpg')],
    'Honda': [('Civic', 'civic.jpg')],
    'Nissan': [('Qashqai', 'qashqai.jpg')],
    'Jeep': [('Renegade', 'renegade.jpg')],
    'Citroen': [('C3', 'c3.jpg')],
    'Dacia': [('Duster', 'duster.jpg')],
    'Opel': [('Corsa', 'corsa.jpg')]
}

ISIMLER = ['Ahmet','Mehmet','Ayse','Fatma','Ali','Zeynep','Can','Elif','Mert','Ece','Deniz','Emre','Seda','Burak','Cem','Naz']
SOYISIMLER = ['Yilmaz','Kaya','Demir','Sahin','Celik','Yildiz','Aydin','Koc','Arslan','Dogan','Ozturk','Kara','Aslan','Polat']

YORUMLAR = [
    ('Hizmetten çok memnun kaldım, araç tertemizdi.', 5),
    ('Fiyat performans harika, tekrar kiralayacağım.', 5),
    ('Araç biraz kirliydi ama personel ilgiliydi.', 4),
    ('Her şey yolundaydı, teşekkürler.', 5),
    ('Teslimatta biraz bekledim ama sorun çözüldü.', 3),
    ('Harika bir deneyimdi, araç yeni gibiydi.', 5)
]

def get_connection():
    # [DÜZELTME] Bağlantıya database ismini ekliyoruz!
    config = DB_CONFIG.copy()
    config['database'] = DB_NAME
    return mysql.connector.connect(**config)

def create_database(cursor):
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    print(f"✅ Veritabanı '{DB_NAME}' sıfırdan oluşturuldu.")

def create_tables(cursor):
    # Veritabanını kullanacağımızı garantiye alıyoruz
    cursor.execute(f"USE {DB_NAME}")
    
    tables = [
        """CREATE TABLE Sehir (sehir_id INT AUTO_INCREMENT PRIMARY KEY, sehir_ad VARCHAR(50) NOT NULL)""",
        
        """CREATE TABLE Kategori (kategori_id INT AUTO_INCREMENT PRIMARY KEY, kategori_ad VARCHAR(50) NOT NULL)""",
        
        """CREATE TABLE EkstraHizmet (ekstra_id INT AUTO_INCREMENT PRIMARY KEY, ad VARCHAR(50) NOT NULL, 
           gunluk_ucret DECIMAL(10,2) NOT NULL, ikon VARCHAR(50) DEFAULT 'fas fa-plus')""",
        
        """CREATE TABLE Sigorta (sigorta_id INT AUTO_INCREMENT PRIMARY KEY, sigorta_sirketi VARCHAR(50) NOT NULL, 
           baslangic_tarihi DATE NOT NULL, bitis_tarihi DATE NOT NULL, police_no VARCHAR(50) UNIQUE)""",
        
        """CREATE TABLE Personel (personel_id INT AUTO_INCREMENT PRIMARY KEY, ad VARCHAR(50) NOT NULL, 
           soyad VARCHAR(50) NOT NULL, gorev ENUM('Yönetici','Satış Temsilcisi') NOT NULL, 
           eposta VARCHAR(100) UNIQUE NOT NULL, sifre VARCHAR(255) NOT NULL)""",
        
        """CREATE TABLE Musteri (musteri_id INT AUTO_INCREMENT PRIMARY KEY, ad VARCHAR(50) NOT NULL, 
           soyad VARCHAR(50) NOT NULL, eposta VARCHAR(100) UNIQUE NOT NULL, sifre VARCHAR(255) NOT NULL, 
           telefon VARCHAR(15), ehliyet_no VARCHAR(20), adres TEXT, 
           ProfilResim VARCHAR(255) DEFAULT 'default_user.png', dogum_tarihi DATE)""",
        
        """CREATE TABLE Arac (arac_id INT AUTO_INCREMENT PRIMARY KEY, plaka VARCHAR(15) UNIQUE NOT NULL, 
           marka VARCHAR(30) NOT NULL, model VARCHAR(30) NOT NULL, yil INT, 
           yakit_turu ENUM('Benzin', 'Dizel', 'Elektrik', 'Hibrit') NOT NULL, 
           vites_turu ENUM('Manuel', 'Otomatik') NOT NULL, kilometre INT DEFAULT 0, 
           gunluk_ucret DECIMAL(10,2), resim_url VARCHAR(255) DEFAULT 'default_car.jpg', 
           durum ENUM('Müsait','Kirada','Bakımda') DEFAULT 'Müsait', kategori_id INT, 
           sigorta_id INT, bulundugu_sehir_id INT, 
           FOREIGN KEY (kategori_id) REFERENCES Kategori(kategori_id), 
           FOREIGN KEY (sigorta_id) REFERENCES Sigorta(sigorta_id), 
           FOREIGN KEY (bulundugu_sehir_id) REFERENCES Sehir(sehir_id))""",
        
        """CREATE TABLE Kampanya (kampanya_id INT AUTO_INCREMENT PRIMARY KEY, kod VARCHAR(20) UNIQUE NOT NULL, 
           indirim_orani INT NOT NULL, son_kullanma_tarihi DATE NOT NULL, aktif BOOLEAN DEFAULT TRUE)""",
        
        """CREATE TABLE Rezervasyon (rezervasyon_id INT AUTO_INCREMENT PRIMARY KEY, musteri_id INT NOT NULL, 
           arac_id INT NOT NULL, baslangic_tarihi DATE NOT NULL, bitis_tarihi DATE NOT NULL, 
           alis_saati VARCHAR(5), teslim_saati VARCHAR(5), toplam_ucret DECIMAL(10,2), 
           indirim_kodu VARCHAR(20), durum ENUM('Onaylandı','Bekliyor','İptal','Tamamlandı','Kirada') DEFAULT 'Bekliyor', 
           FOREIGN KEY (musteri_id) REFERENCES Musteri(musteri_id), 
           FOREIGN KEY (arac_id) REFERENCES Arac(arac_id))""",
        
        """CREATE TABLE RezervasyonEkstra (id INT AUTO_INCREMENT PRIMARY KEY, rezervasyon_id INT NOT NULL, 
           ekstra_id INT NOT NULL, FOREIGN KEY (rezervasyon_id) REFERENCES Rezervasyon(rezervasyon_id) ON DELETE CASCADE, 
           FOREIGN KEY (ekstra_id) REFERENCES EkstraHizmet(ekstra_id))""",
        
        """CREATE TABLE Odeme (odeme_id INT AUTO_INCREMENT PRIMARY KEY, rezervasyon_id INT NOT NULL, 
           odeme_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP, odeme_tutari DECIMAL(10,2), 
           kart_sahibi VARCHAR(100), kart_no_son4 VARCHAR(4), odeme_turu ENUM('Kredi Kartı','Havale') DEFAULT 'Kredi Kartı', 
           FOREIGN KEY (rezervasyon_id) REFERENCES Rezervasyon(rezervasyon_id))""",
        
        """CREATE TABLE Yorum (yorum_id INT AUTO_INCREMENT PRIMARY KEY, musteri_id INT NOT NULL, 
           yorum_metni TEXT NOT NULL, puan INT DEFAULT 5, tarih DATETIME DEFAULT CURRENT_TIMESTAMP, 
           durum ENUM('Bekliyor', 'Onaylandı') DEFAULT 'Bekliyor', 
           FOREIGN KEY (musteri_id) REFERENCES Musteri(musteri_id) ON DELETE CASCADE)""",
        
        """CREATE TABLE Favori (favori_id INT AUTO_INCREMENT PRIMARY KEY, musteri_id INT NOT NULL, 
           arac_id INT NOT NULL, tarih DATETIME DEFAULT CURRENT_TIMESTAMP, 
           FOREIGN KEY (musteri_id) REFERENCES Musteri(musteri_id) ON DELETE CASCADE, 
           FOREIGN KEY (arac_id) REFERENCES Arac(arac_id) ON DELETE CASCADE, 
           UNIQUE(musteri_id, arac_id))""",
        
        """CREATE TABLE Bakim (bakim_id INT AUTO_INCREMENT PRIMARY KEY, arac_id INT NOT NULL, 
           bakim_nedeni TEXT NOT NULL, maliyet DECIMAL(10,2), giris_tarihi DATE NOT NULL, 
           cikis_tarihi DATE, durum ENUM('Devam Ediyor', 'Tamamlandı') DEFAULT 'Devam Ediyor', 
           FOREIGN KEY (arac_id) REFERENCES Arac(arac_id))"""
    ]
    
    for table_sql in tables:
        cursor.execute(table_sql)
    print("✅ Tüm tablolar başarıyla oluşturuldu.")

def seed_data(cursor, conn):
    # 1. TEMEL VERİLER
    for s in SEHIRLER:
        cursor.execute("INSERT INTO Sehir (sehir_ad) VALUES (%s)", (s,))
    
    for k in KATEGORILER:
        cursor.execute("INSERT INTO Kategori (kategori_ad) VALUES (%s)", (k,))
        
    for e in EKSTRA_HIZMETLER:
        cursor.execute("INSERT INTO EkstraHizmet (ad, gunluk_ucret, ikon) VALUES (%s, %s, %s)", e)
        
    for k in KAMPANYALAR:
        cursor.execute("INSERT INTO Kampanya (kod, indirim_orani, son_kullanma_tarihi) VALUES (%s, %s, %s)", k)
        
    # 2. PERSONEL VE MÜŞTERİLER
    pw_hash = generate_password_hash("1234")
    cursor.execute("INSERT INTO Personel (ad, soyad, gorev, eposta, sifre) VALUES (%s,%s,%s,%s,%s)", 
                   ("Ahmet", "Yılmaz", "Yönetici", "admin@rentacar.com", pw_hash))
    
    musteri_ids = []
    for i in range(N_MUSTERI):
        ad = random.choice(ISIMLER)
        soyad = random.choice(SOYISIMLER)
        email = f"{ad.lower()}.{soyad.lower()}{i}@mail.com"
        tel = f"05{random.randint(300,599)}{random.randint(1000000,9999999)}"
        cursor.execute("INSERT INTO Musteri (ad, soyad, eposta, sifre, telefon, ehliyet_no, adres, dogum_tarihi) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                       (ad, soyad, email, pw_hash, tel, f"E-{random.randint(10000,99999)}", "İstanbul/Merkez", "1995-01-01"))
        musteri_ids.append(cursor.lastrowid)

    # 3. SİGORTALAR
    sigorta_ids = []
    for i in range(100):
        sirket = random.choice(SIGORTA_SIRKETLERI)
        police = f"POL-{random.randint(100000,999999)}"
        cursor.execute("INSERT INTO Sigorta (sigorta_sirketi, baslangic_tarihi, bitis_tarihi, police_no) VALUES (%s, %s, %s, %s)",
                       (sirket, "2025-01-01", "2026-01-01", police))
        sigorta_ids.append(cursor.lastrowid)

    # 4. ARAÇLAR (Detaylı Marka/Model/Resim)
    arac_ids = []
    generated_plates = set()
    
    for i in range(N_ARAC):
        marka = random.choice(list(ARAC_HAVUZU.keys()))
        model, resim = random.choice(ARAC_HAVUZU[marka])
        
        while True:
            plaka = f"{random.choice(['34','06','35','07','16'])}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.randint(100,999)}"
            if plaka not in generated_plates:
                generated_plates.add(plaka)
                break
        
        kategori_id = random.randint(1, len(KATEGORILER))
        sigorta_id = random.choice(sigorta_ids)
        sehir_id = random.randint(1, len(SEHIRLER))
        
        if kategori_id == 4: ucret = random.randint(3000, 6000) # Lüks
        elif kategori_id == 3: ucret = random.randint(2000, 3500) # SUV
        else: ucret = random.randint(800, 1800)
        
        durum = 'Müsait'
        
        cursor.execute("""INSERT INTO Arac (plaka, marka, model, yil, yakit_turu, vites_turu, kilometre, gunluk_ucret, resim_url, durum, kategori_id, sigorta_id, bulundugu_sehir_id) 
                          VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                       (plaka, marka, model, random.randint(2021, 2025), 
                        random.choice(['Dizel', 'Benzin', 'Hibrit']), 
                        random.choice(['Otomatik', 'Manuel']), 
                        random.randint(0, 80000), ucret, resim, durum, kategori_id, sigorta_id, sehir_id))
        arac_ids.append(cursor.lastrowid)

    # 5. BAKIM (%15 Araç Bakımda Olsun)
    bakimdaki_araclar = random.sample(arac_ids, k=int(N_ARAC * 0.15))
    for aid in bakimdaki_araclar:
        maliyet = random.randint(1000, 15000)
        neden = random.choice(['Periyodik Bakım', 'Lastik Değişimi', 'Motor Arızası', 'Fren Sistemi'])
        tarih = date.today() - timedelta(days=random.randint(1, 30))
        
        cursor.execute("INSERT INTO Bakim (arac_id, bakim_nedeni, maliyet, giris_tarihi) VALUES (%s,%s,%s,%s)", 
                       (aid, neden, maliyet, tarih))
        cursor.execute("UPDATE Arac SET durum='Bakımda' WHERE arac_id=%s", (aid,))

    # 6. REZERVASYONLAR
    for i in range(N_REZERVASYON):
        mid = random.choice(musteri_ids)
        aid = random.choice(arac_ids)
        
        if aid in bakimdaki_araclar: continue 
        
        gun = random.randint(1, 10)
        if random.random() < 0.7:
            baslangic = date.today() - timedelta(days=random.randint(10, 300))
            durum = 'Tamamlandı'
        else:
            baslangic = date.today() + timedelta(days=random.randint(1, 60))
            durum = 'Onaylandı'
            
        bitis = baslangic + timedelta(days=gun)
        
        cursor.execute("SELECT gunluk_ucret FROM Arac WHERE arac_id=%s", (aid,))
        ucret = cursor.fetchone()['gunluk_ucret']
        toplam = float(ucret) * gun
        
        cursor.execute("""INSERT INTO Rezervasyon (musteri_id, arac_id, baslangic_tarihi, bitis_tarihi, alis_saati, teslim_saati, toplam_ucret, durum) 
                          VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""", 
                       (mid, aid, baslangic, bitis, "09:00", "09:00", toplam, durum))
        rez_id = cursor.lastrowid
        
        if durum == 'Tamamlandı' or durum == 'Onaylandı':
            cursor.execute("INSERT INTO Odeme (rezervasyon_id, odeme_tutari, kart_sahibi, kart_no_son4) VALUES (%s,%s,%s,%s)",
                           (rez_id, toplam, "Test User", "1234"))
            
            if durum == 'Tamamlandı' and random.random() > 0.5:
                yorum, puan = random.choice(YORUMLAR)
                cursor.execute("INSERT INTO Yorum (musteri_id, yorum_metni, puan, durum) VALUES (%s,%s,%s,'Onaylandı')",
                               (mid, yorum, puan))

    conn.commit()
    print(f"🚀 SEED TAMAMLANDI! \n- {N_ARAC} Araç \n- {N_MUSTERI} Müşteri \n- {len(bakimdaki_araclar)} Bakımda Araç \n- {N_REZERVASYON} Rezervasyon eklendi.")

def main():
    # 1. Veritabanını Sıfırla (MySQL'e direkt bağlanıp)
    conn_raw = mysql.connector.connect(user=DB_CONFIG['user'], password=DB_CONFIG['password'], host=DB_CONFIG['host'])
    create_database(conn_raw.cursor())
    conn_raw.close()
    
    # 2. Veritabanına Bağlan ve Tabloları Kur (Arac_Kiralama veritabanına bağlanır)
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    create_tables(cursor)
    seed_data(cursor, conn)
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()