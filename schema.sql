/* ==========================================================
   RENT-A-CAR | FULL SCHEMA + AUTO SEED + AUTO STATUS + ERD
   MySQL 8+
   ========================================================== */

DROP DATABASE IF EXISTS arac_kiralama;
CREATE DATABASE arac_kiralama CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE arac_kiralama;

SET NAMES utf8mb4 COLLATE utf8mb4_0900_ai_ci;
SET sql_safe_updates = 0;
SET time_zone = '+03:00';

-- ==========================================================
-- 1) TABLOLAR
-- ==========================================================

CREATE TABLE Sehir (
    sehir_id INT AUTO_INCREMENT PRIMARY KEY,
    sehir_ad VARCHAR(50) NOT NULL
);

CREATE TABLE Kategori (
    kategori_id INT AUTO_INCREMENT PRIMARY KEY,
    kategori_ad VARCHAR(50) NOT NULL
);

CREATE TABLE EkstraHizmet (
    ekstra_id INT AUTO_INCREMENT PRIMARY KEY,
    ad VARCHAR(50) NOT NULL,
    gunluk_ucret DECIMAL(10,2) NOT NULL,
    ikon VARCHAR(50) DEFAULT 'fas fa-plus'
);

CREATE TABLE Sigorta (
    sigorta_id INT AUTO_INCREMENT PRIMARY KEY,
    sigorta_sirketi VARCHAR(50) NOT NULL,
    baslangic_tarihi DATE NOT NULL,
    bitis_tarihi DATE NOT NULL,
    police_no VARCHAR(50) UNIQUE
);

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

CREATE TABLE Kampanya (
    kampanya_id INT AUTO_INCREMENT PRIMARY KEY,
    kod VARCHAR(20) UNIQUE NOT NULL,
    indirim_orani INT NOT NULL,
    son_kullanma_tarihi DATE NOT NULL,
    aktif BOOLEAN DEFAULT TRUE
);

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
    durum ENUM('Onaylandı','Bekliyor','İptal','Tamamlandı','Kirada') DEFAULT 'Bekliyor',
    FOREIGN KEY (musteri_id) REFERENCES Musteri(musteri_id),
    FOREIGN KEY (arac_id) REFERENCES Arac(arac_id)
);

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

-- ==========================================================
-- 2) STATİK VERİLER (20 şehir / 6 kategori / 15 ekstra / 5 kampanya)
-- ==========================================================

INSERT INTO Sehir (sehir_ad) VALUES
('İstanbul'), ('Ankara'), ('İzmir'), ('Konya'), ('Antalya'),
('Bursa'), ('Adana'), ('Gaziantep'), ('Kayseri'), ('Eskişehir'),
('Mersin'), ('Samsun'), ('Trabzon'), ('Denizli'), ('Diyarbakır'),
('Şanlıurfa'), ('Malatya'), ('Aydın'), ('Muğla'), ('Tekirdağ');

INSERT INTO Kategori (kategori_ad) VALUES
('Ekonomik'), ('Orta Sınıf'), ('SUV'), ('Lüks'), ('Minivan'), ('Elektrikli');

INSERT INTO EkstraHizmet (ad, gunluk_ucret, ikon) VALUES
('Bebek Koltuğu', 50.00, 'fas fa-baby-carriage'),
('Navigasyon (GPS)', 30.00, 'fas fa-map-marked-alt'),
('Ek Sürücü', 100.00, 'fas fa-user-plus'),
('Kış Lastiği', 75.00, 'fas fa-snowflake'),
('Full Kasko Güvencesi', 200.00, 'fas fa-shield-alt'),
('HGS/OGS Paketi', 40.00, 'fas fa-road'),
('Wi-Fi Hotspot', 60.00, 'fas fa-wifi'),
('Premium Temizlik', 80.00, 'fas fa-broom'),
('Araç İçi Kamera', 90.00, 'fas fa-video'),
('Ek Bagaj', 70.00, 'fas fa-suitcase'),
('Şoförlü Teslimat', 250.00, 'fas fa-user-tie'),
('Havaalanı Teslim', 150.00, 'fas fa-plane'),
('Sınırsız Km', 180.00, 'fas fa-infinity'),
('Cam-Far Sigortası', 110.00, 'fas fa-car-crash'),
('Lastik Sigortası', 95.00, 'fas fa-life-ring');

