#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeasyPrint runtime bootstrap.

Windows needs the GTK DLL directory to be visible to the running Python
process. This module wires the local .gtk runtime into PATH,
WEASYPRINT_DLL_DIRECTORIES and os.add_dll_directory before WeasyPrint is used.
"""

from __future__ import annotations

import os
import subprocess
import sys
from io import StringIO
from pathlib import Path
from typing import Optional, Type

from config.settings import PROJECT_ROOT


GTK_DLL_NAME = "libgobject-2.0-0.dll"
LOCAL_GTK_BIN = PROJECT_ROOT / ".gtk" / "bin"
INSTALL_GTK_SCRIPT = PROJECT_ROOT / "scripts" / "install_gtk.ps1"
_DLL_DIRECTORY_HANDLES = []
_HTML_CLASS: Optional[Type] = None


def _prepend_env_path(name: str, path: Path) -> None:
    value = str(path)
    current = os.environ.get(name, "")
    parts = [part for part in current.split(os.pathsep) if part]
    if value not in parts:
        os.environ[name] = os.pathsep.join([value, *parts])


def _register_windows_dll_dir(path: Path) -> None:
    _prepend_env_path("PATH", path)
    _prepend_env_path("WEASYPRINT_DLL_DIRECTORIES", path)

    add_dll_directory = getattr(os, "add_dll_directory", None)
    if add_dll_directory is not None:
        handle = add_dll_directory(str(path))
        _DLL_DIRECTORY_HANDLES.append(handle)


def _run_gtk_installer() -> Path:
    if not INSTALL_GTK_SCRIPT.exists():
        raise RuntimeError(f"GTK kurulum scripti bulunamadi: {INSTALL_GTK_SCRIPT}")

    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(INSTALL_GTK_SCRIPT),
        ],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        output = (result.stdout + "\n" + result.stderr).strip()
        raise RuntimeError(f"GTK runtime kurulamadi. {output}")

    for line in reversed(result.stdout.splitlines()):
        candidate = Path(line.strip())
        if candidate.exists() and (candidate / GTK_DLL_NAME).exists():
            return candidate

    if (LOCAL_GTK_BIN / GTK_DLL_NAME).exists():
        return LOCAL_GTK_BIN

    raise RuntimeError("GTK installer basarili dondu ama libgobject DLL bulunamadi.")


def _ensure_windows_gtk() -> None:
    if (LOCAL_GTK_BIN / GTK_DLL_NAME).exists():
        gtk_bin = LOCAL_GTK_BIN
    else:
        gtk_bin = _run_gtk_installer()

    _register_windows_dll_dir(gtk_bin)


def _load_and_test_html() -> Type:
    from weasyprint import HTML

    HTML(file_obj=StringIO("<html><body><p>ok</p></body></html>")).write_pdf()
    return HTML


def ensure_weasyprint_ready() -> Type:
    """Return weasyprint.HTML after validating the runtime can write a PDF."""
    global _HTML_CLASS

    if _HTML_CLASS is not None:
        return _HTML_CLASS

    if sys.platform == "darwin":
        os.environ.setdefault("DYLD_FALLBACK_LIBRARY_PATH", "/opt/homebrew/lib")
    elif sys.platform == "win32":
        if (LOCAL_GTK_BIN / GTK_DLL_NAME).exists():
            _register_windows_dll_dir(LOCAL_GTK_BIN)

    try:
        _HTML_CLASS = _load_and_test_html()
        return _HTML_CLASS
    except Exception as exc:
        first_error = exc

    if sys.platform == "win32":
        try:
            _ensure_windows_gtk()
            _HTML_CLASS = _load_and_test_html()
            return _HTML_CLASS
        except Exception as exc:
            raise RuntimeError(
                f"WeasyPrint PDF runtime hazir degil: {exc}. Ilk hata: {first_error}"
            ) from exc

    raise RuntimeError(f"WeasyPrint PDF runtime hazir degil: {first_error}") from first_error
