# Fon Analiz Sistemi (FAS)

TEFAS üzerinden fon verisi çeken, 28+ risk-getiri metriği hesaplayan, portföy optimizasyonu ve performans atıf analizi sunan bir Dash web uygulaması.

## Özellikler

- **Fon Keşfi** — TEFAS'taki tüm YAT fonlarını kategori, şirket, dönem bazında filtreleme ve karşılaştırma
- **Risk-Getiri Metrikleri** — Sharpe, Sortino, Calmar, Sterling, Bilgi Oranı, Alfa, Beta, R², VaR, CVaR, Maksimum DD, Ortalama DD, DD Süresi, Toparlanma Süresi, Ulcer, Burke, Skewness, Kurtosis, Omega, M², Up/Down Capture, Batting Average, Active Share (+28 metrik)
- **Benchmark Karşılaştırma** — KYD endeksleri, TLREF, FHISE, ATKAP ve özel mix benchmark oluşturma
- **Korelasyon & Rolling** — Fonlar arası korelasyon matrisi, 63 günlük rolling Sharpe
- **Portföy Optimizasyonu** — MVO (Max Sharpe / Min Varyans), Risk Parity, Target Return, Efficient Frontier, Monte Carlo simülasyonu, walk-forward backtest, goal-based projeksiyon
- **Performans Atıf Analizi** — TE ayrıştırması, Fama-French regresyonu, RBSA stil analizi, Brinson atıf analizi, 7 senaryolu stres testi, ADF durağanlık / eşbütünleşme testi
- **REST API** — 7 endpoint ile fon listesi, tarihsel veri, metrik hesaplama, optimizasyon
- **Dark Mode** — Gece/gündüz teması, kalıcı tercih
- **Mobil Uyumlu** — Hamburger menü, offcanvas sidebar
- **Klavye Kısayolları** — Alt+1 Ana Sayfa, Alt+2 Fon Bulucu, Alt+3 Portföy, Alt+4 API
- **Onboarding** — İlk ziyarette adım adım tanıtım turu
- **Authentication** — Flask-Login ile giriş, favori fonlar ve kayıtlı portföyler
- **Fon Bilgi Kartı** — Yönetim ücreti, AUM, ihraç tarihi, stopaj, USD/TRY kuru, TÜFE reel getiri, işlem hacmi grafiği, benzer fon önerileri
- **Docker Desteği** — Tek komutla容器化 çalıştırma

## Hızlı Başlangıç

Projeyi klonlayıp tek komutla çalıştırabilirsiniz:

### Windows
```bash
git clone <repo-url>
cd fas
run.bat
```

### Linux / macOS
```bash
git clone <repo-url>
cd fas
chmod +x run.command
./run.command
```

### Docker
```bash
git clone <repo-url>
cd fas
docker compose up --build
```

İlk çalıştırmada `.venv` sanal ortamı otomatik oluşturulur ve bağımlılıklar yüklenir. Docker kullanımında bu adımlar atlanır.

## Manuel Kurulum

```bash
git clone <repo-url>
cd fas
python -m venv .venv

# Windows
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python index.py

# Linux / macOS
source .venv/bin/activate
pip install -r requirements.txt
python index.py
```

Uygulama başlatıldığında `http://127.0.0.1:8050` adresinde açılır.

## Ortam Değişkenleri (.env)

Proje köküne bir `.env` dosyası oluşturarak aşağıdaki değişkenleri tanımlayabilirsiniz (opsiyonel):

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `FAS_DEBUG` | `0` | Debug log seviyesi |
| `FAS_PORT` | `8050` | Uygulama portu |
| `FAS_DASH_DEBUG` | `0` | Dash debug modu |
| `FAS_SECRET_KEY` | `fas-dev-key-...` | Flask oturum anahtarı |
| `FAS_DATABASE_URL` | SQLite (yerel) | Veritabanı bağlantısı |
| `FAS_EVDS_API_KEY` | — | TCMB EVDS API anahtarı (makro veri) |
| `FAS_SMTP_HOST` | — | E-posta SMTP sunucusu |
| `FAS_SMTP_PORT` | — | SMTP portu |
| `FAS_SMTP_USER` | — | SMTP kullanıcı adı |
| `FAS_SMTP_PASS` | — | SMTP şifresi |

## Sayfalar

| Sayfa | Path | Açıklama |
|---|---|---|
| **Ana Sayfa** | `/` | Fon seçimi, benchmark karşılaştırma, metrik tablosu, grafikler (getiri, risk-getiri scatter, portföy dağılımı, korelasyon, rolling Sharpe) |
| **Fon Bulucu** | `/fon-bulucu` | Kategori/şirket/vade bazında fon tarama, percentil sıralama, karşılaştırma tablosu |
| **Portföy Analizi** | `/portfolio` | Dönem karşılaştırma (6 ay/1 yıl/3 yıl/5 yıl), MVO optimizasyonu, efficient frontier, atıf analizi, stres testi, kayıtlı portföyler |
| **API Doküman** | `/api-docs` | REST API endpoint referansı ve curl örnekleri |
| **Giriş** | `/giris` | Kullanıcı giriş sayfası (favori/kayıtlı portföy için) |

## Proje Yapısı

