"""Inti kanal pesan (tidak bergantung pada Telegram/WhatsApp): perintah, batas laju, anti pesan ganda.

Adaptor kanal (telegram.py, dan nanti WhatsApp) hanya mengurus format masuk-keluar; jawaban selalu dari chat.handle_message,
jadi perilakunya sama dengan /api/v1/ai/chat (classifier, RAG, rumus, guardrail).
"""
import threading
import time
from collections import OrderedDict, deque

from app import chat

MAKS_PANJANG = 300  # sama dengan batas ChatRequest
BANTUAN_KANAL = chat.HELP + "\n\nPerintah: /start (mulai), /help (panduan), /id (lihat ID chat)."


def balasan(teks: str, id_chat=None) -> str:
    """Kembalikan teks balasan untuk satu pesan masuk."""
    t = (teks or "").strip()
    if not t:
        return "Kirim pertanyaanmu dalam bentuk teks ya."
    if t.startswith("/"):
        perintah = t.split()[0].split("@")[0].lower()
        if perintah == "/start":
            return chat.GREETING_REPLY
        if perintah in ("/help", "/bantuan"):
            return BANTUAN_KANAL
        if perintah == "/id":
            return f"ID chat kamu: {id_chat}"
        return "Perintah itu belum ada. Ketik /help untuk panduan."
    if len(t) > MAKS_PANJANG:
        return f"Pesannya terlalu panjang (maksimal {MAKS_PANJANG} karakter). Coba dipersingkat ya."
    return chat.handle_message(t)["reply"]


class BatasLaju:
    """Batas jumlah pesan per chat dalam satu jendela waktu (di memori, per proses)."""

    def __init__(self, maks: int = 10, jendela: float = 60.0, waktu=time.monotonic):
        self.maks, self.jendela, self.waktu = maks, jendela, waktu
        self._data: dict = {}
        self._kunci = threading.Lock()

    def izinkan(self, id_chat) -> bool:
        sekarang = self.waktu()
        with self._kunci:
            q = self._data.setdefault(id_chat, deque())
            while q and sekarang - q[0] > self.jendela:
                q.popleft()
            if len(q) >= self.maks:
                return False
            q.append(sekarang)
            if len(self._data) > 5000:  # cegah memori membengkak: buang chat yang sudah lama diam
                for k in [k for k, v in self._data.items() if not v or sekarang - v[-1] > self.jendela]:
                    del self._data[k]
            return True


class AntiGanda:
    """Ingat id update terakhir supaya pengiriman ulang dari platform tidak dijawab dua kali."""

    def __init__(self, kapasitas: int = 2000):
        self.kapasitas = kapasitas
        self._ada: OrderedDict = OrderedDict()
        self._kunci = threading.Lock()

    def baru(self, id_update) -> bool:
        with self._kunci:
            if id_update in self._ada:
                return False
            self._ada[id_update] = True
            while len(self._ada) > self.kapasitas:
                self._ada.popitem(last=False)
            return True
