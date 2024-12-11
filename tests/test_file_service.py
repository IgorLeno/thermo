import pytest
from services.file_service import FileService
from config.constants import *
import os

def test_create_directory(file_service, tmp_path):
    """Testa a criação de diretórios."""
    test_dir = tmp_path / "test_dir"
    file_service.create_directory(str(test_dir))
    assert test_dir.exists() and test_dir.is_dir()

def test_clear_directory(file_service, tmp_path):
    """Testa a limpeza de diretórios."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "test_file.txt").touch()
    file_service.clear_directory(str(test_dir))
    assert not (test_dir / "test_file.txt").exists()

def test_copy_file(file_service, tmp_path):
    """Testa a cópia de arquivos."""
    src_file = tmp_path / "src_file.txt"
    src_file.write_text("Test content")
    dest_file = tmp_path / "dest_file.txt"
    file_service.copy_file(str(src_file), str(dest_file))
    assert dest_file.exists()
    assert dest_file.read_text() == "Test content"

def test_move_file(file_service, tmp_path):
    """Testa a movimentação de arquivos."""
    src_file = tmp_path / "src_file.txt"
    src_file.write_text("Test content")
    dest_dir = tmp_path / "dest_dir"
    dest_dir.mkdir()
    dest_file = dest_dir / "src_file.txt"
    file_service.move_file(str(src_file), str(dest_file))
    assert dest_file.exists()
    assert not src_file.exists()