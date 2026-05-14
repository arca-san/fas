#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Startup auto-update helper.

Uses git when possible and only checks origin/master. Installations without
git fall back to downloading master.zip and copying project files while
preserving local runtime folders.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


REPO_OWNER = "arca-san"
REPO_NAME = "fas"
REMOTE = "origin"
MASTER_BRANCH = "master"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MASTER_ZIP_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/archive/refs/heads/{MASTER_BRANCH}.zip"

PRESERVED_DIRS = {".git", ".venv", ".gtk", "env", "venv", "logs", "__pycache__"}
PRESERVED_FILE_SUFFIXES = {".pyc", ".pyo", ".parquet", ".log"}


def log(message: str) -> None:
    print(f"[update] {message}", flush=True)


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def has_git() -> bool:
    return shutil.which("git") is not None


def is_git_repo() -> bool:
    if not (PROJECT_ROOT / ".git").exists():
        return False
    result = run_git(["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip() == "true"


def current_branch() -> str | None:
    result = run_git(["branch", "--show-current"])
    if result.returncode != 0:
        return None
    branch = result.stdout.strip()
    return branch or None


def is_worktree_clean() -> bool:
    result = run_git(["status", "--porcelain"])
    return result.returncode == 0 and not result.stdout.strip()


def is_ancestor(ancestor: str, descendant: str) -> bool:
    result = run_git(["merge-base", "--is-ancestor", ancestor, descendant])
    return result.returncode == 0


def git_update() -> None:
    branch = current_branch()
    if branch not in {"master", "dev"}:
        log(f"Branch '{branch or 'detached'}' icin otomatik update atlandi.")
        return

    log("origin/master kontrol ediliyor...")
    fetch = run_git(["fetch", REMOTE, f"{MASTER_BRANCH}:refs/remotes/{REMOTE}/{MASTER_BRANCH}"])
    if fetch.returncode != 0:
        log("Remote master kontrol edilemedi; uygulama mevcut surumle acilacak.")
        return

    remote_master = f"{REMOTE}/{MASTER_BRANCH}"
    if is_ancestor(remote_master, "HEAD"):
        log("Guncelleme yok.")
        return

    if not is_worktree_clean():
        log("Yerel degisiklikler var; otomatik update atlandi.")
        return

    if branch == "master":
        log("Master branch fast-forward update aliyor...")
        merge = run_git(["merge", "--ff-only", remote_master])
    else:
        log("Dev branch korunarak origin/master merge ediliyor...")
        merge = run_git(["merge", "--no-edit", remote_master])

    if merge.returncode != 0:
        log("Update uygulanamadi; conflict veya git hatasi var.")
        run_git(["merge", "--abort"])
        if merge.stderr.strip():
            log(merge.stderr.strip().splitlines()[-1])
        return

    log("Update tamamlandi.")


def should_preserve(target: Path) -> bool:
    rel_parts = target.relative_to(PROJECT_ROOT).parts
    if any(part in PRESERVED_DIRS for part in rel_parts):
        return True
    return target.suffix.lower() in PRESERVED_FILE_SUFFIXES


def copy_zip_contents(source_root: Path) -> None:
    for source in source_root.rglob("*"):
        relative = source.relative_to(source_root)
        target = PROJECT_ROOT / relative

        if should_preserve(target):
            continue

        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def zip_fallback_update() -> None:
    log("Git bulunamadi veya bu klasor git repo degil; master.zip fallback kullaniliyor.")
    with tempfile.TemporaryDirectory(prefix="fas-update-") as temp_dir:
        temp_path = Path(temp_dir)
        zip_path = temp_path / "master.zip"

        try:
            urllib.request.urlretrieve(MASTER_ZIP_URL, zip_path)
        except (urllib.error.URLError, OSError) as exc:
            log(f"Zip indirilemedi; update atlandi. ({exc})")
            return

        try:
            with zipfile.ZipFile(zip_path) as archive:
                archive.extractall(temp_path)
        except (zipfile.BadZipFile, OSError) as exc:
            log(f"Zip acilamadi; update atlandi. ({exc})")
            return

        extracted = temp_path / f"{REPO_NAME}-{MASTER_BRANCH}"
        if not extracted.exists():
            log("Zip icinde beklenen proje klasoru bulunamadi; update atlandi.")
            return

        try:
            copy_zip_contents(extracted)
        except OSError as exc:
            log(f"Dosyalar kopyalanamadi; update atlandi. ({exc})")
            return

    log("Zip fallback update tamamlandi.")


def main() -> int:
    os.chdir(PROJECT_ROOT)
    try:
        if has_git() and is_git_repo():
            git_update()
        else:
            zip_fallback_update()
    except Exception as exc:
        log(f"Beklenmeyen update hatasi; uygulama mevcut surumle acilacak. ({exc})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
