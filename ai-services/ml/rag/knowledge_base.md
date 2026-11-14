# Basis pengetahuan Asisten Sejuzz (sumber RAG)
# Format: setiap bagian diawali "## id | Judul". Isi harus sesuai fitur aplikasi yang benar-benar ada.
# Setelah mengubah file ini, jalankan ulang: python3 ml/06_bangun_indeks_rag.py

## tentang-aplikasi | Aplikasi ini untuk apa
Aplikasi Sejuzz membantu owner dan karyawan operasional kedai jus memperkirakan berapa cup jus yang bisa dihasilkan dari sejumlah buah. Pengguna memilih jenis buah, mengisi berat atau jumlah buah, lalu memilih ukuran cup. Aplikasi menampilkan rincian berat kulit dan isi buah, estimasi jumlah cup, dan sisa buah. Tujuannya supaya kebutuhan buah bisa disiapkan lebih tepat dan takaran antar karyawan lebih seragam.

## cara-pakai | Cara memakai kalkulator estimasi cup
Langkahnya: pilih jenis buah, isi berat dalam kg atau jumlah buah, pilih ukuran cup small atau large, lalu tekan hitung. Hasilnya berisi berat total, berat kulit, berat isi, takaran per cup, jumlah cup, sisa buah, dan rentang estimasi. Pengguna juga bisa mengetik pertanyaan di asisten chat, misalnya 5 kg semangka jadi berapa cup large.

## rumus-hitung | Rumus perhitungan estimasi cup
Berat total adalah berat dalam gram, atau jumlah buah dikali berat rata-rata satu buah. Berat isi adalah berat total dikurangi bagian yang susut. Berat kulit adalah berat total dikurangi berat isi. Jumlah cup adalah berat isi dibagi takaran per cup, dibulatkan ke bawah. Sisa buah adalah berat isi dikurangi jumlah cup dikali takaran. Semua angka hasil hitungan berasal dari rumus, bukan dari AI.

## arti-susut | Arti susut atau yield buah
Susut adalah persentase bagian buah yang tidak terpakai, misalnya kulit, biji, dan ampas. Yield adalah kebalikannya, yaitu bagian layak pakai dibagi berat buah utuh. Susut dihitung dari rata-rata data timbang setiap jenis buah, yaitu seratus persen dikurangi rata-rata yield dikali seratus. Semakin besar susut, semakin sedikit cup yang dihasilkan dari berat yang sama.

## satuan-input | Satuan berat atau jumlah yang bisa dipakai
Jumlah bahan bisa diisi dalam kg atau dalam jumlah buah. Jika memakai jumlah buah, aplikasi mengubahnya menjadi berat dengan berat rata-rata satu buah dari data timbang. Satuan gram belum didukung langsung, jadi ubah dulu ke kg, misalnya 500 gram ditulis 0,5 kg.

## ukuran-cup | Ukuran cup small dan large
Ada dua ukuran cup, yaitu small dan large. Di menu kedai, small sama dengan Sedang dan large sama dengan Besar. Ukuran lain seperti medium atau satuan oz belum didukung. Cup large memakai takaran lebih banyak, sehingga jumlah cup dari berat buah yang sama lebih sedikit daripada cup small.

## takaran-awal | Takaran per cup dan nilai awalnya
Takaran per cup adalah berat isi buah yang dipakai untuk satu cup. Nilai awal yang dipakai tim adalah 200 gram untuk cup small dan 250 gram untuk cup large. Nilai ini asumsi tim, belum berasal dari resep asli Sejuzz. Jika takaran sudah diatur di aplikasi oleh owner, takaran itulah yang dipakai.

## ubah-takaran | Cara mengubah takaran per cup
Owner dapat mengubah takaran per cup melalui fitur pengaturan takaran di aplikasi. Setelah takaran diubah, perhitungan berikutnya memakai nilai yang baru. Takaran harus lebih dari nol. Karyawan biasa tidak perlu mengubahnya, cukup memakai takaran yang sudah ditetapkan owner.

## rentang-estimasi | Arti rentang estimasi cup
Selain satu angka estimasi, aplikasi menampilkan kisaran wajar jumlah cup, misalnya 23 sampai 28 cup. Kisaran ini dihitung dari sebaran yield setiap jenis buah pada data timbang, memakai persentil 10 sampai 90. Artinya sebagian besar hasil diperkirakan jatuh di dalam kisaran itu. Hasil nyata bisa berada di luar kisaran, karena itu hanya perkiraan.

## data-simulasi | Data yang dipakai adalah data simulasi
Data timbang buah yang dipakai saat ini adalah data simulasi dari tim, bukan hasil timbang nyata dari Sejuzz. Setiap buah punya seratus sampel. Karena itu angka susut dan rentang adalah gambaran awal. Jika data timbang nyata sudah tersedia, data diganti dan angkanya ikut diperbarui. Aplikasi menandai rentang dengan keterangan data simulasi.

