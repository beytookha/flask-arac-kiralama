# 🧠 Project Memory Bank & Git Strategy

Bu dosya, projenin gelişim sürecindeki **Git Commit Stratejisini** ve yapılacak işlerin (To-Do) durumunu takip etmek için oluşturulmuştur. Her bir adım tamamlandığında `[x]` olarak işaretlenecektir.

## 📦 Mevcut Durum: Faz 1 (MVP) Tamamlandı
Proje şu an çalışır durumda, temel fonksiyonlar (Rezervasyon, Admin, Müşteri) aktif. Refactoring (Düzenleme) işlemi öncesi bu haliyle saklanacak.

---

## 📅 Git Commit Planı

### 🟢 Başlangıç (Current State)
- [x] **Commit 001: Initial MVP Release**
    *   **Mesaj Başlığı:** `feat: Initial MVP release of Car Rental System`
    *   **Detay:**
        *   Core Flask application structure (app.py)
        *   Database manager with connection handling (db_manager.py)
        *   MySQL schema with stored procedures and events (schema.sql)
        *   HTML Templates for Customer and Admin panels
        *   Static assets (CSS, JS, Images)
    *   **Komut:** `git add .` -> `git commit -m "..."`

- [x] **Commit 002: Project Documentation**
    *   **Mesaj Başlığı:** `docs: Add project analysis and roadmap`
    *   **Detay:**
        *   Added `project_analysis.md` for refactoring strategy.
        *   Added `github_roadmap.md` for project vision and roles.
        *   Added `memory_bank.md` for commit tracking.

### 🛠️ Faz 2: Refactoring (Mimari Düzenleme)
*Bu aşamada kod modüler hale getirilecek. Her adım ayrı bir commit olacak.*

- [ ] **Commit 003: Infrastructure Setup**
    *   **Mesaj Başlığı:** `chore: Setup project configuration and structure`
    *   **Detay:**
        *   Create `config.py`
        *   Create `.env` example
        *   Create `run.py` entry point
        *   Create `requirements.txt`

- [ ] **Commit 004: Database Layer Refactor**
    *   **Mesaj Başlığı:** `refactor: Implement Connection Pooling and Service Layer`
    *   **Detay:**
        *   Replace manual db connection with connection pool.
        *   Create `extensions.py` for DB init.

- [ ] **Commit 005: Blueprint - Auth Module**
    *   **Mesaj Başlığı:** `refactor(auth): Extract authentication logic to Blueprint`
    *   **Detay:**
        *   Move login/register/logout routes to `blueprints/auth.py`.
        *   Move template files to `templates/auth/`.

- [ ] **Commit 006: Blueprint - Main & Customer Module**
    *   **Mesaj Başlığı:** `refactor(customer): Extract customer logic to Blueprint`
    *   **Detay:**
        *   Move index, profile, reservation routes to `blueprints/customer.py`.

- [ ] **Commit 007: Blueprint - Admin Module**
    *   **Mesaj Başlığı:** `refactor(admin): Extract admin panel logic to Blueprint`
    *   **Detay:**
        *   Move admin dashboard and management routes to `blueprints/admin.py`.

### 🚀 Faz 3: Yeni Özellikler
- [ ] **Commit 008: API Integration**
    *   **Mesaj Başlığı:** `feat(api): Add RESTful API endpoints for calendar events`

---

## 📝 Aktif Görev Listesi (Task Tracking)
Burada projedeki anlık değişiklikleri not alabiliriz.

*   [ ] Git repo başlat (`git init`)
*   [ ] `.gitignore` dosyası oluştur (venv, __pycache__, .env vb. için)
*   [ ] İlk commit'i yap.
