# Metrik Formülleri

Tüm metrikler `components/metrics.py`'de hesaplanır.

| Metrik | Formül | Açıklama |
|--------|--------|----------|
| **Toplam Getiri** | `(P_t / P_0 - 1) × 100` | Dönem başından sonuna yüzde değişim |
| **Yıllıklandırılmış Getiri** | `(∏(1 + R_i))^(252/n) - 1` | Bileşik yıllık büyüme oranı |
| **Volatilite (Yıllık)** | `σ(R) × √252` | Günlük getiri standart sapması, yıllık |
| **Aşağı Yönlü Volatilite** | `σ(R⁻) × √252` | Sadece negatif getirilerin volatilitesi |
| **Maksimum Düşüş** | `min((Cum - Peak)/Peak) × 100` | En yüksekten en düşüğe kayıp (%) |
| **VaR (%95)** | `percentile(R, 5%) × 100` | Tarihsel %95 güven düzeyinde maksimum kayıp |
| **CVaR (%95)** | `mean(R ≤ VaR) × 100` | VaR'ı aşan kayıpların ortalaması |
| **Sharpe Oranı** | `(R_p - R_f) / σ_p` | Birim risk başına fazla getiri |
| **Sortino Oranı** | `(R_p - R_f) / σ_d` | Aşağı yönlü riske göre düzeltilmiş getiri |
| **Beta** | `Cov(R_p, R_m) / Var(R_m)` | Sistematik risk duyarlılığı |
| **Treynor Oranı** | `(R_p - R_f) / β` | Sistematik risk başına fazla getiri |
| **Alpha (Jensen)** | `R_p - [R_f + β × (R_m - R_f)]` | Beklenenin üzerinde getiri (yetenek göstergesi) |
| **R²** | `ρ(R_p, R_m)²` | Benchmark tarafından açıklanan varyans oranı |
| **Information Ratio** | `(R_p - R_m) / TE` | Aktif getiri / Tracking error |

**Değişkenler:**
- `R_p`: Fon günlük getirisi
- `R_m`: Benchmark günlük getirisi
- `R_f`: Risksiz getiri (günlük)
- `σ_p`: Günlük getiri standart sapması
- `σ_d`: Negatif getirilerin standart sapması
- `TE`: Tracking error (fazla getiri standart sapması)

**Varsayımlar:**
- Yılda 252 işlem günü
- Basit getiri (log getiri değil)
- Tarihsel VaR/CVaR (parametrik değil)