INSERT INTO Kampanya (kod, indirim_orani, son_kullanma_tarihi) VALUES
('YAZ2025', 15, '2025-09-01'),
('HOSGELDIN', 10, '2030-12-31'),
('VIP20', 20, '2025-12-31'),
('KIS2025', 12, '2026-03-31'),
('WEEKEND', 8, '2026-12-31');

-- 50 sigorta (basit seri)
INSERT INTO Sigorta (sigorta_sirketi, baslangic_tarihi, bitis_tarihi, police_no)
SELECT
  ELT(1+FLOOR(RAND()*10), 'Allianz','AXA','Anadolu','Mapfre','Sompo','Aksigorta','HDI','Zurich','Generali','Doga') as sirket,
  DATE_ADD('2025-01-01', INTERVAL FLOOR(RAND()*365) DAY) as bas,
  DATE_ADD(DATE_ADD('2025-01-01', INTERVAL FLOOR(RAND()*365) DAY), INTERVAL 365 DAY) as bit,
  CONCAT('POL-', LPAD(n, 4, '0')) as police
FROM (
  SELECT 1000 AS n UNION ALL SELECT 1001 UNION ALL SELECT 1002 UNION ALL SELECT 1003 UNION ALL SELECT 1004
  UNION ALL SELECT 1005 UNION ALL SELECT 1006 UNION ALL SELECT 1007 UNION ALL SELECT 1008 UNION ALL SELECT 1009
  UNION ALL SELECT 1010 UNION ALL SELECT 1011 UNION ALL SELECT 1012 UNION ALL SELECT 1013 UNION ALL SELECT 1014
  UNION ALL SELECT 1015 UNION ALL SELECT 1016 UNION ALL SELECT 1017 UNION ALL SELECT 1018 UNION ALL SELECT 1019
  UNION ALL SELECT 1020 UNION ALL SELECT 1021 UNION ALL SELECT 1022 UNION ALL SELECT 1023 UNION ALL SELECT 1024
  UNION ALL SELECT 1025 UNION ALL SELECT 1026 UNION ALL SELECT 1027 UNION ALL SELECT 1028 UNION ALL SELECT 1029
  UNION ALL SELECT 1030 UNION ALL SELECT 1031 UNION ALL SELECT 1032 UNION ALL SELECT 1033 UNION ALL SELECT 1034
  UNION ALL SELECT 1035 UNION ALL SELECT 1036 UNION ALL SELECT 1037 UNION ALL SELECT 1038 UNION ALL SELECT 1039
  UNION ALL SELECT 1040 UNION ALL SELECT 1041 UNION ALL SELECT 1042 UNION ALL SELECT 1043 UNION ALL SELECT 1044
  UNION ALL SELECT 1045 UNION ALL SELECT 1046 UNION ALL SELECT 1047 UNION ALL SELECT 1048 UNION ALL SELECT 1049
) t;

-- ==========================================================
-- 3) YARDIMCI: Resim dosyaları (senin static/img ile birebir)
-- ==========================================================
-- Arac.resim_url alanına bu dosya adları yazılacak:
-- a3.jpg, bmw520.jpg, c3.jpg, civic.jpg, clio.jpg, corolla.jpg, corsa.jpg,
-- default_car.jpg, duster.jpg, egea.jpg, egeacross.jpg, focus.jpg, i20.jpg,
-- megane.jpg, passat.jpg, peugeot3008.jpg, qashqai.jpg, renegade.jpg, vito.jpg

-- ==========================================================
-- 4) STORED PROCEDURE: Fake ama gerçekçi seed
-- ==========================================================
DELIMITER $$

