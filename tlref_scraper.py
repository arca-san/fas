"""
TLREF Scraper & Dönüştürücü
=============================
Türk Lirası Gecelik Referans Faiz Oranı (TLREF) verisini çeker
ve yıllık oranları günlük/aylık/periyot eşdeğerlerine dönüştürür.

Kaynaklar:
  - CSV:  https://www.borsaistanbul.com/datum/tlreforani.csv
  - API:  https://www.borsaistanbul.com/bist-tlrefk.php
  - ZIP:  https://www.borsaistanbul.com/datum/TLREFORANI_D.zip
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import zipfile
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)
BASE_URL = "https://www.borsaistanbul.com"


class TLREFScraper:
    """TLREF verisini farklı kaynaklardan çeker."""

    CSV_URL = f"{BASE_URL}/datum/tlreforani.csv"
    API_URL = f"{BASE_URL}/bist-tlrefk.php"
    ZIP_URL = f"{BASE_URL}/datum/TLREFORANI_D.zip"
    ZIP_URL_MATRIS = f"{BASE_URL}/datum/TLREF_GETIRI_MATRISI.zip"

    def __init__(self, timeout: int = 30):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.timeout = timeout

    def from_csv(self) -> pd.DataFrame:
        """CSV'den TLREF verisini çeker.

        CSV formatı (semicolon-delimited):
          TARIH;AD;INGILIZCE ADI;KOD;ISIN;DEGER
        """
        resp = self.session.get(self.CSV_URL, timeout=self.timeout)
        resp.raise_for_status()
        content = resp.content.decode("utf-8-sig")

        reader = csv.DictReader(io.StringIO(content), delimiter=";")
        rows = []
        for row in reader:
            date_str = row.get("TARIH", "").strip()
            value_str = row.get("DEGER", "").strip()
            if not date_str or not value_str:
                continue
            try:
                date = datetime.strptime(date_str, "%d/%m/%Y")
                value = float(value_str)
                rows.append({"date": date, "value": value})
            except (ValueError, TypeError):
                continue

        df = pd.DataFrame(rows)
        if df.empty:
            raise ValueError("CSV'den veri okunamadı (beklenen kolonlar: TARIH, DEGER)")

        df = df.sort_values("date").reset_index(drop=True)
        return df

    def from_api(self, day: Optional[int] = None) -> pd.DataFrame:
        """API'den TLREF verisini çeker.

        GET /bist-tlrefk.php?op=fetchTlrefkData&dataType=TLREF&day={day}
        """
        params: Dict[str, str] = {
            "op": "fetchTlrefkData",
            "dataType": "TLREF",
        }
        if day is not None:
            params["day"] = str(day)

        resp = self.session.get(self.API_URL, params=params, timeout=self.timeout)
        resp.raise_for_status()
        payload = resp.json()

        if payload.get("status") != "success":
            raise ValueError(f"API hatası: {payload.get('message', 'bilinmeyen')}")

        data = payload.get("data", [])
        if not data:
            raise ValueError("API'den veri dönmedi")

        rows = []
        for item in data:
            try:
                date = datetime.strptime(item["date"], "%Y-%m-%d")
                value = float(item["clval"])
                rows.append({"date": date, "value": value})
            except (ValueError, TypeError, KeyError):
                continue

        df = pd.DataFrame(rows)
        if df.empty:
            raise ValueError("API'den geçerli veri okunamadı")

        df = df.sort_values("date").reset_index(drop=True)
        return df

    def from_zip(self) -> pd.DataFrame:
        """ZIP arşivinden tarihsel TLREF verisini çeker."""
        resp = self.session.get(self.ZIP_URL, timeout=self.timeout)
        resp.raise_for_status()

        rows = []
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            for name in zf.namelist():
                if not (name.endswith(".csv") or name.endswith(".CSV")):
                    continue
                content = zf.read(name).decode("utf-8-sig")
                reader = csv.DictReader(io.StringIO(content), delimiter=";")
                for row in reader:
                    date_str = row.get("TARIH", "").strip()
                    value_str = row.get("DEGER", "").strip()
                    if not date_str or not value_str:
                        continue
                    try:
                        date = datetime.strptime(date_str, "%d/%m/%Y")
                        value = float(value_str)
                        rows.append({"date": date, "value": value})
                    except (ValueError, TypeError):
                        continue

        df = pd.DataFrame(rows)
        if df.empty:
            raise ValueError("ZIP içinde geçerli CSV bulunamadı")

        df = df.sort_values("date").reset_index(drop=True)
        return df

    def fetch_yield_matrix(self) -> pd.DataFrame:
        """TLREF Getiri Matrisi'ni ZIP'den çeker (opsiyonel)."""
        resp = self.session.get(self.ZIP_URL_MATRIS, timeout=self.timeout)
        resp.raise_for_status()

        rows = []
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            for name in zf.namelist():
                if not (name.endswith(".csv") or name.endswith(".CSV")):
                    continue
                content = zf.read(name).decode("utf-8-sig")
                reader = csv.DictReader(io.StringIO(content), delimiter=";")
                for row in reader:
                    rows.append(row)

        return pd.DataFrame(rows)


class TLREFConverter:
    """Yıllık TLREF oranlarını günlük/aylık/periyot eşdeğerlerine çevirir.

    TLREF yıllık bileşik faiz oranıdır (ACT/365).

    Formüller (r = yıllık oran / 100, ondalık):
      Basit faiz:
        günlük = r / 365
        aylık  = r / 12
        N-gün  = r * N / 365
      Bileşik faiz:
        günlük = (1 + r)^(1/365) - 1
        aylık  = (1 + r)^(1/12) - 1
        N-gün  = (1 + r)^(N/365) - 1
    """

    @staticmethod
    def to_decimal(annual_pct: float) -> float:
        """Yüzdeyi ondalığa çevirir (örn. 39.99 -> 0.3999)."""
        return annual_pct / 100.0

    @staticmethod
    def to_percent(decimal: float) -> float:
        """Ondalığı yüzdeye çevirir (örn. 0.3999 -> 39.99)."""
        return decimal * 100.0

    @staticmethod
    def daily_simple(annual_pct: float) -> float:
        """Yıllık basit faiz -> günlük eşdeğer (% olarak)."""
        return annual_pct / 365.0

    @staticmethod
    def daily_compound(annual_pct: float) -> float:
        """Yıllık bileşik faiz -> günlük eşdeğer (% olarak)."""
        r = annual_pct / 100.0
        daily = (1.0 + r) ** (1.0 / 365.0) - 1.0
        return daily * 100.0

    @staticmethod
    def monthly_simple(annual_pct: float) -> float:
        """Yıllık basit faiz -> aylık eşdeğer (% olarak)."""
        return annual_pct / 12.0

    @staticmethod
    def monthly_compound(annual_pct: float) -> float:
        """Yıllık bileşik faiz -> aylık eşdeğer (% olarak)."""
        r = annual_pct / 100.0
        monthly = (1.0 + r) ** (1.0 / 12.0) - 1.0
        return monthly * 100.0

    @staticmethod
    def period_simple(annual_pct: float, days: int) -> float:
        """Yıllık basit faiz -> N günlük getiri (% olarak)."""
        return annual_pct * days / 365.0

    @staticmethod
    def period_compound(annual_pct: float, days: int) -> float:
        """Yıllık bileşik faiz -> N günlük getiri (% olarak)."""
        r = annual_pct / 100.0
        period_return = (1.0 + r) ** (days / 365.0) - 1.0
        return period_return * 100.0

    @classmethod
    def convert(
        cls,
        annual_pct: float,
        target: str = "daily",
        method: str = "compound",
        days: int = 90,
    ) -> float:
        """Genel dönüştürme fonksiyonu."""
        if method == "simple":
            if target == "daily":
                return cls.daily_simple(annual_pct)
            elif target == "monthly":
                return cls.monthly_simple(annual_pct)
            elif target == "period":
                return cls.period_simple(annual_pct, days)
            else:
                raise ValueError(f"Bilinmeyen hedef: {target}")
        elif method == "compound":
            if target == "daily":
                return cls.daily_compound(annual_pct)
            elif target == "monthly":
                return cls.monthly_compound(annual_pct)
            elif target == "period":
                return cls.period_compound(annual_pct, days)
            else:
                raise ValueError(f"Bilinmeyen hedef: {target}")
        else:
            raise ValueError(f"Bilinmeyen yöntem: {method}")

    @classmethod
    def convert_df(
        cls,
        df: pd.DataFrame,
        target: str = "daily",
        method: str = "compound",
        days: int = 90,
    ) -> pd.DataFrame:
        """DataFrame'deki tüm değerleri dönüştürür."""
        result = df.copy()
        result["converted"] = result["value"].apply(
            lambda v: cls.convert(v, target, method, days)
        )
        result["value_pct"] = result["value"] / 100.0

        label_map = {
            "daily": "Günlük Eşdeğer (%)",
            "monthly": "Aylık Eşdeğer (%)",
            "period": f"{days} Günlük Getiri (%)",
        }
        method_label = "Basit" if method == "simple" else "Bileşik"
        suffix = f"{method_label} - {label_map.get(target, target)}"

        result = result.rename(columns={"converted": suffix})
        return result


