import mysql.connector
from werkzeug.security import generate_password_hash

config = {
    'user': 'root',
    'password': '1234', 
    'host': 'localhost',
}

sql_commands = """
DROP DATABASE IF EXISTS arac_kiralama;
CREATE DATABASE arac_kiralama CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE arac_kiralama;

CREATE TABLE Sehir (
    sehir_id INT AUTO_INCREMENT PRIMARY KEY,
    sehir_ad VARCHAR(50) NOT NULL
);
INSERT INTO Sehir (sehir_ad) VALUES ('İstanbul'), ('Ankara'), ('İzmir'), ('Konya'), ('Antalya'), ('Bursa'), ('Adana');

CREATE TABLE Kategori (
    kategori_id INT AUTO_INCREMENT PRIMARY KEY,
    kategori_ad VARCHAR(50) NOT NULL
);
INSERT INTO Kategori (kategori_ad) VALUES ('Ekonomik'), ('Orta Sınıf'), ('SUV'), ('Lüks'), ('Minivan');

CREATE TABLE EkstraHizmet (
    ekstra_id INT AUTO_INCREMENT PRIMARY KEY,
    ad VARCHAR(50) NOT NULL,
    gunluk_ucret DECIMAL(10,2) NOT NULL,
    ikon VARCHAR(50) DEFAULT 'fas fa-plus'
);
INSERT INTO EkstraHizmet (ad, gunluk_ucret, ikon) VALUES 
('Bebek Koltuğu', 50.00, 'fas fa-baby-carriage'),
('Navigasyon (GPS)', 30.00, 'fas fa-map-marked-alt'),
('Ek Sürücü', 100.00, 'fas fa-user-plus'),
('Kış Lastiği', 75.00, 'fas fa-snowflake'),
('Full Kasko Güvencesi', 200.00, 'fas fa-shield-alt');

CREATE TABLE Sigorta (
    sigorta_id INT AUTO_INCREMENT PRIMARY KEY,
    sigorta_sirketi VARCHAR(50) NOT NULL,
    baslangic_tarihi DATE NOT NULL,
    bitis_tarihi DATE NOT NULL,
    police_no VARCHAR(50) UNIQUE
);
INSERT INTO Sigorta (sigorta_sirketi, baslangic_tarihi, bitis_tarihi, police_no) VALUES
('Allianz', '2025-01-01', '2026-01-01', 'POL-001'),
('AXA', '2025-01-01', '2026-01-01', 'POL-002'),
('Anadolu', '2025-01-01', '2026-01-01', 'POL-003'),
('Mapfre', '2025-01-01', '2026-01-01', 'POL-004'),
('Sompo', '2025-01-01', '2026-01-01', 'POL-005');

CREATE TABLE Personel (
    personel_id INT AUTO_INCREMENT PRIMARY KEY,
    ad VARCHAR(50) NOT NULL,
    soyad VARCHAR(50) NOT NULL,
    gorev ENUM('Yönetici','Satış Temsilcisi') NOT NULL,
    eposta VARCHAR(100) UNIQUE NOT NULL,
    sifre VARCHAR(255) NOT NULL
);

CREATE TABLE Musteri (
    musteri_id INT AUTO_INCREMENT PRIMARY KEY,
    ad VARCHAR(50) NOT NULL,
    soyad VARCHAR(50) NOT NULL,
    eposta VARCHAR(100) UNIQUE NOT NULL,
    sifre VARCHAR(255) NOT NULL,
    telefon VARCHAR(15),
    ehliyet_no VARCHAR(20),
    adres TEXT,
    ProfilResim VARCHAR(255) DEFAULT 'default_user.png',
    dogum_tarihi DATE
);

CREATE TABLE Arac (
    arac_id INT AUTO_INCREMENT PRIMARY KEY,
    plaka VARCHAR(15) UNIQUE NOT NULL,
    marka VARCHAR(30) NOT NULL,
    model VARCHAR(30) NOT NULL,
    yil INT,
    yakit_turu ENUM('Benzin', 'Dizel', 'Elektrik', 'Hibrit') NOT NULL,
    vites_turu ENUM('Manuel', 'Otomatik') NOT NULL,
    kilometre INT DEFAULT 0,
    gunluk_ucret DECIMAL(10,2),
    resim_url VARCHAR(255) DEFAULT 'default_car.jpg',
    durum ENUM('Müsait','Kirada','Bakımda') DEFAULT 'Müsait',
    kategori_id INT,
    sigorta_id INT,
    bulundugu_sehir_id INT,
    FOREIGN KEY (kategori_id) REFERENCES Kategori(kategori_id),
    FOREIGN KEY (sigorta_id) REFERENCES Sigorta(sigorta_id),
    FOREIGN KEY (bulundugu_sehir_id) REFERENCES Sehir(sehir_id)
);

INSERT INTO Arac (plaka, marka, model, yil, yakit_turu, vites_turu, gunluk_ucret, resim_url, kategori_id, sigorta_id, bulundugu_sehir_id) VALUES
('34VA101', 'Fiat', 'Egea', 2023, 'Dizel', 'Manuel', 800.00, 'egea.jpg', 1, 1, 1),
('34VA102', 'Renault', 'Clio', 2024, 'Benzin', 'Otomatik', 950.00, 'clio.jpg', 1, 2, 1),
('34VA103', 'Peugeot', '3008', 2023, 'Dizel', 'Otomatik', 1800.00, 'peugeot3008.jpg', 3, 3, 1),
('34VA104', 'BMW', '520i', 2024, 'Benzin', 'Otomatik', 4500.00, 'bmw520.jpg', 4, 4, 1),
('34VA105', 'Mercedes', 'Vito', 2022, 'Dizel', 'Otomatik', 2500.00, 'vito.jpg', 5, 5, 1),
('06AN001', 'Volkswagen', 'Passat', 2023, 'Dizel', 'Otomatik', 2000.00, 'passat.jpg', 4, 1, 2),
('06AN002', 'Toyota', 'Corolla', 2022, 'Hibrit', 'Otomatik', 1200.00, 'corolla.jpg', 2, 2, 2),
('06AN003', 'Ford', 'Focus', 2023, 'Benzin', 'Manuel', 1100.00, 'focus.jpg', 2, 3, 2),
('06AN004', 'Dacia', 'Duster', 2024, 'Dizel', 'Manuel', 1300.00, 'duster.jpg', 3, 4, 2),
('35IZ001', 'Opel', 'Corsa', 2023, 'Benzin', 'Otomatik', 900.00, 'corsa.jpg', 1, 5, 3),
('35IZ002', 'Nissan', 'Qashqai', 2023, 'Benzin', 'Otomatik', 1600.00, 'qashqai.jpg', 3, 1, 3),
('35IZ003', 'Citroen', 'C3', 2024, 'Benzin', 'Manuel', 850.00, 'c3.jpg', 1, 2, 3),
('42KN001', 'Renault', 'Megane', 2022, 'Dizel', 'Otomatik', 1300.00, 'megane.jpg', 2, 3, 4),
('42KN002', 'Honda', 'Civic', 2023, 'Benzin', 'Otomatik', 1500.00, 'civic.jpg', 2, 4, 4),
('42KN003', 'Fiat', 'Egea Cross', 2024, 'Hibrit', 'Otomatik', 1100.00, 'egeacross.jpg', 3, 5, 4),
('07ANT01', 'Jeep', 'Renegade', 2023, 'Hibrit', 'Otomatik', 1900.00, 'renegade.jpg', 3, 1, 5),
('07ANT02', 'Audi', 'A3', 2023, 'Benzin', 'Otomatik', 2200.00, 'a3.jpg', 4, 2, 5),
('07ANT03', 'Hyundai', 'i20', 2024, 'Benzin', 'Otomatik', 950.00, 'i20.jpg', 1, 3, 5);

CREATE TABLE Rezervasyon (
    rezervasyon_id INT AUTO_INCREMENT PRIMARY KEY,
    musteri_id INT NOT NULL,
    arac_id INT NOT NULL,
    baslangic_tarihi DATE NOT NULL,
    bitis_tarihi DATE NOT NULL,
    alis_saati VARCHAR(5),
    teslim_saati VARCHAR(5),
    toplam_ucret DECIMAL(10,2),
    indirim_kodu VARCHAR(20),
    durum ENUM('Onaylandı','Bekliyor','İptal','Tamamlandı') DEFAULT 'Bekliyor',
    FOREIGN KEY (musteri_id) REFERENCES Musteri(musteri_id),
    FOREIGN KEY (arac_id) REFERENCES Arac(arac_id)
);

CREATE TABLE Kampanya (
    kampanya_id INT AUTO_INCREMENT PRIMARY KEY,
    kod VARCHAR(20) UNIQUE NOT NULL,
    indirim_orani INT NOT NULL,
    son_kullanma_tarihi DATE NOT NULL,
    aktif BOOLEAN DEFAULT TRUE
);
INSERT INTO Kampanya (kod, indirim_orani, son_kullanma_tarihi) VALUES 
('YAZ2025', 15, '2025-09-01'),
('HOSGELDIN', 10, '2030-12-31'),
('VIP20', 20, '2025-12-31');

CREATE TABLE RezervasyonEkstra (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rezervasyon_id INT NOT NULL,
    ekstra_id INT NOT NULL,
    FOREIGN KEY (rezervasyon_id) REFERENCES Rezervasyon(rezervasyon_id) ON DELETE CASCADE,
    FOREIGN KEY (ekstra_id) REFERENCES EkstraHizmet(ekstra_id)
);

CREATE TABLE Odeme (
    odeme_id INT AUTO_INCREMENT PRIMARY KEY,
    rezervasyon_id INT NOT NULL,
    odeme_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
    odeme_tutari DECIMAL(10,2),
    kart_sahibi VARCHAR(100),
    kart_no_son4 VARCHAR(4),
    odeme_turu ENUM('Kredi Kartı','Havale') DEFAULT 'Kredi Kartı',
    FOREIGN KEY (rezervasyon_id) REFERENCES Rezervasyon(rezervasyon_id)
);

CREATE TABLE Yorum (
    yorum_id INT AUTO_INCREMENT PRIMARY KEY,
    musteri_id INT NOT NULL,
    yorum_metni TEXT NOT NULL,
    puan INT DEFAULT 5,
    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
    durum ENUM('Bekliyor', 'Onaylandı') DEFAULT 'Bekliyor',
    FOREIGN KEY (musteri_id) REFERENCES Musteri(musteri_id) ON DELETE CASCADE
);

CREATE TABLE Favori (
    favori_id INT AUTO_INCREMENT PRIMARY KEY,
    musteri_id INT NOT NULL,
    arac_id INT NOT NULL,
    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (musteri_id) REFERENCES Musteri(musteri_id) ON DELETE CASCADE,
    FOREIGN KEY (arac_id) REFERENCES Arac(arac_id) ON DELETE CASCADE,
    UNIQUE(musteri_id, arac_id) 
);

/* --- YENİ: BAKIM TABLOSU --- */
CREATE TABLE Bakim (
    bakim_id INT AUTO_INCREMENT PRIMARY KEY,
    arac_id INT NOT NULL,
    bakim_nedeni TEXT NOT NULL,
    maliyet DECIMAL(10,2),
    giris_tarihi DATE NOT NULL,
    cikis_tarihi DATE,
    durum ENUM('Devam Ediyor', 'Tamamlandı') DEFAULT 'Devam Ediyor',
    FOREIGN KEY (arac_id) REFERENCES Arac(arac_id)
);
"""

