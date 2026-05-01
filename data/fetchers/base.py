#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AbstractFetcher — tüm veri çekici modüller bu arayüzü uygular.
Teknik borcu önlemek için veri kaynağı detayları bu katmanda gizlenir.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import date

import pandas as pd


class AbstractFetcher(ABC):
    """
    Fon, benchmark ve risk-free verileri için soyut temel sınıf.
    """

    @abstractmethod
    def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """
        Belirtilen sembol için tarihsel fiyat verisini döndürür.

        Returns
        -------
        pd.DataFrame
            En az 'tarih' ve 'fiyat' sütunları içermeli.
        """
        ...

    @abstractmethod
    def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """
        Sembol/kod araması yapar.

        Returns
        -------
        List[Dict[str, Any]]
            [{'kod': ..., 'unvan': ..., 'tip': ...}, ...]
        """
        ...

    @abstractmethod
    def list_available_symbols(self) -> List[Dict[str, Any]]:
        """
        Kullanılabilir tüm sembolleri listeler.
        """
        ...