## buah-tersedia | Daftar buah yang tersedia
Buah yang tersedia ada delapan belas, yaitu alpukat, blackberry, blueberry, buah naga, jambu merah, jeruk, kelapa, mangga, melon, nanas, pakcoy, pepaya, pisang, semangka, sirsak, stroberi, terong belanda, dan tomat. Buah di luar daftar ini belum bisa dihitung.

## buah-tidak-ada | Jika buah tidak ada di daftar
Jika buah yang ditanyakan tidak ada di daftar, aplikasi akan menyampaikan bahwa buah itu belum ada di data dan menampilkan buah yang tersedia. Pilih salah satu buah dari daftar itu, atau minta owner menambahkan data buah baru.

## satu-buah | Satu perhitungan untuk satu jenis buah
Satu perhitungan hanya untuk satu jenis buah. Campuran dua buah atau lebih dalam satu cup belum didukung. Untuk jus campuran, hitung setiap buah sendiri dengan berat bagian masing-masing.

## nol-cup | Kenapa hasilnya nol cup
Hasil nol cup berarti berat isi buah belum cukup untuk satu cup penuh dengan takaran yang dipilih. Tambah jumlah buahnya, atau pilih ukuran cup yang lebih kecil. Berat isi tetap ditampilkan, jadi pengguna bisa melihat berapa yang tersedia.

## sisa-buah | Arti sisa buah
Sisa buah adalah berat isi buah yang tersisa setelah dibagi menjadi cup penuh. Jumlahnya selalu lebih kecil dari takaran satu cup. Sisa ini bisa dipakai untuk cup berikutnya atau diperhitungkan dalam persiapan buah.

## akurasi-estimasi | Seberapa akurat estimasinya
Estimasi bukan jaminan hasil produksi. Hasil nyata dipengaruhi ukuran dan kualitas buah, tingkat kematangan, dan cara mengolah. Karena itu aplikasi menampilkan rentang, bukan hanya satu angka. Perbedaan antara estimasi dan hasil produksi nyata sebaiknya dicatat supaya takaran dan data bisa disesuaikan.

## rentang-lebar | Kenapa rentang beberapa buah lebar
Rentang lebih lebar untuk buah yang bagian layaknya sangat bervariasi. Kelapa adalah yang paling bervariasi, sehingga rentang cup-nya lebar. Blackberry, blueberry, dan stroberi sangat stabil, sehingga rentangnya sempit. Semangka dan melon berada di tengah.

## pesan-error | Arti pesan kesalahan input
Jumlah atau berat harus berupa angka lebih dari nol. Satuan harus kg atau buah, dan ukuran cup harus small atau large. Jika data belum lengkap, aplikasi atau asisten akan meminta bagian yang kurang, misalnya jenis buah, jumlah, atau ukuran cup. Perbaiki isian sesuai pesan, lalu hitung lagi.

## fitur-chat | Cara memakai asisten chat
Asisten chat bisa menghitung estimasi cup dari kalimat bebas, menjawab takaran per cup, menjelaskan susut buah, dan memberi panduan memakai aplikasi. Contoh pertanyaan: lima kilo semangka jadi berapa cup large, takaran melon berapa gram, mangga susutnya berapa persen. Asisten menolak pertanyaan di luar topik estimasi cup jus.

## batas-asisten | Hal yang tidak dikerjakan aplikasi
Aplikasi tidak mengelola stok otomatis, pencatatan transaksi, harga beli, perhitungan keuntungan, pembelian ke supplier, jadwal karyawan, pembukuan keuangan, multi-outlet, atau perizinan. Asisten hanya membantu estimasi cup jus, takaran, susut buah, dan panduan penggunaan.

## asisten-sibuk | Jika penjelasan AI tidak muncul
Jika layanan AI sedang sibuk atau kuotanya habis, penjelasan diganti kalimat singkat dari template. Angka estimasi, rentang, dan sisa buah tetap benar karena dihitung dengan rumus. Coba lagi beberapa saat kemudian jika ingin penjelasan yang lebih lengkap.

## pengguna-aplikasi | Siapa yang memakai aplikasi
Aplikasi dipakai oleh owner dan karyawan operasional Sejuzz. Owner dapat mengatur takaran per cup, sedangkan karyawan memakai hasil estimasi untuk menyiapkan buah dan menyamakan takaran antar karyawan.

## baca-hasil | Cara membaca hasil perhitungan
Hasil menampilkan beberapa angka. Berat total adalah berat buah sebelum diolah. Berat kulit adalah bagian yang terbuang. Berat isi adalah bagian yang bisa dipakai. Jumlah cup adalah estimasi cup penuh. Sisa buah adalah isi yang belum cukup untuk satu cup. Rentang menunjukkan kisaran jumlah cup yang wajar.
