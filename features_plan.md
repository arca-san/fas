# FAS Feature Gap Audit

> Portföy Yönetim Şirketi Perspektifi — Fon Analiz Sistemi Eksik Özellikler

---

## Mevcut Yetenekler

- 4 sayfa: Ana Sayfa (`/`), Fon Bulucu (`/fon-bulucu`), Portföy Analizi (`/portfolio`), Detaylı Bilgi (`/detayli-bilgi`)
- 14 risk/getiri metriği: Sharpe, Sortino, Beta, Alfa, VaR, CVaR, Max Drawdown, Volatilite, Treynor, R², Enformasyon Oranı, Toplam Getiri, Yıllık Getiri, Aşağı Yönlü Volatilite
- 3 veri kaynağı: TEFAS (fon fiyatları), BIST-KYD (63 endeks), Yahoo Finance (17 global benchmark)
- Kümülatif getiri çizgi grafiği, risk-getiri scatter plot, bar chart (dönemsel karşılaştırma)
- Light/dark tema, favorites (localStorage), custom mix benchmark oluşturma
- TLREF risksiz faiz oranı, benchmark otomatik atama (KAP cache → scraping → kategori mapping fallback)
- Parquet tabanlı dosya cache (24 saat TTL)

---

## CRITICAL — En Yüksek Öncelikli Eksikler (6 adet)

| # | Özellik | Açıklama |
|---|---|---|
| 1 | **Portföy Optimizasyonu** | Markowitz ortalama-varyans optimizasyonu. Efficient frontier, minimum varyans portföyü, teğet portföy, maksimum Sharpe portföyü. `scipy` requirements'ta var ama hiç kullanılmamış. Kovaryans matrisi inşası, optimizasyon kısıtları (ağırlık alt/üst limit, sektör limiti). |
| 2 | **Performans Atıfı (Brinson Attribution)** | Allocation effect vs selection effect vs interaction effect dekompozisyonu. Şu an sadece Jensen Alpha (tek faktör) var. Sektör ve varlık sınıfı bazında atıf yok. Benchmark'tan sapmanın kaynağı analiz edilemiyor. |
| 3 | **PDF Rapor Çıktısı** | Müşteriye, yönetime veya SPK uyumuna sunulacak profesyonel rapor yok. Metrik tabloları, grafikler, benchmark karşılaştırması, şirket logosu ve yasal disclaimer içeren PDF. |
| 4 | **BES (Bireysel Emeklilik) Fon Desteği** | TEFAS API `fonTipi="BES"` parametresini destekliyor ancak her yerde `"YAT"` hardcoded. BES fon evreni (yaklaşık 300+ fon) tamamen dışarıda. Devlet katkısı hesaplaması, hak kazanma süresi takibi de yok. |
| 5 | **Portföy Ağırlıklandırma ve Özel Dağılım** | Tüm fonlar eşit ağırlıklı varsayılıyor. Kullanıcı yüzdesel ağırlık giremiyor. Ağırlıklı portföy getirisi, ağırlıklı risk metrikleri hesaplanmıyor. |
| 6 | **Excel / CSV Export** | Hiçbir veri, tablo veya analiz sonucu dışa aktarılamıyor. Metrik tabloları, fiyat serileri, karşılaştırma sonuçları Excel'e indirilemiyor. |

---

## HIGH — Yüksek Öncelikli Eksikler (19 adet)

### Portföy Yönetimi

| # | Özellik | Açıklama |
|---|---|---|
| 7 | **Portföy Rebalancing** | Eşik bazlı (%5 sapma) ve takvim bazlı (aylık/çeyreklik) rebalancing simülasyonu. Drift analizi, rebalancing maliyeti hesaplaması. |
| 8 | **Kayıtlı / Adlandırılmış Portföyler** | Portföy yapılandırmalarını adlandırıp kaydetme, sonra geri çağırma. Yan yana portföy karşılaştırması. |
| 9 | **Portföy Backtesting** | Seçili ağırlıklarla geçmiş dönem simülasyonu. Rolling window backtest, walk-forward optimizasyon. |
| 10 | **Efficient Frontier Görselleştirme** | Risk-getiri düzleminde efficient frontier eğrisi, portföylerin konumu, tangent portfolio, CML çizgisi. Portföy yönetiminin en temel görseli. |

