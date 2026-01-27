import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

# Veritabanı Ayarları
db_config = {
    'user': 'root',
    'password': '1234',  # Şifreni kontrol et
    'host': 'localhost',
    'database': 'arac_kiralama',
    'raise_on_warnings': True
}

def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    # [KRİTİK DÜZELTME] GROUP BY hatasını çözen sihirli satır:
    cursor = conn.cursor()
    cursor.execute("SET SESSION sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));")
    cursor.close()
    return conn

# --- GENEL VERİ ÇEKME ---
def get_sehirler():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Sehir")
    result = cursor.fetchall()
    conn.close()
    return result

def get_kategoriler():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Kategori")
    result = cursor.fetchall()
    conn.close()
    return result

def get_ekstra_hizmetler():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM EkstraHizmet")
    result = cursor.fetchall()
    conn.close()
    return result

# --- ARAÇ İŞLEMLERİ ---
def get_tum_araclar(sehir_id=None, baslangic=None, bitis=None, vites=None, yakit=None, min_fiyat=0, max_fiyat=100000):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT a.*, s.sehir_ad 
        FROM Arac a
        JOIN Sehir s ON a.bulundugu_sehir_id = s.sehir_id
        WHERE a.durum != 'Bakımda'
        AND a.gunluk_ucret BETWEEN %s AND %s
    """
    params = [min_fiyat, max_fiyat]

    if sehir_id and sehir_id != "":
        query += " AND a.bulundugu_sehir_id = %s"
        params.append(sehir_id)
    
    if vites and vites != "":
        query += " AND a.vites_turu = %s"
        params.append(vites)

    if yakit and yakit != "":
        query += " AND a.yakit_turu = %s"
        params.append(yakit)
    
    if baslangic and bitis:
        query += """ 
            AND a.arac_id NOT IN (
                SELECT arac_id FROM Rezervasyon 
                WHERE durum IN ('Onaylandı', 'Bekliyor', 'Kirada')
                AND (baslangic_tarihi <= %s AND bitis_tarihi >= %s)
            )
        """
        params.append(bitis)
        params.append(baslangic)

    cursor.execute(query, tuple(params))
    araclar = cursor.fetchall()
    conn.close()
    return araclar

def get_arac_by_id(arac_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Arac WHERE arac_id = %s", (arac_id,))
    arac = cursor.fetchone()
    conn.close()
    return arac

def add_arac_ve_sigorta(arac_bilgi, sigorta_bilgi):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql_sigorta = "INSERT INTO Sigorta (sigorta_sirketi, baslangic_tarihi, bitis_tarihi, police_no) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql_sigorta, (sigorta_bilgi['sirket'], sigorta_bilgi['baslangic'], sigorta_bilgi['bitis'], sigorta_bilgi['police']))
        sigorta_id = cursor.lastrowid

        sql_arac = """INSERT INTO Arac (plaka, marka, model, yil, yakit_turu, vites_turu, gunluk_ucret, resim_url, kategori_id, bulundugu_sehir_id, sigorta_id, durum) 
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Müsait')"""
        val_arac = (arac_bilgi['plaka'], arac_bilgi['marka'], arac_bilgi['model'], arac_bilgi['yil'], 
                    arac_bilgi['yakit'], arac_bilgi['vites'], arac_bilgi['ucret'], arac_bilgi['resim'], 
                    arac_bilgi['kategori'], arac_bilgi['sehir'], sigorta_id)
        cursor.execute(sql_arac, val_arac)
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def teslim_al_arac(rezervasyon_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT arac_id FROM Rezervasyon WHERE rezervasyon_id = %s", (rezervasyon_id,))
        rez = cursor.fetchone()
        if rez:
            cursor.execute("UPDATE Arac SET durum = 'Müsait' WHERE arac_id = %s", (rez['arac_id'],))
            cursor.execute("UPDATE Rezervasyon SET durum = 'Tamamlandı' WHERE rezervasyon_id = %s", (rezervasyon_id,))
            conn.commit()
            return True
        return False
    finally: conn.close()

# --- GİRİŞ & MÜŞTERİ ---
def check_user_login(eposta, sifre):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Personel WHERE eposta = %s", (eposta,))
    admin = cursor.fetchone()
    if admin and check_password_hash(admin['sifre'], sifre):
        conn.close()
        return {'type': 'admin', 'data': admin}
    cursor.execute("SELECT * FROM Musteri WHERE eposta = %s", (eposta,))
    musteri = cursor.fetchone()
    if musteri and check_password_hash(musteri['sifre'], sifre):
        conn.close()
        return {'type': 'musteri', 'data': musteri}
    conn.close()
    return None

def check_email_exists(eposta):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Musteri WHERE eposta = %s", (eposta,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_password_by_email(eposta, yeni_sifre):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        hashed = generate_password_hash(yeni_sifre)
        cursor.execute("UPDATE Musteri SET sifre = %s WHERE eposta = %s", (hashed, eposta))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def register_musteri(bilgiler):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Musteri WHERE eposta = %s", (bilgiler['eposta'],))
    if cursor.fetchone(): conn.close(); return False
    
    hashed = generate_password_hash(bilgiler['sifre'])
    sql = """INSERT INTO Musteri (ad, soyad, eposta, telefon, sifre, adres, ehliyet_no, dogum_tarihi, ProfilResim) 
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'default_user.png')"""
    val = (bilgiler['ad'], bilgiler['soyad'], bilgiler['eposta'], bilgiler['telefon'], hashed, 
           bilgiler['adres'], bilgiler['ehliyet'], bilgiler['dogum'])
    cursor.execute(sql, val)
    conn.commit()
    conn.close()
    return True

def get_musteri_by_id(musteri_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Musteri WHERE musteri_id = %s", (musteri_id,))
    res = cursor.fetchone()
    conn.close()
    return res

def update_musteri_profil(mid, ad, soyad, tel, adr, resim=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if resim:
            cursor.execute("UPDATE Musteri SET ad=%s, soyad=%s, telefon=%s, adres=%s, ProfilResim=%s WHERE musteri_id=%s", (ad, soyad, tel, adr, resim, mid))
        else:
            cursor.execute("UPDATE Musteri SET ad=%s, soyad=%s, telefon=%s, adres=%s WHERE musteri_id=%s", (ad, soyad, tel, adr, mid))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def check_current_password(mid, sifre):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT sifre FROM Musteri WHERE musteri_id = %s", (mid,))
    user = cursor.fetchone()
    conn.close()
    return check_password_hash(user['sifre'], sifre) if user else False

def update_musteri_sifre(mid, yeni_hash):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Musteri SET sifre = %s WHERE musteri_id = %s", (yeni_hash, mid))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

# --- REZERVASYON ---
def add_rezervasyon(bilgi, odeme):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        ind_kod = bilgi.get('indirim_kodu', None)
        sql_rez = "INSERT INTO Rezervasyon (musteri_id, arac_id, baslangic_tarihi, bitis_tarihi, alis_saati, teslim_saati, toplam_ucret, indirim_kodu, durum) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'Onaylandı')"
        val_rez = (bilgi['musteri_id'], bilgi['arac_id'], bilgi['baslangic_tarihi'], bilgi['bitis_tarihi'], bilgi['alis_saati'], bilgi['teslim_saati'], bilgi['toplam_ucret'], ind_kod)
        cursor.execute(sql_rez, val_rez)
        rez_id = cursor.lastrowid

        if 'ekstralar' in bilgi and bilgi['ekstralar']:
            sql_eks = "INSERT INTO RezervasyonEkstra (rezervasyon_id, ekstra_id) VALUES (%s,%s)"
            for eid in bilgi['ekstralar']:
                cursor.execute(sql_eks, (rez_id, eid))
        
        sql_odm = "INSERT INTO Odeme (rezervasyon_id, odeme_tutari, kart_sahibi, kart_no_son4, odeme_turu) VALUES (%s,%s,%s,%s,%s)"
        val_odm = (rez_id, bilgi['toplam_ucret'], odeme['sahip'], odeme['no'][-4:], odeme['tur'])
        cursor.execute(sql_odm, val_odm)
        
        cursor.execute("UPDATE Arac SET durum='Kirada' WHERE arac_id=%s", (bilgi['arac_id'],))
        conn.commit()
        return True
    except Exception as e: print(e); conn.rollback(); return False
    finally: conn.close()

def get_musteri_rezervasyonlari(mid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT r.*, a.marka, a.model, a.resim_url,
               (SELECT GROUP_CONCAT(eh.ad SEPARATOR ', ') FROM RezervasyonEkstra re JOIN EkstraHizmet eh ON re.ekstra_id=eh.ekstra_id WHERE re.rezervasyon_id=r.rezervasyon_id) as ekstralar_str
        FROM Rezervasyon r JOIN Arac a ON r.arac_id=a.arac_id
        WHERE r.musteri_id=%s ORDER BY r.rezervasyon_id DESC
    """
    cursor.execute(sql, (mid,))
    res = cursor.fetchall()
    conn.close()
    return res

# --- KUPON ---
def get_kampanya_by_code(kod):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Kampanya WHERE kod=%s AND aktif=1 AND son_kullanma_tarihi >= CURDATE()", (kod,))
    res = cursor.fetchone()
    conn.close()
    return res

def check_user_coupon_usage(mid, kod):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Rezervasyon WHERE musteri_id=%s AND indirim_kodu=%s AND durum!='İptal'", (mid, kod))
    cnt = cursor.fetchone()[0]
    conn.close()
    return cnt > 0

# --- YORUM / FAVORİ ---
def add_yorum(mid, metin, puan):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Yorum (musteri_id, yorum_metni, puan, durum) VALUES (%s,%s,%s,'Bekliyor')", (mid, metin, puan))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def get_onayli_yorumlar():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # [DÜZELTME] MAX() eklenerek GROUP BY hatası giderildi
    sql = """
        SELECT y.*, 
               MAX(m.ad) as ad, 
               MAX(LEFT(m.soyad, 1)) as soyad_bas_harf, 
               MAX(m.ProfilResim) as ProfilResim, 
               MAX(s.sehir_ad) as sehir_ad 
        FROM Yorum y 
        JOIN Musteri m ON y.musteri_id = m.musteri_id 
        LEFT JOIN Rezervasyon r ON r.musteri_id = m.musteri_id 
        LEFT JOIN Arac a ON r.arac_id = a.arac_id
        LEFT JOIN Sehir s ON a.bulundugu_sehir_id = s.sehir_id
        WHERE y.durum = 'Onaylandı' 
        GROUP BY y.yorum_id 
        ORDER BY y.tarih DESC LIMIT 6
    """
    cursor.execute(sql)
    res = cursor.fetchall()
    conn.close()
    return res

def toggle_favori(mid, aid):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT favori_id FROM Favori WHERE musteri_id=%s AND arac_id=%s", (mid, aid))
        ex = cursor.fetchone()
        if ex:
            cursor.execute("DELETE FROM Favori WHERE favori_id=%s", (ex[0],))
            action = 'removed'
        else:
            cursor.execute("INSERT INTO Favori (musteri_id, arac_id) VALUES (%s,%s)", (mid, aid))
            action = 'added'
        conn.commit()
        return {'status':'success', 'action':action}
    except: return {'status':'error'}
    finally: conn.close()

def get_user_favori_ids(mid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT arac_id FROM Favori WHERE musteri_id=%s", (mid,))
    res = [r[0] for r in cursor.fetchall()]
    conn.close()
    return res

def get_user_favoriler_detayli(mid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT f.favori_id, a.*, s.sehir_ad FROM Favori f JOIN Arac a ON f.arac_id=a.arac_id JOIN Sehir s ON a.bulundugu_sehir_id=s.sehir_id WHERE f.musteri_id=%s ORDER BY f.favori_id DESC", (mid,))
    res = cursor.fetchall()
    conn.close()
    return res

# --- ADMIN FONKSİYONLARI ---
def get_dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    stats = {}
    cursor.execute("SELECT COUNT(*) as sayi FROM Arac")
    stats['arac'] = cursor.fetchone()['sayi']
    cursor.execute("SELECT COUNT(*) as sayi FROM Musteri")
    stats['musteri'] = cursor.fetchone()['sayi']
    
    cursor.execute("SELECT SUM(toplam_ucret) as ciro FROM Rezervasyon WHERE durum IN ('Onaylandı', 'Tamamlandı')")
    gelir = cursor.fetchone()['ciro'] or 0
    cursor.execute("SELECT SUM(maliyet) as gider FROM Bakim")
    gider = cursor.fetchone()['gider'] or 0
    stats['ciro'] = float(gelir) - float(gider)

    cursor.execute("SELECT a.marka, COUNT(r.rezervasyon_id) as sayi FROM Rezervasyon r JOIN Arac a ON r.arac_id=a.arac_id GROUP BY a.marka LIMIT 5")
    md = cursor.fetchall()
    stats['marka_isimleri'] = [i['marka'] for i in md]
    stats['marka_sayilari'] = [i['sayi'] for i in md]
    stats['aktif'] = sum(stats['marka_sayilari'])

    cursor.execute("SELECT DATE_FORMAT(baslangic_tarihi, '%Y-%m') as ay, SUM(toplam_ucret) as toplam FROM Rezervasyon WHERE durum IN ('Onaylandı', 'Tamamlandı') GROUP BY ay ORDER BY ay ASC LIMIT 6")
    kd = cursor.fetchall()
    stats['ay_isimleri'] = [i['ay'] for i in kd]
    stats['aylik_kazanclar'] = [float(i['toplam']) for i in kd]
    conn.close()
    return stats

def get_dashboard_tables():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.*, m.ad as musteri_ad, m.soyad as musteri_soyad, m.telefon, a.plaka, a.marka, a.model,
               (SELECT GROUP_CONCAT(eh.ad SEPARATOR ', ') FROM RezervasyonEkstra re JOIN EkstraHizmet eh ON re.ekstra_id=eh.ekstra_id WHERE re.rezervasyon_id=r.rezervasyon_id) as ekstralar_str
        FROM Rezervasyon r JOIN Musteri m ON r.musteri_id=m.musteri_id JOIN Arac a ON r.arac_id=a.arac_id ORDER BY r.rezervasyon_id DESC LIMIT 5
    """)
    rez = cursor.fetchall()
    cursor.execute("SELECT * FROM Musteri ORDER BY musteri_id DESC LIMIT 5")
    mus = cursor.fetchall()
    cursor.execute("SELECT a.marka, a.model, a.plaka, DATEDIFF(s.bitis_tarihi, CURDATE()) as kalan_gun FROM Arac a JOIN Sigorta s ON a.sigorta_id=s.sigorta_id WHERE DATEDIFF(s.bitis_tarihi, CURDATE()) <= 30")
    uyar = cursor.fetchall()
    conn.close()
    return rez, mus, uyar

def get_all_table_names():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    t = [r[0] for r in cursor.fetchall()]
    conn.close()
    return t

def get_table_data(t_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if not t_name.isidentifier(): return [], []
        cursor.execute(f"SELECT * FROM {t_name}")
        rows = cursor.fetchall()
        cols = [i[0] for i in cursor.description]
        return cols, rows
    except: return [], []
    finally: conn.close()

def run_custom_sql(q):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(q)
        if q.strip().upper().startswith("SELECT") or q.strip().upper().startswith("SHOW"):
            rows = cursor.fetchall()
            cols = [i[0] for i in cursor.description] if cursor.description else []
            conn.close()
            return {'status':'success', 'columns':cols, 'rows':rows}
        else:
            conn.commit()
            aff = cursor.rowcount
            conn.close()
            return {'status':'success', 'message': f"Etkilenen: {aff}"}
    except Exception as e:
        conn.close()
        return {'status':'error', 'message': str(e)}

# --- BAKIM / EXCEL / DİĞER ---
def add_bakim(aid, neden, maliyet, tarih):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Bakim (arac_id, bakim_nedeni, maliyet, giris_tarihi) VALUES (%s,%s,%s,%s)", (aid, neden, maliyet, tarih))
        cursor.execute("UPDATE Arac SET durum='Bakımda' WHERE arac_id=%s", (aid,))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def finish_bakim(bid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT arac_id FROM Bakim WHERE bakim_id=%s", (bid,))
        rec = cursor.fetchone()
        if rec:
            cursor.execute("UPDATE Bakim SET durum='Tamamlandı', cikis_tarihi=CURDATE() WHERE bakim_id=%s", (bid,))
            cursor.execute("UPDATE Arac SET durum='Müsait' WHERE arac_id=%s", (rec['arac_id'],))
            conn.commit()
            return True
        return False
    except: return False
    finally: conn.close()

def get_bakim_listesi():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT b.*, a.plaka, a.marka, a.model FROM Bakim b JOIN Arac a ON b.arac_id=a.arac_id ORDER BY b.durum ASC, b.giris_tarihi DESC")
    res = cursor.fetchall()
    conn.close()
    return res

def get_calendar_events():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT r.rezervasyon_id, r.baslangic_tarihi, r.bitis_tarihi, a.plaka, a.marka, m.ad, m.soyad, r.durum FROM Rezervasyon r JOIN Arac a ON r.arac_id=a.arac_id JOIN Musteri m ON r.musteri_id=m.musteri_id WHERE r.durum IN ('Onaylandı','Kirada')")
    res = cursor.fetchall()
    conn.close()
    return res

def add_kampanya(kod, oran, tarih):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Kampanya (kod, indirim_orani, son_kullanma_tarihi) VALUES (%s,%s,%s)", (kod, oran, tarih))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def get_all_kampanyalar():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT *, DATEDIFF(son_kullanma_tarihi, CURDATE()) as kalan_gun FROM Kampanya ORDER BY son_kullanma_tarihi DESC")
    res = cursor.fetchall()
    conn.close()
    return res

def delete_kampanya(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Kampanya WHERE kampanya_id=%s", (id,))
    conn.commit()
    conn.close()
    return True

def get_tum_musteriler_excel():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT musteri_id, ad, soyad, eposta, telefon, adres, dogum_tarihi FROM Musteri")
    res = cursor.fetchall()
    conn.close()
    return res

def get_aylik_ciro_excel():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT DATE_FORMAT(baslangic_tarihi, '%Y-%m') as Donem, SUM(toplam_ucret) as Ciro, COUNT(*) as Islem_Sayisi FROM Rezervasyon WHERE durum IN ('Onaylandı', 'Tamamlandı') GROUP BY Donem ORDER BY Donem DESC")
    res = cursor.fetchall()
    conn.close()
    return res

def get_all_sigortalar():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT s.*, a.plaka, a.marka, a.model, a.durum as arac_durumu, DATEDIFF(s.bitis_tarihi, CURDATE()) as kalan_gun FROM Sigorta s LEFT JOIN Arac a ON s.sigorta_id = a.sigorta_id ORDER BY s.bitis_tarihi ASC")
    res = cursor.fetchall()
    conn.close()
    return res

def update_sigorta(sid, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Sigorta SET sigorta_sirketi=%s, baslangic_tarihi=%s, bitis_tarihi=%s, police_no=%s WHERE sigorta_id=%s", (data['sirket'], data['baslangic'], data['bitis'], data['police'], sid))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def get_sigorta_by_id(sid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Sigorta WHERE sigorta_id=%s", (sid,))
    res = cursor.fetchone()
    conn.close()
    return res

def get_rezervasyon_detay_pdf(rid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT r.*, m.ad, m.soyad, m.ehliyet_no, m.telefon, m.eposta, m.adres, a.plaka, a.marka, a.model, a.yil, a.yakit_turu, s.sigorta_sirketi, s.police_no FROM Rezervasyon r JOIN Musteri m ON r.musteri_id = m.musteri_id JOIN Arac a ON r.arac_id = a.arac_id LEFT JOIN Sigorta s ON a.sigorta_id = s.sigorta_id WHERE r.rezervasyon_id = %s", (rid,))
    res = cursor.fetchone()
    if res:
        cursor.execute("SELECT e.ad, e.gunluk_ucret FROM RezervasyonEkstra re JOIN EkstraHizmet e ON re.ekstra_id = e.ekstra_id WHERE re.rezervasyon_id = %s", (rid,))
        res['ekstralar'] = cursor.fetchall()
    conn.close()
    return res

def get_tum_yorumlar_admin():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT y.*, m.ad, m.soyad FROM Yorum y JOIN Musteri m ON y.musteri_id = m.musteri_id ORDER BY field(y.durum, 'Bekliyor', 'Onaylandı'), y.tarih DESC")
    res = cursor.fetchall()
    conn.close()
    return res

def yorum_durum_degistir(yid, islem):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if islem == 'onayla': cursor.execute("UPDATE Yorum SET durum = 'Onaylandı' WHERE yorum_id = %s", (yid,))
        elif islem == 'sil': cursor.execute("DELETE FROM Yorum WHERE yorum_id = %s", (yid,))
        conn.commit()
        return True
    except: return False
    finally: conn.close()