CREATE PROCEDURE sp_seed_all(
  IN p_arac INT,
  IN p_musteri INT,
  IN p_rez INT
)
BEGIN
  DECLARE i INT DEFAULT 0;

  -- 4.1 Admin
  IF (SELECT COUNT(*) FROM Personel) = 0 THEN
    INSERT INTO Personel (ad, soyad, gorev, eposta, sifre)
    VALUES ('Ahmet','Yılmaz','Yönetici','admin@rentacar.com',
      'pbkdf2:sha256:260000$demo$3a0b0d6b2e6f4c1b3a0b0d6b2e6f4c1b3a0b0d6b2e6f4c1b3a0b0d6b2e6f4c1b');
  END IF;

  -- 4.2 Müşteriler
  SET i = 0;
  WHILE i < p_musteri DO
    SET @ad = ELT(1+FLOOR(RAND()*20),
      'Ahmet','Mehmet','Ayse','Fatma','Ali','Zeynep','Can','Elif','Mert','Ece',
      'Deniz','Emre','Seda','Burak','Cem','Naz','Irem','Hakan','Selin','Oguz'
    );
    SET @soyad = ELT(1+FLOOR(RAND()*20),
      'Yilmaz','Kaya','Demir','Sahin','Celik','Yildiz','Aydin','Koc','Arslan','Dogan',
      'Ozturk','Kara','Aslan','Polat','Aksoy','Gunes','Kilic','Tas','Erdem','Bulut'
    );
    SET @email = CONCAT(LOWER(@ad),'.',LOWER(@soyad),LPAD(i+1,4,'0'),'@mail.com');
    SET @tel = CONCAT('05', LPAD(FLOOR(RAND()*1000000000),9,'0'));
    SET @eh = CONCAT('E-', LPAD(FLOOR(RAND()*99999),5,'0'));
    SET @dog = DATE_ADD('1975-01-01', INTERVAL FLOOR(RAND()*12000) DAY);
    SET @adr = CONCAT(
      (SELECT sehir_ad FROM Sehir ORDER BY RAND() LIMIT 1),
      ' / ',
      ELT(1+FLOOR(RAND()*6),'Merkez','Cankaya','Kadikoy','Konak','Nilufer','Kepez')
    );

    IF (SELECT COUNT(*) FROM Musteri WHERE eposta=@email) = 0 THEN
      INSERT INTO Musteri(ad,soyad,eposta,sifre,telefon,ehliyet_no,adres,dogum_tarihi,ProfilResim)
      VALUES(@ad,@soyad,@email,
        'pbkdf2:sha256:260000$demo$3a0b0d6b2e6f4c1b3a0b0d6b2e6f4c1b3a0b0d6b2e6f4c1b3a0b0d6b2e6f4c1b',
        @tel,@eh,@adr,@dog,'default_user.png');
    END IF;

    SET i = i + 1;
  END WHILE;

  -- 4.3 Araçlar
  SET i = 0;
  WHILE i < p_arac DO
    SET @sehir_kod = ELT(1+FLOOR(RAND()*10),'34','06','35','07','16','01','42','27','38','55');
    SET @L1 = SUBSTRING('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 1+FLOOR(RAND()*26), 1);
    SET @L2 = SUBSTRING('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 1+FLOOR(RAND()*26), 1);
    SET @L3 = SUBSTRING('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 1+FLOOR(RAND()*26), 1);
    SET @N1 = LPAD(FLOOR(RAND()*1000),3,'0');
    SET @plaka = CONCAT(@sehir_kod,@L1,@L2,@L3,@N1);

    SET @marka = ELT(1+FLOOR(RAND()*12),
      'Fiat','Renault','Toyota','Volkswagen','Ford','Hyundai','Peugeot','BMW','Mercedes','Audi','Honda','Nissan'
    );

    SET @model = CASE @marka
      WHEN 'Fiat' THEN ELT(1+FLOOR(RAND()*2),'Egea','Egea Cross')
      WHEN 'Renault' THEN ELT(1+FLOOR(RAND()*2),'Clio','Megane')
      WHEN 'Toyota' THEN 'Corolla'
      WHEN 'Volkswagen' THEN 'Passat'
      WHEN 'Ford' THEN 'Focus'
      WHEN 'Hyundai' THEN 'i20'
      WHEN 'Peugeot' THEN '3008'
      WHEN 'BMW' THEN '520i'
      WHEN 'Mercedes' THEN 'Vito'
      WHEN 'Audi' THEN 'A3'
      WHEN 'Honda' THEN 'Civic'
      WHEN 'Nissan' THEN 'Qashqai'
      ELSE 'Egea'
    END;

    SET @resim = CASE @model
      WHEN 'A3' THEN 'a3.jpg'
      WHEN '520i' THEN 'bmw520.jpg'
      WHEN 'C3' THEN 'c3.jpg'
      WHEN 'Civic' THEN 'civic.jpg'
      WHEN 'Clio' THEN 'clio.jpg'
      WHEN 'Corolla' THEN 'corolla.jpg'
      WHEN 'Corsa' THEN 'corsa.jpg'
      WHEN 'Duster' THEN 'duster.jpg'
      WHEN 'Egea' THEN 'egea.jpg'
      WHEN 'Egea Cross' THEN 'egeacross.jpg'
      WHEN 'Focus' THEN 'focus.jpg'
      WHEN 'i20' THEN 'i20.jpg'
      WHEN 'Megane' THEN 'megane.jpg'
      WHEN 'Passat' THEN 'passat.jpg'
      WHEN '3008' THEN 'peugeot3008.jpg'
      WHEN 'Qashqai' THEN 'qashqai.jpg'
      WHEN 'Renegade' THEN 'renegade.jpg'
      WHEN 'Vito' THEN 'vito.jpg'
      ELSE 'default_car.jpg'
    END;

    SET @yakit = ELT(1+FLOOR(RAND()*4),'Benzin','Dizel','Elektrik','Hibrit');
    SET @vites = ELT(1+FLOOR(RAND()*2),'Manuel','Otomatik');
    SET @yil = 2019 + FLOOR(RAND()*7);
    SET @km = FLOOR(RAND()*180000);

    SET @kategori_id = 1 + FLOOR(RAND()*6);
    SET @sigorta_id = (SELECT sigorta_id FROM Sigorta ORDER BY RAND() LIMIT 1);
    SET @bulundugu_sehir_id = 1 + FLOOR(RAND()*20);

    SET @ucret = CASE @kategori_id
      WHEN 1 THEN ROUND(750 + RAND()*400,2)
      WHEN 2 THEN ROUND(1000 + RAND()*600,2)
      WHEN 3 THEN ROUND(1400 + RAND()*1200,2)
      WHEN 4 THEN ROUND(2200 + RAND()*3300,2)
      WHEN 5 THEN ROUND(1600 + RAND()*1600,2)
      WHEN 6 THEN ROUND(1800 + RAND()*2400,2)
      ELSE ROUND(1000 + RAND()*1000,2)
    END;

    IF (SELECT COUNT(*) FROM Arac WHERE plaka=@plaka) = 0 THEN
      INSERT INTO Arac(plaka,marka,model,yil,yakit_turu,vites_turu,kilometre,gunluk_ucret,resim_url,durum,kategori_id,sigorta_id,bulundugu_sehir_id)
      VALUES(@plaka,@marka,@model,@yil,@yakit,@vites,@km,@ucret,@resim,'Müsait',@kategori_id,@sigorta_id,@bulundugu_sehir_id);
      SET i = i + 1;
    END IF;
  END WHILE;

  -- 4.4 Bakım (%15 araç)  ✅ FIX: LIMIT değişken için dynamic SQL
  SET @bakim_sayi = FLOOR((SELECT COUNT(*) FROM Arac) * 0.15);

  SET @sql_bakim = CONCAT(
    "INSERT INTO Bakim(arac_id,bakim_nedeni,maliyet,giris_tarihi,durum) ",
    "SELECT arac_id, ",
    "ELT(1+FLOOR(RAND()*5),'Periyodik bakım','Fren bakımı','Yağ değişimi','Lastik değişimi','Kaporta onarımı'), ",
    "ROUND(500 + RAND()*15000,2), ",
    "DATE_SUB(CURDATE(), INTERVAL FLOOR(RAND()*60) DAY), ",
    "'Devam Ediyor' ",
    "FROM Arac ",
    "ORDER BY RAND() ",
    "LIMIT ", @bakim_sayi
  );

  PREPARE stmt_bakim FROM @sql_bakim;
  EXECUTE stmt_bakim;
  DEALLOCATE PREPARE stmt_bakim;

  UPDATE Arac
  SET durum='Bakımda'
  WHERE arac_id IN (SELECT arac_id FROM Bakim WHERE durum='Devam Ediyor');

  -- 4.5 Rezervasyon + Ödeme + Ekstralar
  SET i = 0;
  WHILE i < p_rez DO
    SET @musteri_id = (SELECT musteri_id FROM Musteri ORDER BY RAND() LIMIT 1);
    SET @arac_id = (SELECT arac_id FROM Arac WHERE durum != 'Bakımda' ORDER BY RAND() LIMIT 1);

    SET @start = DATE_ADD(CURDATE(), INTERVAL (FLOOR(RAND()*210) - 30) DAY);
    SET @days = 1 + FLOOR(RAND()*14);
    SET @end = DATE_ADD(@start, INTERVAL @days DAY);

    SET @alis = ELT(1+FLOOR(RAND()*7),'09:00','10:00','11:00','12:00','13:00','14:00','15:00');
    SET @teslim = ELT(1+FLOOR(RAND()*7),'09:00','10:00','11:00','12:00','13:00','14:00','15:00');

    SET @gunluk = (SELECT gunluk_ucret FROM Arac WHERE arac_id=@arac_id);
    SET @toplam = ROUND(@gunluk * @days, 2);

    SET @ind_kod = NULL;
    IF RAND() < 0.35 THEN
      SET @ind_kod = (
        SELECT kod
        FROM Kampanya
        WHERE aktif=1 AND son_kullanma_tarihi >= CURDATE()
        ORDER BY RAND()
        LIMIT 1
        );
      IF @ind_kod IS NOT NULL THEN
        SET @oran = (
            SELECT indirim_orani
            FROM Kampanya
            WHERE kod = CONVERT(@ind_kod USING utf8mb4) COLLATE utf8mb4_0900_ai_ci
            );
        SET @toplam = ROUND(@toplam * (1 - (@oran/100)), 2);
      END IF;
    END IF;

    SET @durum = ELT(1+FLOOR(RAND()*4),'Onaylandı','Bekliyor','İptal','Tamamlandı');

    INSERT INTO Rezervasyon(musteri_id,arac_id,baslangic_tarihi,bitis_tarihi,alis_saati,teslim_saati,toplam_ucret,indirim_kodu,durum)
    VALUES(@musteri_id,@arac_id,@start,@end,@alis,@teslim,@toplam,@ind_kod,@durum);

    SET @rez_id = LAST_INSERT_ID();

    IF @durum <> 'İptal' THEN
      SET @kart_sahibi = CONCAT(
        ELT(1+FLOOR(RAND()*20),'Ahmet','Mehmet','Ayse','Fatma','Ali','Zeynep','Can','Elif','Mert','Ece','Deniz','Emre','Seda','Burak','Cem','Naz','Irem','Hakan','Selin','Oguz'),
        ' ',
        ELT(1+FLOOR(RAND()*20),'Yilmaz','Kaya','Demir','Sahin','Celik','Yildiz','Aydin','Koc','Arslan','Dogan','Ozturk','Kara','Aslan','Polat','Aksoy','Gunes','Kilic','Tas','Erdem','Bulut')
      );
      SET @son4 = LPAD(FLOOR(RAND()*10000),4,'0');
      SET @tur = ELT(1+FLOOR(RAND()*2),'Kredi Kartı','Havale');
      INSERT INTO Odeme(rezervasyon_id,odeme_tutari,kart_sahibi,kart_no_son4,odeme_turu)
      VALUES(@rez_id,@toplam,@kart_sahibi,@son4,@tur);
    END IF;

    IF RAND() < 0.50 THEN
      SET @k = 1 + FLOOR(RAND()*3);

      SET @sql_ekstra = CONCAT(
        "INSERT INTO RezervasyonEkstra(rezervasyon_id, ekstra_id) ",
        "SELECT ", @rez_id, ", ekstra_id ",
        "FROM EkstraHizmet ",
        "ORDER BY RAND() ",
        "LIMIT ", @k
      );

      PREPARE stmt_ekstra FROM @sql_ekstra;
      EXECUTE stmt_ekstra;
      DEALLOCATE PREPARE stmt_ekstra;
    END IF;

    SET i = i + 1;
  END WHILE;



  SET @fav_limit = (SELECT COUNT(*) FROM Musteri) * 5;

  SET @sql_fav = CONCAT(
    "INSERT IGNORE INTO Favori(musteri_id, arac_id) ",
    "SELECT m.musteri_id, a.arac_id ",
    "FROM Musteri m ",
    "JOIN Arac a ",
    "ORDER BY RAND() ",
    "LIMIT ", @fav_limit
  );

  PREPARE stmt_fav FROM @sql_fav;
  EXECUTE stmt_fav;
  DEALLOCATE PREPARE stmt_fav;


  -- 4.7 Yorumlar
  SET @yorum_sayi = FLOOR((SELECT COUNT(*) FROM Rezervasyon) * 0.30);

  SET @sql_yorum = CONCAT(
    "INSERT INTO Yorum(musteri_id, yorum_metni, puan, durum) ",
    "SELECT r.musteri_id, ",
    "ELT(1+FLOOR(RAND()*6), ",
    "'Çok memnun kaldım, araç tertemizdi.', ",
    "'İletişim hızlıydı, tekrar kiralarım.', ",
    "'Fiyat/performans çok iyi.', ",
    "'Araç beklediğimden iyiydi.', ",
    "'Teslim alma süreci kolaydı.', ",
    "'Biraz gecikme oldu ama çözdüler.' ",
    "), ",
    "ELT(1+FLOOR(RAND()*3),3,4,5), ",
    "ELT(1+FLOOR(RAND()*2),'Bekliyor','Onaylandı') ",
    "FROM Rezervasyon r ",
    "ORDER BY RAND() ",
    "LIMIT ", @yorum_sayi
  );

  PREPARE stmt_yorum FROM @sql_yorum;
  EXECUTE stmt_yorum;
  DEALLOCATE PREPARE stmt_yorum;

END$$

-- ==========================================================
-- 5) ARAÇ DURUMU OTOMATİK GÜNCELLEME (BUGÜNE GÖRE)
-- ==========================================================
CREATE PROCEDURE sp_update_arac_durum()
BEGIN
  UPDATE Arac a
  JOIN Bakim b ON b.arac_id = a.arac_id
  SET a.durum = 'Bakımda'
  WHERE b.durum = 'Devam Ediyor';

  UPDATE Arac a
  SET a.durum = 'Kirada'
  WHERE a.durum <> 'Bakımda'
    AND EXISTS (
      SELECT 1
      FROM Rezervasyon r
      WHERE r.arac_id = a.arac_id
        AND r.durum IN ('Onaylandı','Bekliyor','Kirada')
        AND CURDATE() BETWEEN r.baslangic_tarihi AND r.bitis_tarihi
    );

  UPDATE Arac a
  SET a.durum = 'Müsait'
  WHERE a.durum <> 'Bakımda'
    AND NOT EXISTS (
      SELECT 1
      FROM Rezervasyon r
      WHERE r.arac_id = a.arac_id
        AND r.durum IN ('Onaylandı','Bekliyor','Kirada')
        AND CURDATE() BETWEEN r.baslangic_tarihi AND r.bitis_tarihi
    );
END$$

-- ==========================================================
-- 6) INFORMATION_SCHEMA -> MERMAID ERD ÜRETİMİ
-- ==========================================================
CREATE PROCEDURE sp_generate_mermaid_erd()
BEGIN
  SET SESSION group_concat_max_len = 1000000;

  SELECT CONCAT(
    'erDiagram\n',
    IFNULL((
      SELECT GROUP_CONCAT(
        CONCAT(
          UPPER(kcu.REFERENCED_TABLE_NAME),
          ' ||--o{ ',
          UPPER(kcu.TABLE_NAME),
          ' : ',
          kcu.CONSTRAINT_NAME
        )
        SEPARATOR '\n'
      )
      FROM information_schema.KEY_COLUMN_USAGE kcu
      WHERE kcu.TABLE_SCHEMA = DATABASE()
        AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
    ), ''),
    '\n'
  ) AS mermaid_erd;
END$$

DELIMITER ;

-- ==========================================================
-- 7) EVENT SCHEDULER (günde 1 kez araç durumu güncelle)
-- ==========================================================
-- Not: event_scheduler kapalıysa:
-- SET GLOBAL event_scheduler = ON;

DROP EVENT IF EXISTS ev_update_arac_durum;
CREATE EVENT ev_update_arac_durum
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP + INTERVAL 5 MINUTE
DO
  CALL sp_update_arac_durum();

-- ==========================================================
-- 8) OTOMATİK SEED
-- ==========================================================
CALL sp_seed_all(250, 100, 200);
CALL sp_update_arac_durum();

-- ERD'yi görmek için:
CALL sp_generate_mermaid_erd();