try:
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    print("⏳ Veritabanı sıfırlanıyor...")
    for command in sql_commands.split(';'):
        if command.strip():
            cursor.execute(command)
    print("✅ Tablolar başarıyla oluşturuldu.")
    
    sifre_admin = generate_password_hash("1234") 
    sql_admin = "INSERT INTO Personel (ad, soyad, gorev, eposta, sifre) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(sql_admin, ('Ahmet', 'Yılmaz', 'Yönetici', 'admin@rentacar.com', sifre_admin))
    print("✅ Yönetici eklendi.")

    sifre_musteri = generate_password_hash("1234")
    sql_musteri = """INSERT INTO Musteri (ad, soyad, eposta, telefon, sifre, adres, ehliyet_no, dogum_tarihi, ProfilResim) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'default_user.png')"""
    cursor.execute(sql_musteri, ('Mehmet', 'Kaya', 'mehmet@gmail.com', '05551234567', sifre_musteri, 'Ankara', 'E-12345', '1995-01-01'))
    print("✅ Örnek Müşteri eklendi.")

    sql_yorum = "INSERT INTO Yorum (musteri_id, yorum_metni, puan, durum) VALUES (1, 'Hizmetten çok memnun kaldım.', 5, 'Onaylandı')"
    cursor.execute(sql_yorum)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("🚀 İŞLEM TAMAM! db_reset.py çalıştı.")
except mysql.connector.Error as err:
    print(f"❌ HATA: {err}")