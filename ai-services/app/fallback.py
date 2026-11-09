"""Balasan template tanpa LLM, dipakai saat LLM gagal atau jawabannya tidak lolos pemeriksaan angka."""


def _num(x: float) -> str:
    return f"{x:,.2f}".rstrip("0").rstrip(".").replace(",", "_").replace(".", ",").replace("_", ".")


def explain_template(calc: dict, amount, unit: str) -> str:
    cup, sisa = calc["jumlah_cup"], calc["sisa_buah_gram"]
    teks = (f"Dari {_num(amount)} {unit} {calc['fruit']}, daging buah yang bisa dipakai sekitar "
            f"{_num(calc['berat_isi_gram'])} gram. Dengan takaran {_num(calc['gram_per_cup'])} gram per cup "
            f"{calc['cup_size']}, estimasinya {cup} cup, sisa buah sekitar {_num(sisa)} gram.")
    if cup == 0:
        teks += " Jumlahnya belum cukup untuk satu cup."
    return teks + " Ini hanya estimasi, hasil nyata bisa sedikit berbeda."


fmt_num = _num
