| Model | CV macro-F1 (latih) | Validasi macro-F1 (heldout sintetis) | Uji akurasi (manual) | Uji macro-F1 (manual) |
|---|---|---|---|---|
| 0. Aturan kata kunci (pembanding, tanpa pelatihan) | - | 0.550 | 0.752 | 0.722 |
| 1. TF-IDF + Logistic Regression (param 0.3) | 0.999 | 0.904 | 0.893 | 0.889 |
| 2. TF-IDF + Complement Naive Bayes (param 1.0) | 0.993 | 0.827 | 0.826 | 0.824 |

Model terpilih: **1. TF-IDF + Logistic Regression (param 0.3)** (dipilih dari macro-F1 data validasi, bukan data uji).
Jumlah data uji manual: 121 kalimat; satu kesalahan menggeser akurasi sekitar 0.8 poin.