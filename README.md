# Fon Analiz Sistemi (FAS)

TEFAS üzerinden fon verisi çeken, risk-getiri metrikleri hesaplayan ve interaktif raporlar sunan bir web uygulaması.

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
chmod +x run.sh
./run.sh
```

İlk çalıştırmada `.venv` sanal ortamı otomatik oluşturulur ve bağımlılıklar yüklenir.

## Manuel Kurulum

Eğer otomatik scriptleri kullanmak istemezseniz:

```bash
python -m venv .venv

# Windows
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python index.py

# Linux / macOS
source .venv/bin/activate
pip install -r requirements.txt
python index.py
```

Uygulama başlatıldığında tarayıcınızda `http://127.0.0.1:8050` adresinden erişebilirsiniz.

## Proje Yapısı

```
fas/
├── app.py              # Dash uygulaması
├── index.py            # Çok sayfalı layout
├── run.bat / run.sh    # Başlatma scriptleri
├── config/             # Ayarlar, sabitler, logger
├── data/               # Veri çekme, temizleme, cache
│   └── fetchers/       # TEFAS API wrapper
├── core/               # Metrik hesaplamaları, modeller
├── components/         # Dash UI bileşenleri
├── pages/              # Sayfalar (Home, Analiz, Karşılaştırma, Rapor)
└── reports/            # Rapor şablonları
```

## Gereksinimler

- Python 3.10+
- pip

## Lisans

MIT
