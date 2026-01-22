import urllib.request
import ssl
import csv
import io
from datetime import datetime

# URL pro stažení CSV
URL = 'https://www.mamtex.cz/export/products.csv?patternId=279&partnerId=8&hash=98f603114b86c6b8be3cc9563c71ce983ce16ff98eb32df69d8cb32b73ada2ba'

# Výstupní soubor
OUTPUT_FILE = 'marze_export.csv'


def stahni_csv(url):
    """Stáhne CSV z URL a vrátí obsah jako string."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    with urllib.request.urlopen(url, context=ctx, timeout=120) as response:
        return response.read().decode('windows-1250')


def parse_cenu(hodnota):
    """Převede string ceny na float (např. '119,00' -> 119.0)."""
    if not hodnota:
        return 0.0
    return float(hodnota.replace(',', '.').replace(' ', ''))


def spocitej_marzi(produkty):
    """Spočítá marži pro každý produkt."""
    vysledky = []

    for p in produkty:
        nakupni = parse_cenu(p.get('purchasePrice', '0'))
        prodejni = parse_cenu(p.get('price', '0'))

        marze_kc = prodejni - nakupni
        marze_procent = ((prodejni - nakupni) / prodejni * 100) if prodejni > 0 else 0

        vysledky.append({
            'code': p.get('code', ''),
            'name': p.get('name', ''),
            'nakupni_cena': nakupni,
            'prodejni_cena': prodejni,
            'marze_kc': round(marze_kc, 2),
            'marze_procent': round(marze_procent, 2)
        })

    return vysledky


def uloz_csv(vysledky, soubor):
    """Uloží výsledky do CSV souboru."""
    with open(soubor, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'code', 'name', 'nakupni_cena', 'prodejni_cena', 'marze_kc', 'marze_procent'
        ], delimiter=';')
        writer.writeheader()
        writer.writerows(vysledky)


def main():
    print(f"[{datetime.now()}] Stahuji CSV z mamtex.cz...")
    obsah = stahni_csv(URL)

    reader = csv.DictReader(io.StringIO(obsah), delimiter=';')
    produkty = list(reader)

    print(f"Načteno {len(produkty)} produktů.")

    vysledky = spocitej_marzi(produkty)

    uloz_csv(vysledky, OUTPUT_FILE)
    print(f"Uloženo do {OUTPUT_FILE}")

    # Statistiky
    prumerna_marze = sum(v['marze_procent'] for v in vysledky) / len(vysledky) if vysledky else 0
    print(f"Průměrná marže: {prumerna_marze:.2f}%")


if __name__ == "__main__":
    main()