### Analitik

| # | Özellik | Açıklama |
|---|---|---|
| 11 | **Faktör Analizi (Fama-French / Carhart)** | 3/5 faktör modeli, Carhart momentum faktörü. Faktör yüklemeleri (loading), faktör getirileri. Türkiye'ye özel faktörler (BIST boyut, değer). |
| 12 | **Returns-Based Style Analysis (RBSA)** | William Sharpe stili getiri bazlı stil analizi. Fonun hangi varlık sınıflarına ne kadar maruz kaldığı. Style drift takibi (zaman içinde stilde kayma). |
| 13 | **Rolling (Kayan Pencere) Metrikler** | Tüm metriklerin zaman serisi: rolling Sharpe (1y, 3y), rolling beta, rolling alpha, rolling volatility, rolling max drawdown, rolling correlation. Trendleri görmek için kritik. |
| 14 | **Korelasyon Matrisi / Heatmap** | Fonlar arası ve fon-benchmark arası korelasyonların görsel matrisi. Isı haritası (heatmap) ile diversifikasyon analizi. |
| 15 | **Up / Down Capture Ratios** | Piyasa yükselirken ve düşerken fonun asimetrik performansı. Up capture > down capture olması istenir. |
| 16 | **Dövize Göre Düzeltilmiş Getiri** | Yabancı varlık tutan fonların getirisi TRY cinsinden gösteriliyor. Kur etkisi ve varlık getirisi ayrıştırılmalı. USD/TRY, EUR/TRY bazlı düzeltilmiş getiriler. Türkiye'de FX önemli bir faktör. |

### Veri (API altyapısı var, UI eksik)

| # | Özellik | Açıklama |
|---|---|---|
| 17 | **Fon Portföy Dağılımı (Varlık Kırılımı)** | `fon_portfoy_dagilimi()` API endpoint'i tamamen implemente edilmiş, 60+ varlık kategorisi (Hisse Senedi, Devlet Tahvili, Ters Repo, Özel Sektör Tahvili, Eurobond, Kıymetli Maden vb.) Türkçe label'larıyla tanımlı. **Veri mevcut, sadece UI gösterimi yok.** |
| 18 | **Yönetim Ücretleri (Expense Ratio)** | `fonlar_yonetim_ucretleri()` API çalışıyor. Fonlar arası maliyet karşılaştırması yapılamıyor. Portföy yöneticisi için maliyet analizi olmazsa olmaz. |
| 19 | **Fon Büyüklüğü / AUM** | `fonlar_buyukluk()` API çalışıyor. Fon büyüklüğüne göre filtreleme, AUM trend analizi yok. Likidite riski değerlendirilemiyor. |
| 20 | **Kurucu / Fon Şirketi Karşılaştırması** | `kurucuKod` alanı API'da mevcut ama filtreleme/gruplama yok. "Ak Portföy vs İş Portföy vs Yapı Kredi Portföy" gibi şirket bazında karşılaştırma yapılamıyor. |

### Teknik Altyapı

