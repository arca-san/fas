# Fon Analiz Sistemi — Proje Planı

## Amaç

- Fonların tarihsel performansını analiz etmek
- Benchmark ve risksiz getiri ile karşılaştırmak
- Risk ölçümlerini ve risk-ayarlı performans metriklerini hesaplamak
- Sonuçları rapor ve görsellerle sunmak

## Kapsam

### Girdiler (Veri)

- Fon fiyatları / birim pay değeri (NAV) veya günlük fiyat serisi
- Risksiz getiri oranı (TL için kısa vadeli faiz / gösterge)
- Benchmark endeks fiyat serisi (ör. BIST, TEFAS kıyas endeksi vb.)
- (Opsiyonel) Fonun gider oranı, yönetim ücreti, kategori, strateji bilgileri

### Çıktılar

- Dönemsel getiri (günlük/haftalık/aylık), kümülatif getiri
- Volatilite (standart sapma), aşağı yönlü volatilite
- Maksimum düşüş (max drawdown), VaR/CVaR (opsiyonel)
- Beta, alpha, R²
- Sharpe, Sortino, Treynor, Information Ratio
- Benchmark'a göre göreli performans ve katkı analizi
- Tekil fon raporu + fonlar arası karşılaştırma raporu

## Varsayımlar ve Kararlar

- Getiriler için varsayılan: log getiri veya basit getiri (projede standartlaştırılacak)
- Frekans: günlük veri → aylık/haftalık agregasyon opsiyonel
- Risk-free oran dönüştürme: yıllık → günlük eşdeğer (açık formül ile)
- Zaman aralığı ve veri temizleme (eksik günler, tatiller) tutarlı bir kural seti ile ele alınacak

## İş Paketleri

### 1. PDF Rapor — GTK Bağımlılığını Kaldır / Alternatif Çözüm
WeasyPrint Windows'ta GTK runtime gerektiriyor. Her makinede çalışan bir PDF çözümüne geçilmeli (pdfkit, reportlab, vs.) veya GTK kurulumu otomatikleştirilmeli.

### 2. Veri Kaynağı Sağlamlığı
- TEFAS API değişikliklerine karşı izleme ve hata yönetimi
- KYD verileri için fallback mekanizması
- Önbellek stratejisinin iyileştirilmesi

### 3. Hata Yönetimi ve Kullanıcı Geri Bildirimi
- Tüm callback'lerde try/except ve kullanıcıya anlamlı hata mesajı
- Loading state'ler (Dash'te loading spinner vb.)
- Uzun süren işlemler için progress feedback

### 4. Test ve Kalite
- Metrik hesaplarının birim testleri (pytest)
- Edge case'ler: tek fon, boş veri, eksik tarih aralığı
- CI pipeline (GitHub Actions)

### 5. UI/UX İyileştirmeleri
- Mobil uyum (responsive tablo/grafik)
- Tema desteği (açık/koyu)
- Favori fon listesi ve kalıcılık

### 6. Performans
- Büyük portföylerde sayfa yüklenme süresinin iyileştirilmesi
- Veri ön yükleme / lazy loading
- Gereksiz callback tetiklemelerinin azaltılması
