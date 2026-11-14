"""Pengaturan tes bersama.

Classifier intent dan RAG dimatikan otomatis di semua tes supaya tes lama deterministik dan tidak memakai jaringan.
Tes yang memakai model/RAG asli meminta fixture `classifier_aktif` atau `rag_aktif`.
"""
import pytest

from app import intent_model, rag


@pytest.fixture(autouse=True)
def _matikan_classifier_dan_rag(request, monkeypatch):
    if "classifier_aktif" not in request.fixturenames:
        monkeypatch.setattr(intent_model, "predict", lambda text: None)
    if "rag_aktif" not in request.fixturenames:
        monkeypatch.setattr(rag, "jawab", lambda pertanyaan: None)


@pytest.fixture
def classifier_aktif():
    return True


@pytest.fixture
def rag_aktif():
    return True
