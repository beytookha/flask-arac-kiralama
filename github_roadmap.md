# 🗺️ Project Roadmap & Role Integration Plan

Bu belge, **Araç Kiralama Otomasyonu** projesinin gelişim sürecini, mimari hedeflerini ve rol tabanlı (Role-Based) geliştirme rotasını içerir.

## 🚀 Proje Vizyonu
Güvenli, ölçeklenebilir ve kullanıcı dostu bir araç kiralama platformu oluşturmak. Proje şu anda **MVP (Minimum Viable Product)** aşamasındadır ve **V2.0 Mimari Dönüşüm** evresine geçmektedir.

---

## 📅 Gelişim Fazları (Development Phases)

### ✅ Faz 1: MVP (Tamamlandı)
- [x] Veritabanı şemasının oluşturulması ve normalize edilmesi.
- [x] Temel rezervasyon döngüsü (Araç Seç -> Tarih Seç -> Öde -> Kirala).
- [x] Basit Admin Paneli (KPI Dashboard, Araç Yönetimi).
- [x] Müşteri Paneli (Profil, Geçmiş Kiralamalar).
- [x] PDF Sözleşme üretimi ve E-posta bildirimleri.

### 🛠️ Faz 2: Mimari Refactoring (Şu Anki Odak)
Bu faz, projenin "Spagetti Kod" yapısından kurtarılıp modüler hale getirilmesini hedefler.
- [ ] **Modüler Yapıya Geçiş:** `app.py` dosyasının parçalanarak **Blueprint** yapısına geçilmesi.
- [ ] **Konfigürasyon Yönetimi:** `.env` ve `config.py` ile hardcoded şifrelerin temizlenmesi.
- [ ] **Veritabanı Katmanı:** Connection Pooling entegrasyonu (Performans artışı için).
- [ ] **Statik Analiz:** Kod kalitesinin artırılması ve PEP8 uyumu.

### 🔮 Faz 3: İleri Özellikler & Mikroservis Hazırlığı
- [ ] **API First Yaklaşımı:** Mobil uygulama entegrasyonu için RESTful API (Swagger/OpenAPI).
- [ ] **Ödeme Sistemi:** Iyzico veya Stripe sanal POS entegrasyonu.
- [ ] **Redis Önbellekleme:** Sık sorgulanan araç listesi verilerinin cache'lenmesi.
- [ ] **Dockerizasyon:** Projenin container yapısına alınması.

---

## 👥 Rol Rotası (Role-Based Routing Map)

Proje GitHub üzerinde 3 ana kolda (Branch/Role) ilerleyecektir. Her rolün sorumluluk alanı ve erişim yetkileri ayrıştırılmıştır.

### 1. `feature/frontend-ux` (Frontend Developer Rolü)
*   **Odak:** Kullanıcı deneyimi, Tasarım, HTML/CSS/JS.
*   **Görevler:**
    *   Jinja2 şablonlarının parçalanması (`base.html`, `macros`).
    *   Responsive tasarım iyileştirmeleri.
    *   AJAX ile sayfa yenilenmeden filtreleme yapılması.
*   **Yetki:** `templates/`, `static/` klasörleri.

### 2. `feature/backend-core` (Backend Developer Rolü)
*   **Odak:** İş mantığı, Veritabanı, Güvenlik.
*   **Görevler:**
    *   Blueprint refactoring (View Module ayrımı).
    *   SQL optimizasyonu ve Connection Pool.
    *   Güvenlik (CSRF koruması, Rate Limiting).
*   **Yetki:** `blueprints/`, `services/`, `extensions.py`, `models/`.

### 3. `feature/devops-db` (Database Admin / DevOps Rolü)
*   **Odak:** Veri bütünlüğü, Sunucu yönetimi, CI/CD.
*   **Görevler:**
    *   Stored Procedure ve Trigger bakımları.
    *   Yedekleme senaryoları.
    *   GitHub Actions ile otomatik test ve deploy süreçleri.
*   **Yetki:** `schema.sql`, `Dockerfile`, `.github/workflows`.

---

## 🚦 Katkı Verme Rehberi (Contribution)

1.  Bir **Issue** açarak yapmak istediğiniz değişikliği tartışın.
2.  İlgili rolün branch'inden (`feature/backend-core` vb.) yeni bir dal oluşturun.
3.  Geliştirmenizi yapın ve **Pull Request (PR)** açın.
4.  Kod incelemesi (Code Review) sonrası `main` dala merge edilecektir.
