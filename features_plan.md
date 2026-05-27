# FAS Feature Plan

> Portföy Yönetim Şirketi Perspektifi — Fon Analiz Sistemi Özellik Planı

---

## ✅ YAPILMIŞ OLANLAR (28 özellik)

### CRITICAL (3/6)
| # | Özellik | Commit |
|---|---|---|
| 4 | **BES Fon Desteği** — YAT/BES toggle sidebar'da, 6 dosya güncellendi | `da2483c` |
| 5 | **Portföy Ağırlıklandırma** — % ağırlık input'ları + ağırlıklı portföy serisi | `69b9351` |
| 6 | **Excel/CSV Export** — Metrik tablosu CSV indirme butonu | `05e3b7c` |

### HIGH (8/19)
| # | Özellik | Commit |
|---|---|---|
| 13 | **Rolling Metrikler** — 63 günlük kayan Sharpe oranı chart | `aacede3` |
| 14 | **Korelasyon Matrisi Heatmap** — Fonlar arası korelasyon görselleştirme | `08f9d81` |
| 15 | **Up/Down Capture Ratios** — Metrik olarak eklendi | `7ac23cc` |
| 16 | **Dövize Göre Düzeltilmiş Getiri** — USD/TRY kuru + dönemsel değişim | `c64ad5f` |
| 17 | **Fon Portföy Dağılımı** — Donut chart ile varlık kırılımı | `e5c0a28` |
| 18 | **Yönetim Ücretleri** — Fon bilgi kartında yönetim ücreti sütunu | `df16c32` |
| 19 | **Fon Büyüklüğü (AUM)** — Fon bilgi kartında portföy büyüklüğü | `df16c32` |
| 20 | **Kurucu Bazlı Filtre** — Fon Bulucu'da şirket kodu ile filtreleme | `42b9caf` |

### MEDIUM (9/22)
| # | Özellik | Commit |
|---|---|---|
| 28 | **Detaylı Drawdown Analizi** — Ort DD, DD Süresi, Toparlanma, Ulcer Index | `7ac23cc` |
| 29 | **Skewness / Kurtosis** — Çarpıklık ve basıklık metrikleri | `7ac23cc` |
| 32 | **Fon Yaşı / İhraç Tarihi** — Fon bilgi kartında sütun | `680a765` |
| 33 | **Percentile Rank** — Fon Bulucu tablosunda "Top %X" sütunu | `42b9caf` |
| 35 | **Katılım Fon Ayrımı** — Tabloda "KATILIM" badge | `09c4012` |
| 36 | **Serbest Fon Özel İşlem** — Tabloda "SERBEST" badge | `09c4012` |
| 37 | **Stopaj Sonrası Getiri (Oran)** — Fon bilgi kartında stopaj sütunu | `09c4012` |
| 38 | **Forex Veri Kaynağı** — USD/TRY yfinance üzerinden çekiliyor | `c64ad5f` |
| 43 | **Dashboard / Piyasa Özeti** — Günlük top 5 yükselen widget | `c319b38` |

### LOW (8/19)
| # | Özellik | Commit |
|---|---|---|
| 49 | **Calmar Oranı** — Yıllık getiri / Max DD | `7ac23cc` |
| 50 | **Sterling Oranı** — Yıllık getiri / (Ort DD + %10) | `7ac23cc` |
| 52 | **Omega Oranı** — Tam dağılımlı risk-ödül | `12fabb4` |
| 53 | **Batting Average** — Benchmark yenme yüzdesi | `7ac23cc` |
| 54 | **Active Share** — Benchmark'tan sapma yaklaşımı | `12fabb4` |
| 55 | **M² / Modigliani Ölçüsü** — Riske göre düzeltilmiş getiri | `12fabb4` |
| 67 | **.env Desteği** — python-dotenv + `.env.example` | `b692848` |
| 68 | **Log Rotasyonu** — RotatingFileHandler 5MB/3 yedek | `b692848` |

---

## 📦 KALAN EKSİKLER — İş Paketleri (40 özellik)

---

### İş Paketi A: Portföy Mühendisliği (CRITICAL, ~15 gün)

| # | Özellik | Açıklama |
|---|---|---|
| 1 | **Portföy Optimizasyonu** | Markowitz MVO, kovaryans matrisi, min varyans, max Sharpe, efficient frontier. `scipy.optimize` ile. |
| 10 | **Efficient Frontier Görselleştirme** | Risk-getiri scatter'ına EF eğrisi + CML + tangent portfolio. |
| 44 | **Risk Budgeting / Risk Parity** | Eşit risk katkılı portföy, risk bütçesi kısıtları. |
| 7 | **Portföy Rebalancing** | Eşik bazlı (%5 drift) ve takvim bazlı simülasyon. Maliyet analizi. |
| 9 | **Portföy Backtesting** | Rolling window, walk-forward, seçili ağırlıklarla geçmiş simülasyonu. |
| 45 | **Hedef Bazlı Planlama** | Hedef getiri/tarih için portföy önerisi, birikim projeksiyonu. |
| 27 | **Monte Carlo Simülasyonu** | İleriye dönük getiri dağılımı, MC VaR, emeklilik projeksiyonu. |

---

### İş Paketi B: Atıf & Stil Analizi (HIGH, ~10 gün)

