# Modul Sentimen Ulasan (ai-services)

Menebak apakah ulasan pelanggan **positif** atau **negatif**.
Kode: `app/routers/sentimen.py` (endpoint) dan `app/sentimen/` (model dan logika).
Dokumentasi interaktif: `/docs` pada alamat API utama.

## Autentikasi
Sama seperti router lain: header `X-API-Key`, aktif bila `SERVICE_API_KEY` terisi di server.
Backend Express mengirim header ini. Kalau `SERVICE_API_KEY` kosong (lokal), header tidak diperlukan.

## Endpoint

### `POST /api/v1/sentimen`: satu kalimat
Request:
```json
{ "teks": "Jusnya segar banget, pelayanannya ramah dan cepat" }
```
Response 200:
```json
{
  "teks": "Jusnya segar banget, pelayanannya ramah dan cepat",
  "sentimen": "positif",
  "skor": 1.513,
  "yakin": true,
  "peringatan": null
}
```

| Field | Arti |
|---|---|
| `sentimen` | `"positif"` atau `"negatif"` |
| `skor` | Makin jauh dari 0 makin yakin. Positif = tebakan positif, negatif = tebakan negatif |
| `yakin` | `false` kalau nilai mutlak skor di bawah 0,5 (model ragu). Sebaiknya UI menampilkan "kurang yakin" |
| `peringatan` | Berisi teks kalau kalimat tampaknya berbahasa Inggris (model lemah di sini). Selain itu `null` |

### `POST /api/v1/sentimen/batch`: banyak kalimat (maksimal 100)
Request: `{ "daftar_teks": ["Mantap jusnya", "Tempat kotor dan pelayanan buruk"] }`

Response 200 berisi `jumlah`, `jumlah_positif`, `jumlah_negatif`, `jumlah_tidak_terbaca`, dan `hasil` (urutannya sama dengan masukan).
Kalimat yang tidak berisi kata (misalnya hanya emoji) tetap muncul di `hasil` dengan `sentimen: null` dan penjelasan di `peringatan`.

### `GET /api/v1/sentimen/info`: info model
Memuat `label`, `sklearn_version` (saat model dilatih), `versi_sklearn_server`, dan `versi_cocok`.

## Format error (seragam dengan router lain)
```json
{ "error": { "code": "TEXT_NOT_ANALYZABLE", "message": "..." } }
```

| HTTP | `code` | Kapan | Yang dilakukan UI |
|---|---|---|---|
| 401 | `UNAUTHORIZED` | Header `X-API-Key` tidak ada atau salah | Periksa konfigurasi backend |
| 422 | `VALIDATION_ERROR` | `teks` kosong atau lebih dari 1000 karakter, field hilang, atau batch kosong/lebih dari 100 | Tampilkan `message` |
| 422 | `TEXT_NOT_ANALYZABLE` | Kalimat tidak berisi kata (hanya emoji, angka, atau tanda baca) | Minta pengguna menulis ulang |
| 503 | `MODEL_UNAVAILABLE` | File model tidak ada atau tidak bisa dibuka | Tampilkan "layanan analisis sedang tidak tersedia". Pengelola melatih ulang model |

**Cek kecocokan versi.** Kalau `versi_cocok` bernilai `false`, scikit-learn di server berbeda dari saat model dilatih.
Model tetap bisa terbuka, tetapi hasilnya **tidak terjamin** (scikit-learn mencatat peringatan di log).
Perbaikannya: latih ulang model dengan versi yang sama dengan server (`scripts/latih_model_sentimen.py`).

## Contoh pemanggilan dari backend Express (Axios)
Sebaiknya dipanggil dari backend, bukan langsung dari browser.
```js
import axios from "axios";

export async function analisisSentimen(teks) {
  const { data } = await axios.post(
    `${process.env.AI_SERVICE_URL}/api/v1/sentimen`,
    { teks },
    { headers: { "X-API-Key": process.env.SERVICE_API_KEY }, timeout: 10000 }
  );
  return data; // { sentimen, skor, yakin, peringatan }
}
```

## Keterbatasan (tulis juga di README proyek)
- Data negatif Sejuzz hanya 8 ulasan, jadi evaluasi kelas negatif belum stabil.
- Kalimat berbahasa Inggris dan ulasan campuran (memuji sekaligus mengeluh) sering salah. Itu sebabnya ada `peringatan` dan `yakin`.
- Skor "yakin" adalah aturan kasar, bukan probabilitas.
