# Fon Analiz Sistemi — Proje Planı

Bu doküman, “fas” (Fon Analiz Sistemi) projesinin uçtan uca geliştirme planını ve teslimat kapsamını tanımlar.

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
- Benchmark’a göre göreli performans ve katkı analizi
- Tekil fon raporu + fonlar arası karşılaştırma raporu

## Varsayımlar ve Kararlar

- Getiriler için varsayılan: log getiri veya basit getiri (projede standartlaştırılacak)
- Frekans: günlük veri → aylık/haftalık agregasyon opsiyonel
- Risk-free oran dönüştürme: yıllık → günlük eşdeğer (açık formül ile)
- Zaman aralığı ve veri temizleme (eksik günler, tatiller) tutarlı bir kural seti ile ele alınacak

## İş Paketleri (2 Haftalık Takvim)

### 1. Gün — Fon fiyat verisinin çekilmesi

- Kaynak(lar) ve erişim yöntemi belirleme (API / scraping / dosya)
- Tek fon için örnek veri indirme, tarih-fiyat serisi standardı

### 2. Gün — Risksiz getiri verisinin çekilmesi

- Veri kaynağı belirleme (faiz/bono gösterge vb.)
- Yıllık oranların günlük/aylık eşdeğer dönüşümü

### 3. Gün — Benchmark endeks verisinin çekilmesi

- Endeks seçimi ve veri temini
- Fon ve benchmark takvimlerini hizalama

### 4. Gün — Fon performans analizi

- Getiri hesapları (günlük ve kümülatif)
- Görselleştirme: fiyat, kümülatif getiri, dönemsel getiri dağılımı

### 5. Gün — Benchmark performans analizi

- Benchmark getiri serisi ve kümülatif performans
- Fon vs benchmark karşılaştırmalı grafikler

### 6. Gün — Risk analizi

- Volatilite, aşağı yönlü volatilite
- Maksimum düşüş ve toparlanma süresi (opsiyonel)
- (Opsiyonel) VaR/CVaR

### 7. Gün — Getiri & risk karşılaştırması

- Risk-getiri saçılım grafikleri
- Fon kategorisine göre kıyas (varsa)

### 8. Gün — Sharpe ve Sortino

- Risksiz getiri entegrasyonu
- Sharpe/Sortino hesapları ve yorumlama şablonu

### 9. Gün — Treynor oranı

- Beta hesap altyapısı (regresyon)
- Treynor metrikleri ve raporlama

### 10. Gün — Alpha ve Beta

- CAPM regresyonu (fon getirisi ~ benchmark getirisi)
- Alpha, beta, p-değerleri (opsiyonel)

### 11. Gün — R² ve Information Ratio

- Tracking error ve active return
- IR ve R² hesapları

### 12. Gün — Performans analiz raporu

- Rapor şablonu: özet, metrikler, grafikler, yorum
- Tek fon raporu çıktısı (PDF/HTML/Markdown)

### 13. Gün — Sunum ve değerlendirme

- Bulguların kontrol listesi (tutarlılık, veri kayması, uç değer)
- Son rötuşlar

### 14. Gün — Fon karşılaştırma analizi

- Çoklu fon pipeline’ı (aynı metrik seti)
- Sıralama tabloları ve filtreler

### 15. Gün — Karşılaştırma raporu

- Karşılaştırma raporu çıktısı
- Reprodüksiyon talimatları (nasıl çalıştırılır)

## Eksiklerin Tamamlanması İçin Kontrol Listesi

- [x] Veri kaynakları ve erişim yöntemleri netleşti
- [x] Tarih hizalama ve eksik veri politikası yazıldı (`docs/veri_politikasi.md`)
- [x] Risksiz oran dönüşüm formülü standardize edildi
- [x] Getiri tanımı (log/basit) proje genelinde tekleştirildi
- [x] Metriklerin formülleri ve birimleri dokümante edildi (`docs/metrik_formulleri.md`)
- [x] Rapor formatı ve çıktı hedefi (PDF/HTML) belirlendi

