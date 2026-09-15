from itertools import product
import re

print("======================================")
print("    SIMULATOR TABEL KEBENARAN")
print("======================================")

# ======================================
# 1. INPUT
# ======================================

ekspresi = input("Masukkan ekspresi logika: ")

# ======================================
# 2. TOKENISASI
# ======================================

token = re.findall(r'[A-Za-z]+|[()]', ekspresi.upper())

print("\nToken:")
print(token)

# ======================================
# 3. DETEKSI VARIABEL
# ======================================

operator = ["AND", "OR", "NOT"]

variabel = []

for t in token:
    if t not in operator and t not in ["(", ")"]:
        if t not in variabel:
            variabel.append(t)

print("\nVariabel:")
print(variabel)

print("Jumlah variabel:", len(variabel))

# ======================================
# 4. PARSER
# ======================================

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.posisi = 0

    def current(self):
        if self.posisi < len(self.tokens):
            return self.tokens[self.posisi]
        return None

    def makan(self, token_diharapkan):
        if self.current() == token_diharapkan:
            self.posisi += 1
        else:
            raise ValueError(
                f"Token '{token_diharapkan}' diharapkan."
            )

    # OR memiliki prioritas paling rendah
    def parse_or(self):
        kiri = self.parse_and()

        while self.current() == "OR":
            self.makan("OR")
            kanan = self.parse_and()
            kiri = ("OR", kiri, kanan)

        return kiri

    # AND memiliki prioritas di atas OR
    def parse_and(self):
        kiri = self.parse_not()

        while self.current() == "AND":
            self.makan("AND")
            kanan = self.parse_not()
            kiri = ("AND", kiri, kanan)

        return kiri

    # NOT memiliki prioritas paling tinggi
    def parse_not(self):
        if self.current() == "NOT":
            self.makan("NOT")
            return ("NOT", self.parse_not())

        return self.parse_primary()

    # Variabel atau tanda kurung
    def parse_primary(self):
        if self.current() == "(":
            self.makan("(")
            hasil = self.parse_or()
            self.makan(")")
            return hasil

        elif self.current() in variabel:
            hasil = self.current()
            self.posisi += 1
            return hasil

        else:
            raise ValueError(
                f"Token tidak valid: {self.current()}"
            )


# ======================================
# 5. MEMBUAT STRUKTUR PARSING
# ======================================

try:
    parser = Parser(token)
    struktur = parser.parse_or()

    if parser.current() is not None:
        raise ValueError(
            f"Token tidak terpakai: {parser.current()}"
        )

    print("\nParsing berhasil!")

except ValueError as e:
    print("\nERROR:", e)
    exit()


# ======================================
# 6. EVALUASI STRUKTUR
# ======================================

def evaluasi(struktur, nilai):
    
    # Jika struktur adalah variabel
    if isinstance(struktur, str):
        return nilai[struktur]

    operator = struktur[0]

    # NOT
    if operator == "NOT":
        return not evaluasi(struktur[1], nilai)

    # AND
    if operator == "AND":
        return (
            evaluasi(struktur[1], nilai)
            and evaluasi(struktur[2], nilai)
        )

    # OR
    if operator == "OR":
        return (
            evaluasi(struktur[1], nilai)
            or evaluasi(struktur[2], nilai)
        )


# ======================================
# 7. GENERATOR KOMBINASI
# ======================================

kombinasi = list(
    product([True, False], repeat=len(variabel))
)

print("\nJumlah kombinasi:", len(kombinasi))


# ======================================
# 8. TABEL KEBENARAN
# ======================================

print("\nTABEL KEBENARAN")
print("-" * 45)

# Header
for v in variabel:
    print(f"{v:^8}", end="")

print(f"{'HASIL':^10}")

print("-" * 45)

# Isi tabel
for data in kombinasi:

    nilai_variabel = dict(zip(variabel, data))

    hasil = evaluasi(struktur, nilai_variabel)

    # Tampilkan nilai variabel
    for nilai in data:
        simbol = "T" if nilai else "F"
        print(f"{simbol:^8}", end="")

    # Tampilkan hasil
    simbol_hasil = "T" if hasil else "F"
    print(f"{simbol_hasil:^10}")

# ======================================
# 9. KESIMPULAN
# ======================================

semua_hasil = []

for data in kombinasi:
    nilai_variabel = dict(zip(variabel, data))
    hasil = evaluasi(struktur, nilai_variabel)
    semua_hasil.append(hasil)

print("-" * 45)

if all(semua_hasil):
    print("Kesimpulan: TAUTOLOGI")
elif not any(semua_hasil):
    print("Kesimpulan: KONTRADIKSI")
else:
    print("Kesimpulan: KONTINGENSI")

print("Program selesai.")