"""Pengaturan tes bersama.

Classifier intent dimatikan otomatis di semua tes supaya tes lama tetap menguji jalur LLM/aturan secara deterministik.
Tes yang memakai model asli meminta fixture `classifier_aktif`.
"""
import pytest

from app import intent_model


@pytest.fixture(autouse=True)
def _matikan_classifier(request, monkeypatch):
    if "classifier_aktif" in request.fixturenames:
        return
    monkeypatch.setattr(intent_model, "predict", lambda text: None)


@pytest.fixture
def classifier_aktif():
    return True
