# Veri Politikası

## Veri Kaynakları

| Kaynak | Kapsam | Erişim Yöntemi |
|--------|--------|----------------|
| TEFAS | Fon fiyat/birim pay değeri | REST API + scraping |
| KYD (KAP) | Benchmark endeks verileri | REST API |
| TLREF | Risksiz getiri oranı | ZIP/CSV dosyası |

## Tarih Hizalama

Tüm fon ve benchmark verileri **tarih bazlı join** ile hizalanır. Eksik günler (tatil, hafta sonu) ileri doğru doldurulur (`ffill`). Hizalama yöntemi `CALENDAR_ALIGN_METHOD` ile `config/settings.py`'de kontrol edilir.

## Risksiz Oran Dönüşümü

- **Kaynak**: TLREF (Türk Lirası Referans Faiz Oranı)
- **Dönüşüm**: `daily_compound(oransal_faiz) -> yıllık faizi günlük bileşik getiriye çevirir`
- **Varsayılan yıllık**: %45 (`DEFAULT_RISK_FREE_ANNUAL = 0.45`)

## Getiri Tanımı

Proje genelinde **basit getiri** kullanılır (`pct_change`). Log getiri opsiyonu `RETURN_METHOD` ile kontrol edilir ancak mevcut sürümde basit getiri standarttır.

## Önbellekleme

- TEFAS ve KYD verileri `data/cache/` dizininde önbelleğe alınır
- Varsayılan TTL: 24 saat (`CACHE_TTL_HOURS = 24`)
- TLREF verisi anlık çekilir, önbelleklenmez