class TLREFReport:
    """TLREF verisini raporlar."""

    @staticmethod
    def print_summary(df: pd.DataFrame) -> None:
        """DataFrame ozetini yazdirir."""
        if df.empty:
            print("  Veri yok.")
            return

        print(f"  Toplam kayit: {len(df)}")
        print(f"  Tarih araligi: {df['date'].min().date()} - {df['date'].max().date()}")
        print(f"  Min TLREF: {df['value'].min():.4f}%")
        print(f"  Max TLREF: {df['value'].max():.4f}%")
        print(f"  Ortalama:  {df['value'].mean():.4f}%")
        print(f"  Son TLREF: {df['value'].iloc[-1]:.4f}%")

    @staticmethod
    def print_table(df: pd.DataFrame, max_rows: int = 20) -> None:
        """Tablo goruntusu yazdirir."""
        if df.empty:
            print("  Veri yok.")
            return

        display = df.tail(max_rows).copy()
        date_col = display["date"].dt.strftime("%d/%m/%Y")
        display.insert(0, "Tarih", date_col)

        value_cols = [c for c in display.columns if c not in ("date", "Tarih")]
        formatted = display[["Tarih"] + value_cols].copy()

        for col in value_cols:
            formatted[col] = formatted[col].apply(
                lambda x: f"{x:.6f}" if isinstance(x, (int, float)) else x
            )

        sep = "-" * 90
        print(sep)
        header = " | ".join(str(c).ljust(18) for c in formatted.columns)
        print(f"  {header}")
        print(sep)
        for _, row in formatted.iterrows():
            vals = " | ".join(str(v).ljust(18) for v in row)
            print(f"  {vals}")
        print(sep)
        print(f"  ... son {max_rows} kayit gosteriliyor (toplam {len(df)})")

    @staticmethod
    def export_csv(df: pd.DataFrame, filepath: str) -> str:
        """DataFrame'i CSV'ye aktarir."""
        out = df.copy()
        out["date"] = out["date"].dt.strftime("%d/%m/%Y")
        out.to_csv(filepath, sep=";", index=False, encoding="utf-8-sig")
        return filepath


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Komut satiri argumanlarini ayristirir."""
    parser = argparse.ArgumentParser(
        description="TLREF Scraper & Donusturucu",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ornek:\n"
            "  %(prog)s --source csv\n"
            "  %(prog)s --source csv --convert daily --method compound\n"
            "  %(prog)s --source csv --convert monthly --method simple\n"
            "  %(prog)s --source api --convert period --days 90 --export tlref_period.csv\n"
        ),
    )
    parser.add_argument(
        "--source",
        choices=["csv", "api", "zip"],
        default="csv",
        help="Veri kaynagi (varsayilan: csv)",
    )
    parser.add_argument(
        "--convert",
        choices=["daily", "monthly", "period", "none"],
        default="daily",
        help="Donusum hedefi (varsayilan: daily)",
    )
    parser.add_argument(
        "--method",
        choices=["simple", "compound"],
        default="compound",
        help="Faiz yontemi (varsayilan: compound)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Period donusumunde gun sayisi (varsayilan: 90)",
    )
    parser.add_argument(
        "--api-days",
        type=int,
        default=None,
        help="API day parametresi (None = tumu, orn: 3650 = 10 yil)",
    )
    parser.add_argument(
        "--export",
        type=str,
        default=None,
        help="CSV'ye aktar (dosya yolu)",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=20,
        help="Tablo satir sayisi (varsayilan: 20)",
    )
    parser.add_argument(
        "--no-table",
        action="store_true",
        help="Tabloyu gizle",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """Ana CLI giris noktasi."""
    args = parse_args(argv)

    try:
        scraper = TLREFScraper()

        source_label = {"csv": "CSV", "api": "API", "zip": "ZIP"}
        print(f"\n=== TLREF Scraper ===")
        print(f"  Kaynak: {source_label.get(args.source, args.source)}")

        if args.source == "csv":
            df = scraper.from_csv()
        elif args.source == "api":
            df = scraper.from_api(day=args.api_days)
        elif args.source == "zip":
            df = scraper.from_zip()
        else:
            raise ValueError(f"Bilinmeyen kaynak: {args.source}")

        print(f"  Veri: {len(df)} kayit bulundu")

        if args.convert != "none":
            df = TLREFConverter.convert_df(
                df, target=args.convert, method=args.method, days=args.days
            )
            method_label = "Basit" if args.method == "simple" else "Bilesik"
            target_labels = {
                "daily": "Gunluk",
                "monthly": "Aylik",
                "period": f"{args.days} Gunluk",
            }
            print(
                f"  Donusum: Yillik -> {target_labels[args.convert]} ({method_label} Faiz)"
            )

        print()
        TLREFReport.print_summary(df)
        print()

        if not args.no_table:
            TLREFReport.print_table(df, max_rows=args.rows)

        if args.export:
            path = TLREFReport.export_csv(df, args.export)
            print(f"\n  CSV'ye aktarildi: {path}")

        return 0

    except requests.exceptions.RequestException as e:
        print(f"\n  Istek hatasi: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"\n  JSON cozumleme hatasi: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"\n  Veri hatasi: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n  Beklenmeyen hata: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