| # | Özellik | Açıklama |
|---|---|---|
| 21 | **Kullanıcı Kimlik Doğrulama (Auth)** | Login/kayıt sistemi yok. Rol bazlı yetkilendirme (admin, analist, müşteri) yok. Çok kullanıcılı profesyonel kullanım imkansız. |
| 22 | **Veritabanı (Persistent Storage)** | Sadece Parquet dosya cache var (uçucu, sorgulanamaz). PostgreSQL / SQLite ile fon verisi, kullanıcı verisi, analiz geçmişi, favoriler kalıcı saklanmalı. |
| 23 | **REST API Katmanı** | Tüm TEFAS çağrıları doğrudan Dash callback'lerinden yapılıyor. Harici sistemlerin (risk sistemi, raporlama, CRM) FAS verisine erişebilmesi için headless API katmanı gerekli. |
| 24 | **Test Kapsamı** | Sadece `test_metrics.py` (20 test) var. Sayfalar, fetcher'lar, chart'lar, cache, scraper'lar, TLREF, KYD, Yahoo, KAP — hiçbirinin testi yok. Coverage ~%5. |
| 25 | **Enflasyona Göre Düzeltilmiş Getiri (Reel Getiri)** | TÜFE'ye göre reel getiri hesaplanmıyor. Türkiye'de yüksek enflasyon ortamında nominal getiriler yanıltıcı. TÜİK TÜFE verisi entegre edilmeli. |

---

## MEDIUM — Orta Öncelikli Eksikler (22 adet)

### Risk & Stres Analizi

| # | Özellik | Açıklama |
|---|---|---|
| 26 | **Stres Testi / Senaryo Analizi** | Tarihi kriz senaryoları: 2008 küresel krizi, 2018 Türkiye krizi, COVID 2020, 2023 seçim sonrası. Hipotetik şoklar: faiz ±500bps, USD/TRY ±%20, BIST ±%30. Portföy üzerindeki etki simülasyonu. |
| 27 | **Monte Carlo Simülasyonu** | İleriye dönük getiri dağılımı projeksiyonu. Monte Carlo VaR (şu an sadece tarihi VaR var). Emeklilik/birikim projeksiyonu. |
| 28 | **Detaylı Drawdown Analizi** | Ortalama drawdown, drawdown süresi (ay), drawdown frekansı, toparlanma süresi, Pain Index, Ulcer Index. Şu an sadece Max Drawdown var. |
| 29 | **Skewness / Kurtosis** | Getiri dağılımının çarpıklık ve basıklık ölçüleri. Normal dağılım varsayımının geçerliliğini test etmek için. |

### Veri & Veri Kaynakları

| # | Özellik | Açıklama |
|---|---|---|
| 30 | **İşlem Hacmi / Fund Flow** | `islem_hacmi()`, `fon_bazli_islem_hacmi()` API verileri UI'da yok. Hangi fonlara para girişi/çıkışı var, trend analizi. |
| 31 | **TEFAS Duyuruları** | `duyurular()` API çalışıyor. Fon doküman değişiklikleri, yönetici değişiklikleri, birleşme/bölünme olayları kullanıcıya gösterilmiyor. |
| 32 | **Fon Yaşı / İhraç Tarihi** | Fonun kuruluş tarihi, minimum ilk yatırım tutarı, nitelikli yatırımcı kısıtı. Survivorship bias farkındalığı için fon yaşı kritik. |
| 33 | **Kategori İçi Yüzdelik Sıralama (Percentile Rank)** | Fon Bulucu top 10 gösteriyor ama fonun kendi kategorisinde yüzde kaçıncı dilimde olduğu bilgisi yok (örn. "Bu fon kategorisinde top %15'te"). |
| 34 | **Time-Weighted vs Money-Weighted Return** | Şu an sadece TWR (geometrik bağlama). Nakit akışlı portföyler için MWR / IRR hesaplaması gerekli. |
| 35 | **Katılım (İslami) Fon Ayrımı** | KATLM benchmark'ı tanımlı ama fon listesinde İslami/konvansiyonel ayrımı yok. Katılım endeksine uygunluk filtresi. |
| 36 | **Serbest Fon (Hedge Fund Benzeri) Özel İşlem** | Serbest fonların benchmark'ı yok, yüksek minimum yatırım (genelde 1M+ TL), nitelikli yatırımcı şartı. Özel gösterim ve uyarılar gerekli. |
| 37 | **Net-of-Tax (Stopaj Sonrası) Getiri** | Fon türüne ve elde tutma süresine göre stopaj oranı değişiyor (%0 BES, %7.5-10 diğer). Vergi sonrası net getiri hesaplanmıyor. |
| 38 | **Forex Veri Kaynağı** | USD/TRY, EUR/TRY için TCMB veya Yahoo'dan özel veri çekme yok. Kur ayrıştırması için gerekli. |

