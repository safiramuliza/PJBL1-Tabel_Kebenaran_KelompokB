# PJBL-1 — Simulator Tabel Kebenaran & Verifikator Argumen

## Penjelasan Singkat Proyek

Simulator Tabel Kebenaran & Verifikator Argumen adalah aplikasi sederhana berbasis Python yang digunakan untuk memproses dan mengevaluasi ekspresi logika proposisional secara otomatis.

Aplikasi menerima input berupa string ekspresi logika, kemudian melakukan tokenisasi dan parsing untuk mengenali variabel serta operator logika seperti AND, OR, dan NOT. Setelah itu, aplikasi mendeteksi variabel proposisional secara otomatis dan membangkitkan seluruh kemungkinan kombinasi nilai kebenaran sebanyak 2ⁿ kombinasi, dengan n sebagai jumlah variabel.

Setiap kombinasi nilai kemudian dievaluasi berdasarkan ekspresi yang diberikan dan hasilnya ditampilkan dalam bentuk tabel kebenaran. Aplikasi juga dapat menentukan apakah suatu ekspresi merupakan tautologi, kontradiksi, atau kontingensi.

## Tujuan Proyek

Proyek ini bertujuan untuk menerapkan konsep logika proposisional dan tabel kebenaran dari Matematika Diskrit ke dalam sebuah program komputer yang dapat melakukan proses secara otomatis.

## Teknologi

- Bahasa Pemrograman: Python
- Editor: Visual Studio Code
- Konsep: Tokenisasi, parsing, variabel proposisional, kombinasi 2ⁿ, evaluasi logika, dan tabel kebenaran.

## Alur Program

```text
Input Ekspresi
      ↓
Tokenisasi
      ↓
Deteksi Variabel
      ↓
Parsing
      ↓
Pembangkitan 2ⁿ Kombinasi
      ↓
Evaluasi Ekspresi
      ↓
Tabel Kebenaran
      ↓
Kesimpulan
(Tautologi/Kontradiksi/Kontingensi)