#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Veri modelleri — Pydantic ile validasyon ve tip güvenliği.
"""

from datetime import date
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field, ConfigDict


class PricePoint(BaseModel):
    """Tekil tarih-fiyat noktası."""
    model_config = ConfigDict(populate_by_name=True)

    tarih: date
    fiyat: float = Field(..., gt=0)


class FundData(BaseModel):
    """Ham fon verisi (TEFAS'tan çekildikten sonra)."""
    model_config = ConfigDict(populate_by_name=True)

    fon_kodu: str = Field(..., alias="fonKodu")
    fon_unvan: Optional[str] = Field(None, alias="fonUnvan")
    fiyat_verisi: List[PricePoint] = Field(default_factory=list)
    kaynak: str = "tefas"
    meta: Dict[str, Any] = Field(default_factory=dict)


class BenchmarkData(BaseModel):
    """Benchmark verisi."""
    model_config = ConfigDict(populate_by_name=True)

    sembol: str
    ad: str
    fiyat_verisi: List[PricePoint] = Field(default_factory=list)
    kaynak: str = "yfinance"  # veya tefas, csv, vb.


class RiskFreeData(BaseModel):
    """Risksiz getiri verisi (günlük oranlar)."""
    model_config = ConfigDict(populate_by_name=True)

    tarih: date
    gunluk_oran: float
    yillik_oran: float
    kaynak_aciklama: str


class MetricSet(BaseModel):
    """Bir fon için hesaplanmış tüm metrikler."""
    model_config = ConfigDict(populate_by_name=True)

    fon_kodu: str
    baslangic_tarihi: date
    bitis_tarihi: date
    gozlem_sayisi: int

    # Getiri
    toplam_getiri: float
    yilliklandirilmis_getiri: float
    gunluk_ortalama_getiri: float

    # Risk
    volatilite: float
    asagi_yonlu_volatilite: float
    maksimum_dusus: float
    var_95: Optional[float] = None
    cvar_95: Optional[float] = None

    # Regresyon
    beta: Optional[float] = None
    alpha: Optional[float] = None
    r_kare: Optional[float] = None

    # Rasyolar
    sharpe_orani: Optional[float] = None
    sortino_orani: Optional[float] = None
    treynor_orani: Optional[float] = None
    information_ratio: Optional[float] = None

    # Benchmark bilgisi
    benchmark_sembol: Optional[str] = None

    class Config:
        json_encoders = {date: lambda v: v.isoformat()}