| # | Özellik | Açıklama |
|---|---|---|
| 2 | **Performans Atıfı (Brinson)** | Allocation + selection + interaction dekompozisyonu. |
| 11 | **Faktör Analizi (Fama-French)** | 3/5 faktör modeli, Carhart momentum, faktör yüklemeleri. |
| 12 | **Returns-Based Style Analysis** | Sharpe RBSA, style drift takibi. |
| 26 | **Stres Testi / Senaryo** | 2008, 2018 TR, COVID senaryoları; faiz ±500bps, kur ±%20 şokları. |
| 56 | **Tracking Error Dekompozisyonu** | Sistematik vs idiosinkratik TE ayrıştırması. |

---

### İş Paketi C: Raporlama & Export (CRITICAL, ~8 gün)

| # | Özellik | Açıklama |
|---|---|---|
| 3 | **PDF Rapor Çıktısı** | Jinja2 template + WeasyPrint/pdfkit. Şirket logosu, disclaimer, metrik + grafik. |
| 25 | **Enflasyona Göre Düzeltilmiş Getiri** | TÜİK TÜFE verisi entegrasyonu, reel getiri hesaplaması. |
| 34 | **Time-Weighted vs Money-Weighted** | MWR / IRR hesaplaması, nakit akışlı portföyler için. |
| 30 | **İşlem Hacmi / Fund Flow** | `islem_hacmi()` API verisi UI'a eklenecek. Trend analizi. |
| 31 | **TEFAS Duyuruları** | `duyurular()` API verisi, bildirim kartı veya sayfası. |

---

### İş Paketi D: Altyapı & DevOps (HIGH-MEDIUM, ~10 gün)

| # | Özellik | Açıklama |
|---|---|---|
| 21 | **Kullanıcı Kimlik Doğrulama** | Flask-Login veya Dash-Enterprise auth. Rol bazlı yetkilendirme. |
| 22 | **Veritabanı** | SQLite (MVP) → PostgreSQL. Kullanıcı, portföy, analiz geçmişi, favoriler. |
| 23 | **REST API Katmanı** | Flask/Dash API endpoint'leri. Harici sistem entegrasyonu. |
| 8 | **Kayıtlı Portföyler** | DB'ye bağlı adlandırılmış portföyler, yan yana karşılaştırma. |
| 39 | **Server-side Favoriler** | localStorage → DB migration. Cihaz bağımsız izleme listesi. |
| 24 | **Test Kapsamı** | Pytest: sayfalar, fetcher'lar, chart'lar, cache, scraper'lar. Coverage %5 → %70+. |
| 46 | **Docker Desteği** | Dockerfile + docker-compose.yml. Tek komutla ayağa kaldırma. |
| 47 | **CI/CD Pipeline** | GitHub Actions: lint → test → build → deploy. |
| 48 | **Rate Limit Queue** | Retry + exponential backoff + persistent queue (Redis/SQLite). |

---

### İş Paketi E: UX & Erişilebilirlik (MEDIUM-LOW, ~7 gün)

| # | Özellik | Açıklama |
|---|---|---|
| 41 | **Fuzzy Fon Arama** | Anahtar kelime bazlı arama (teknoloji, sağlık, eurobond). |
| 42 | **Mobil Responsive** | Hamburger menü, mobil-first kart düzeni. |
| 40 | **E-posta Uyarıları** | NAV eşik, fiyat değişimi, benchmark sapması için bildirim. |
| 62 | **"Benzer Fon" Keşfi** | Kategori/getiri benzerliğine göre öneri. |
| 63 | **Klavye Kısayolları** | Sayfa gezinme, sık işlemler için shortcut. |
| 64 | **Erişilebilirlik (WCAG/ARIA)** | Ekran okuyucu, kontrast, klavye navigasyonu. |
| 65 | **Onboarding / Rehberli Tur** | İlk kullanım için adım adım tanıtım. |

---

### İş Paketi F: İleri Analitik & Veri (LOW, ~8 gün)

| # | Özellik | Açıklama |
|---|---|---|
| 51 | **Burke Oranı** | Getiri / sqrt(sum(drawdown²)). |
| 57 | **Cointegration Testleri** | ADF, Johansen. Pair trading sinyalleri. |
| 58 | **BYF (ETF) Ayrımı** | ETF'lere özel spread, prim/iskonto bilgisi. |
| 59 | **ESG/Sürdürülebilirlik** | ESG kategorisi filtresi. |
| 60 | **Sektör/Market Cap Kırılımı** | Large/mid/small cap, sektör dağılımı. |
| 61 | **Makroekonomik Veri** | TÜFE, GSYH, CDS, TCMB faizi. |
| 66 | **WebSocket / Gerçek Zamanlı** | Anlık fiyat, push notification. |

---

## Özet

| Durum | Adet |
|---|---|
| ✅ **Yapılmış** | **28** |
| 📦 **Kalan (6 iş paketi)** | **40** |
| **TOPLAM** | **68** |

### İş Paketi Özeti

| Paket | Konu | Özellik | Süre (tahmini) |
|---|---|---|---|
| A | Portföy Mühendisliği | 7 | ~15 gün |
| B | Atıf & Stil Analizi | 5 | ~10 gün |
| C | Raporlama & Export | 5 | ~8 gün |
| D | Altyapı & DevOps | 9 | ~10 gün |
| E | UX & Erişilebilirlik | 7 | ~7 gün |
| F | İleri Analitik & Veri | 7 | ~8 gün |