```
fas/
├── app.py                 # Dash uygulaması girişi, auth, REST API
├── index.py               # Çok sayfalı layout, tema, onboarding
├── run.bat / run.command  # Başlatma scriptleri
├── pyproject.toml         # Proje metadata
├── requirements.txt       # Python bağımlılıkları
├── Dockerfile             # Docker imaj tanımı
├── docker-compose.yml     # Docker Compose yapılandırması
├── .env.example           # Çevresel değişken şablonu
│
├── config/                # Uygulama ayarları
│   ├── settings.py        # Tüm konfigürasyon sabitleri
│   ├── constants.py       # Metrik isimleri, açıklamaları
│   ├── benchmarks.py      # Benchmark endeks tanımları
│   ├── benchmark_mapping.py  # Benchmark → fon kategorisi eşleme
│   └── logger.py          # Log yapılandırması
│
├── data/                  # Veri katmanı
│   ├── dao.py             # Veritabanı CRUD işlemleri
│   ├── queue.py           # Rate limit kuyruğu (JobQueue, RateLimiter)
│   ├── macro_scraper.py   # TCMB EVDS + TÜFE veri çekici
│   └── fetchers/          # TEFAS, TEFAS fetcher, benchmark verisi
│
├── components/            # Dash UI bileşenleri
│   ├── charts.py          # Tüm grafik fabrikaları (~25 fonksiyon)
│   ├── metrics.py         # 28+ risk-getiri metriği hesaplama
│   ├── optimizer.py       # Portföy optimizasyon motoru (MVO, RP, MC, vb.)
│   ├── attribution.py     # Performans atıf analizi (TE, FF, RBSA, Brinson, stres)
│   ├── layout.py          # Navbar, sidebar, offcanvas navigasyon
│   └── onboarding.py      # İlk ziyaret tanıtım turu
│
├── pages/                 # Sayfalar
│   ├── home.py            # Ana Sayfa
│   ├── fon_bulucu.py      # Fon Bulucu
│   ├── portfolio.py       # Portföy Analizi
│   ├── api_docs.py        # REST API Dokümantasyonu
│   ├── giris.py           # Giriş Sayfası
│   ├── duyurular.py       # TEFAS Duyuruları (geliştirme aşamasında)
│   └── detayli_bilgi.py   # Detaylı bilgi sayfası
│
├── core/                  # Çekirdek modüller
│   └── models/            # Veritabanı modelleri
│
├── assets/                # Statik dosyalar
│   ├── style.css          # Tema sistemi (~1400 satır, 40+ tasarım token)
│   ├── clientside.js      # İstemci tarafı JS (tema, kısayol, ARIA)
│   └── logo.png           # Uygulama logosu
│
├── scraper/               # Web scraper modülü
│   ├── kap_scraper.py     # KAP.org.tr benchmark verisi çekici
│   └── cache/             # Scraper önbelleği
│
├── scripts/               # Yardımcı scriptler
│   └── auto_update.py     # Otomatik güncelleme
│
├── tests/                 # Testler
│   ├── conftest.py        # Test yapılandırması
│   └── test_metrics.py    # Metrik hesaplama testleri
│
├── docs/                  # Dokümantasyon
│   ├── metrik_formulleri.md   # Metrik formülleri
│   └── veri_politikasi.md     # Veri politikası
│
├── api.py                 # REST API blueprint (7 endpoint)
├── auth.py                # Flask-Login yapılandırması
├── database.py            # SQLAlchemy oturum yönetimi
├── models.py              # ORM modelleri (User, Favorite, SavedPortfolio)
├── wsgi.py                # WebSocket skeleton (flask-socketio)
├── tlref_scraper.py       # TLREF (risksiz getiri) veri çekici
└── features_plan.md       # Özellik planı ve durum takibi
```

## REST API

Uygulama ile birlikte 7 REST API endpoint'i çalışır. Detaylı dokümantasyon ve curl örnekleri için çalışan uygulamada `/api-docs` sayfasını ziyaret edin.

| Metot | Endpoint | Açıklama |
|---|---|---|
| GET | `/api/v1/funds` | Tüm fonları listeler |
| GET | `/api/v1/funds/{kod}` | Tek fon anlık bilgisi |
| GET | `/api/v1/funds/{kod}/history` | Tarihsel fiyat verisi |
| GET | `/api/v1/benchmarks` | Benchmark endeks listesi |
| GET | `/api/v1/benchmarks/{kod}/data` | Benchmark endeks verisi |
| POST | `/api/v1/metrics` | Fon metriklerini hesaplar |
| POST | `/api/v1/optimize` | Portföy optimizasyonu |

## Teknolojiler

- **Frontend:** Dash 4.1, Dash Bootstrap 5.3 (Flatly), Dash Mantine, Bootstrap Icons
- **Backend:** Flask, SQLAlchemy, Flask-Login, flask-socketio
- **Hesaplama:** pandas, numpy, scipy, statsmodels
- **Veri:** requests, yfinance, pyarrow
- **Kapsayıcı:** Docker, Docker Compose
- **CI/CD:** GitHub Actions (pytest + coverage)

## Gereksinimler

- Python 3.10+
- pip
- (opsiyonel) Docker + Docker Compose

## Lisans

MIT