### UX & Kullanıcı Deneyimi

| # | Özellik | Açıklama |
|---|---|---|
| 39 | **Kayıtlı İzlenecekler / Favoriler (Server-side)** | Favoriler sadece `localStorage`'da (tarayıcıya özel, cihazlar arası taşınmaz). Kullanıcı hesabına bağlı kalıcı izleme listeleri gerekli. |
| 40 | **E-posta Uyarıları / Bildirimler** | NAV eşik değeri, fiyat değişimi, benchmark'tan sapma, drawdown limiti gibi olaylarda e-posta bildirimi. |
| 41 | **Tam Metin / Fuzzy Fon Arama** | Sadece fon kodu veya tam unvan eşleşmesi. "teknoloji", "sağlık", "eurobond" gibi anahtar kelimelerle arama yok. |
| 42 | **Mobil Responsive Tasarım** | Sidebar `md` altında gizleniyor ama hamburger menü veya mobil navigasyon yok. |
| 43 | **Dashboard / Piyasa Özeti** | Ana sayfada tek bakışta piyasa özeti, en çok yükselen/düşen fonlar, günlük işlem hacmi, benchmark performans özeti widget'ları. |
| 44 | **Risk Budgeting / Risk Parity** | Eşit risk katkılı (ERC) portföy, risk bütçeleme optimizasyonu. |
| 45 | **Hedef Bazlı Planlama (Goal-Based)** | Hedef getiri veya hedef tarih için gerekli portföy yapısı önerisi. Emeklilik/birikim hedef simülasyonu. |

### DevOps & Operasyon

| # | Özellik | Açıklama |
|---|---|---|
| 46 | **Docker Desteği** | `Dockerfile` ve `docker-compose.yml` yok. Manuel `venv` + `pip install` kurulumu. |
| 47 | **CI/CD Pipeline** | GitHub Actions veya benzeri CI/CD yok. Otomatik test, lint, deploy pipeline'ı. |
| 48 | **Rate Limit Queue (Gelişmiş)** | TEFAS API rate limit yönetimi sadece `time.sleep()` ile inline. Retry + exponential backoff + persistent queue yok. |

---

## LOW — Düşük Öncelikli Eksikler (19 adet)

### Ek Metrikler ve Oranlar

| # | Özellik | Açıklama |
|---|---|---|
| 49 | **Calmar Oranı** | Yıllık getiri / Max Drawdown. Drawdown bazlı risk-ayarlı getiri. |
| 50 | **Sterling Oranı** | Yıllık getiri / (Ortalama Drawdown + %10). |
| 51 | **Burke Oranı** | Getiri / (drawdown kareleri toplamının karekökü). |
| 52 | **Omega Oranı** | Tam getiri dağılımını dikkate alan risk-ödül metriği. |
| 53 | **Batting Average** | Fonun benchmark'ı yendiği dönemlerin yüzdesi. |
| 54 | **Active Share** | Fon portföyünün benchmark'tan ne kadar farklılaştığı. |
| 55 | **M² / Modigliani Ölçüsü** | Riske göre düzeltilmiş getiri karşılaştırması. |

### Detaylı Analizler

