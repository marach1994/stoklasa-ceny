import urllib.request
import ssl
import csv
import io
import time
from datetime import datetime

# URL pro stažení CSV
URL = 'https://www.mamtex.cz/export/products.csv?patternId=279&partnerId=8&hash=98f603114b86c6b8be3cc9563c71ce983ce16ff98eb32df69d8cb32b73ada2ba&supplierId=316'

# Výstupní soubor
OUTPUT_FILE = 'marze_export.csv'


def stahni_csv(url, max_pokusu=3):
    """Stáhne CSV z URL a vrátí obsah jako string."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = {'User-Agent': 'Mozilla/5.0 (compatible; MarzeBot/1.0)'}
    req = urllib.request.Request(url, headers=headers)

    for pokus in range(max_pokusu):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=600) as response:
                return response.read().decode('windows-1250')
        except Exception as e:
            print(f"Pokus {pokus + 1}/{max_pokusu} selhal: {e}")
            if pokus < max_pokusu - 1:
                time.sleep(10)
            else:
                raise


def parse_cenu(hodnota):
    """Převede string ceny na float (např. '119,00' -> 119.0)."""
    if not hodnota:
        return 0.0
    return float(hodnota.replace(',', '.').replace(' ', ''))


def zaokrouhli_na_5(hodnota):
    """Zaokrouhlí hodnotu na nejbližší 5 (27→30, 51→50, 63→65)."""
    zbytek = hodnota % 5
    if zbytek == 0:
        return int(hodnota)
    elif zbytek == 1:
        return int(hodnota - 1)  # dolů
    else:
        return int(hodnota + (5 - zbytek))  # nahoru


def spocitej_marzi(produkty):
    """Spočítá marži pro každý produkt."""
    vysledky = []

    for p in produkty:
        nakupni = parse_cenu(p.get('purchasePrice', '0'))
        prodejni = parse_cenu(p.get('standardPrice', '0'))

        marze_kc = prodejni - nakupni
        marze_procent = ((prodejni - nakupni) / prodejni * 100) if prodejni > 0 else 0
        multishop = zaokrouhli_na_5(marze_procent)

        vysledky.append({
            'Kód produktu': p.get('code', ''),
            'Název': p.get('name', ''),
            'Nákupní cena': nakupni,
            'Prodejní cena': prodejni,
            'Marže Kč': round(marze_kc, 2),
            'Marže %': round(marze_procent, 2),
            'Multishop': multishop
        })

    return vysledky


def uloz_csv(vysledky, soubor):
    """Uloží výsledky do CSV souboru."""
    with open(soubor, 'w', newline='', encoding='windows-1250') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Kód produktu', 'Název', 'Nákupní cena', 'Prodejní cena', 'Marže Kč', 'Marže %', 'Multishop'
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
    prumerna_marze = sum(v['Marže %'] for v in vysledky) / len(vysledky) if vysledky else 0
    print(f"Průměrná marže: {prumerna_marze:.2f}%")


if __name__ == "__main__":
    main()
