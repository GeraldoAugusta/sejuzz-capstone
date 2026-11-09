| Model | MAE CV (gram) | MAE uji (gram) | RMSE uji (gram) | R2 uji | MAE uji (cup) |
|---|---|---|---|---|---|
| 0. Referensi (rata-rata yield semua buah) | 107.24 | 104.36 | 203.11 | 0.7240 | 0.517 |
| 1. Baseline (rata-rata yield per buah) | 19.48 | 17.54 | 36.74 | 0.9910 | 0.092 |
| 2. Regresi linear per buah | 19.50 | 17.72 | 37.17 | 0.9910 | 0.092 |
| 3a. Random forest (bawaan) | 23.00 | 21.18 | 43.78 | 0.9870 | 0.108 |
| 3b. Random forest (tuning) | 20.35 | 18.48 | 38.19 | 0.9900 | 0.097 |

Model terpilih: **1. Baseline (rata-rata yield per buah)**. Alasan: baseline punya galat CV paling kecil, model yang lebih rumit tidak memberi perbaikan.
Cakupan rentang P10-P90 pada data uji: 78.6%.