| # | Özellik | Açıklama |
|---|---|---|
| 56 | **Tracking Error Dekompozisyonu** | Sistematik vs idiosinkratik TE ayrıştırması. |
| 57 | **Cointegration / Durağanlık Testleri** | Pair trading, spread analizi için ADF testi, Johansen testi. |
| 58 | **BYF (ETF) Ayrımı** | BYF'lar borsada gün içi işlem görür, TEFAS sadece gün sonu NAV verir. ETF'lere özel işlem hacmi, spread, prim/iskonto bilgisi. |
| 59 | **ESG / Sürdürülebilirlik Fonları** | "Sürdürülebilirlik Fonu" kategorisi mevcut, ESG skoru veya filtresi yok. |
| 60 | **Sektör / Market Cap Kırılımı** | Hisse senedi fonları için large/mid/small cap dağılımı, sektör ağırlıkları. |
| 61 | **Makroekonomik Veri Entegrasyonu** | TÜFE, GSYH, cari açık, CDS spread, TCMB politika faizi verileri. |

### UX / Erişilebilirlik

| # | Özellik | Açıklama |
|---|---|---|
| 62 | **"Benzer Fon" Keşif / Öneri Motoru** | Stil, kategori ve getiri benzerliğine göre benzer fon önerileri. |
| 63 | **Klavye Kısayolları** | Sayfalar arası gezinme, sık kullanılan işlemler için kısayollar. |
| 64 | **Erişilebilirlik (WCAG / ARIA)** | Ekran okuyucu desteği, yeterli kontrast oranları, klavye navigasyonu. |
| 65 | **Onboarding / Rehberli Tur** | İlk kullanım için adım adım tanıtım turu, contextual yardım. |

### Teknik

| # | Özellik | Açıklama |
|---|---|---|
| 66 | **WebSocket / Gerçek Zamanlı Veri** | Anlık fiyat güncellemesi, push notification. |
| 67 | **Çevresel Değişken (.env) Desteği** | `os.environ.get()` ile debug flag'leri okunuyor ama `.env` dosyası ve python-dotenv entegrasyonu yok. |
| 68 | **Log Rotasyonu** | `logs/fas.log` sınırsız büyüyor, `RotatingFileHandler` yok. |

---

## Low-Hanging Fruit — Verisi Hazır, Sadece UI Eksik

Bu özelliklerin **TEFAS API'den verisi zaten çekiliyor veya tek bir parametre değişikliği ile çekilebilir durumda.** Backend geliştirmesi gerekmeden sadece frontend/UI eklemesi yeterli:

| # | Özellik | API / Veri Kaynağı | Durum |
|---|---|---|---|
| 1 | **Fon Portföy Dağılımı** | `fon_portfoy_dagilimi()` → `_tefas_api.py:469` | API hazır, 60+ label tanımlı |
| 2 | **Yönetim Ücretleri** | `fonlar_yonetim_ucretleri()` → `_tefas_api.py:338` | API hazır |
| 3 | **Fon Büyüklüğü (AUM)** | `fonlar_buyukluk()` → `_tefas_api.py:384` | API hazır |
| 4 | **İşlem Hacimleri** | `islem_hacmi()`, `fon_bazli_islem_hacmi()` → `_tefas_api.py:412,431` | API hazır |
| 5 | **TEFAS Duyuruları** | `duyurular()` → `_tefas_api.py:520` | API hazır |
| 6 | **BES Fon Verisi** | `fonTipi` parametresini `"YAT"` → `"BES"` değiştir | Tek satırlık değişiklik |
| 7 | **Kategori Sıralaması** | `fon_profil_detay()` → `_tefas_api.py:535` | API hazır |
| 8 | **Kurucu Bazlı Filtre** | `kurucuKod` / `kurucu` alanları API yanıtında mevcut | Veri mevcut, filtre UI'ı yok |

---

## Özet İstatistikler

| Öncelik | Adet |
|---|---|
| **CRITICAL** | 6 |
| **HIGH** | 19 |
| **MEDIUM** | 22 |
| **LOW** | 19 |
| **Low-Hanging Fruit** | 8 |
| **TOPLAM** | **66** |
