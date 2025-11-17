#!/usr/bin/env python3
"""
plates_access.py
Jednostavan program za školu koji pamti 15 registarskih tablica ("tablice"),
provjerava unesenu tablicu i dozvoljava pristup odgovarajućem parking mjestu.

- Spreman za brzo razumijevanje i uređivanje (čitki komentari i podijeljeni blokovi)
- Podaci se trajno spremaju u `plates_data.json`
- Pristupi se loguju u `access_log.json`

Kako koristiti (primjer):
  python plates_access.py

Autorski napomene: kod je pisan na hrvatsko/bosanskom jeziku radi lakšeg razumijevanja.
"""

# ----- IMPORTI I KONFIGURACIJA -------------------------------------------------
import json
import os
from datetime import datetime

DATA_FILE = 'plates_data.json'   # Spremište za tablice (lista objekata: {'spot': int, 'plate': str})
LOG_FILE = 'access_log.json'     # Log pristupa (vrijeme, tablica, spot, granted)
TOTAL_SPOTS = 15                 # Broj mjesta koje želimo zapamtiti

# ---------------------------------------------------------------------------
# NOTE (BRZI PRIKAZ):
# - Ako tražite 'mjesto gdje se unose tablice', pogledajte funkciju
#   `initialize_plates_interactive()` (dolje) — tamo se interaktivno unose
#   tablice i poziva se `save_plates(...)` da se podaci trajno zapamte.
# - Također pogledajte `save_plates()` koja piše u `plates_data.json`.
# ---------------------------------------------------------------------------


# ----- POMOĆNE FUNKCIJE ZA SPREMANJE/UCITAVANJE ---------------------------------

def load_plates():
    """Učitaj tablice iz `DATA_FILE`. Ako datoteka ne postoji, vrati praznu listu."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []


def save_plates(plates):
    """Spremi listu tablica u `DATA_FILE`."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(plates, f, ensure_ascii=False, indent=2)

# ------------------------- IMPORTANT (BOLD MARKER) ---------------------------
# OVO JE FUNKCIJA KOJA SPREMA TABLICE NA DISK. Ako želite da program zapamti
# tablice, one moraju proći kroz ovu funkciju (ili možete ručno urediti
# `plates_data.json`).
# -----------------------------------------------------------------------------


def log_access(entry):
    """Dodaj zapis u `LOG_FILE` (apend)."""
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except Exception:
            logs = []
    logs.append(entry)
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


# ----- NORMALIZACIJA I PRETRAGA TABLICA ---------------------------------------

def normalize_plate(s):
    """Normaliziraj unos tablice radi lakše usporedbe: ukloni razmake i velika slova."""
    return ''.join(s.split()).upper()


def find_plate(plates, plate_input):
    """Vrati rezervaciju ako tablica postoji; inače None.

    plates: lista dictova sa 'spot' i 'plate'
    plate_input: string unesene tablice
    """
    norm = normalize_plate(plate_input)
    for p in plates:
        if normalize_plate(p.get('plate', '')) == norm:
            return p
    return None


# ----- INICIJALIZACIJA: KREIRANJE/UREĐIVANJE OBAVEZNIH 15 TABLICA ---------------

def initialize_plates_interactive():
    """Interaktivno unesi točno `TOTAL_SPOTS` tablica. Pretpostavka: jednostavan unos od strane administratora."""
    print(f"Inicijalizacija {TOTAL_SPOTS} tablica. Unesite jednu po jednu (bez dijaloga).")
    # ======================================================================
    # >>>>>  >>>>>  >>>>>  >>>>>  IMPORTANT (BOLD)  <<<<<<  <<<<< <<<<<<
    # >>>>>  OVDJE UNESITE TABLICE: program će ih zapamtiti u `plates_data.json`
    # >>>>>  Nakon što unesete tablice, poziva se `save_plates(plates)` i podaci
    # >>>>>  će ostati trajno spremljeni. Ako želite ručno unijeti tablice bez
    # >>>>>  interaktivnog unosa, otvorite `plates_data.json` ili koristite
    # >>>>>  funkciju `save_plates(...)` u Python interpreteru.
    # >>>>>  >>>>>  >>>>>  >>>>>  >>>>>  >>>>>  >>>>>
    # ======================================================================
    plates = []
    seen = set()
    i = 1
    while i <= TOTAL_SPOTS:
        val = input(f"[{i}/{TOTAL_SPOTS}] Unesite tablicu za mjesto #{i}: ").strip()
        if not val:
            print("Prazan unos, pokušajte ponovno.")
            continue
        norm = normalize_plate(val)
        if norm in seen:
            print("Ta tablica je već unesena. Unesite drugu.")
            continue
        plates.append({'spot': i, 'plate': val})
        seen.add(norm)
        i += 1
    save_plates(plates)
    print(f"Spremljeno {TOTAL_SPOTS} tablica u {DATA_FILE}.")
    return plates


# ----- FUNKCIJA ZA PROVJERU TABLICE I DOZVOLU PRISTUPA -------------------------

def verify_plate(plates, plate_input):
    """Provjeri unesenu tablicu.

    Ako postoji, zabilježi pristup i vrati (True, spot). Ako ne postoji, zabilježi odbijanje i vrati (False, None).
    """
    found = find_plate(plates, plate_input)
    timestamp = datetime.now().isoformat()
    if found:
        entry = {'time': timestamp, 'plate': plate_input, 'spot': found['spot'], 'granted': True}
        log_access(entry)
        return True, found['spot']
    else:
        entry = {'time': timestamp, 'plate': plate_input, 'spot': None, 'granted': False}
        log_access(entry)
        return False, None


# ----- JEDNOSTAVNE CRUD OPERACIJE ZA TABLICE ----------------------------------

def list_plates(plates):
    """Ispiši trenutno spremljene tablice i njihove spotove."""
    if not plates:
        print("Nema spremljenih tablica.")
        return
    print("Trenutne tablice:")
    for p in plates:
        print(f"  Mjesto #{p['spot']:2d} -> {p['plate']}")


def add_or_update_plate(plates):
    """Dodaj ili ažuriraj tablicu na određenom spotu."""
    try:
        spot = int(input(f"Unesite broj mjesta (1-{TOTAL_SPOTS}): "))
    except ValueError:
        print("Neispravan broj.")
        return plates
    if not (1 <= spot <= TOTAL_SPOTS):
        print("Broj van opsega.")
        return plates
    plate = input("Unesite tablicu (npr. ABC-123): ").strip()
    if not plate:
        print("Prazan unos.")
        return plates
    # provjeri postoji li već zapis za spot
    for p in plates:
        if p['spot'] == spot:
            p['plate'] = plate
            save_plates(plates)
            print(f"Ažurirano mjesto #{spot} -> {plate}")
            return plates
    # inače dodaj
    plates.append({'spot': spot, 'plate': plate})
    plates.sort(key=lambda x: x['spot'])
    save_plates(plates)
    print(f"Dodano mjesto #{spot} -> {plate}")
    return plates


def remove_plate(plates):
    """Ukloni tablicu po broju mjesta ili po tablici."""
    mode = input("Ukloni po (1) broju mjesta ili (2) tablici? (1/2): ").strip()
    if mode == '1':
        try:
            spot = int(input("Unesite broj mjesta: "))
        except ValueError:
            print("Neispravan broj.")
            return plates
        new = [p for p in plates if p['spot'] != spot]
        if len(new) == len(plates):
            print("Nije pronađeno mjesto.")
        else:
            save_plates(new)
            print(f"Uklonjeno mjesto #{spot}.")
        return new
    elif mode == '2':
        plate = input("Unesite tablicu za uklanjanje: ").strip()
        norm = normalize_plate(plate)
        new = [p for p in plates if normalize_plate(p.get('plate','')) != norm]
        if len(new) == len(plates):
            print("Tablica nije pronađena.")
        else:
            save_plates(new)
            print(f"Uklonjena tablica {plate}.")
        return new
    else:
        print("Neispravan izbor.")
        return plates


# ----- POMOĆNA FUNKCIJA: PRIKAŽI LOG ------------------------------------------------

def show_logs(limit=50):
    """Prikaži zadnjih `limit` zapisa iz LOG_FILE-a."""
    if not os.path.exists(LOG_FILE):
        print("Nema logova još.")
        return
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    except Exception:
        print("Ne mogu otvoriti logove.")
        return
    print(f"Prikaz zadnjih {limit} zapisa (najnoviji prvi):")
    for e in logs[-limit:][::-1]:
        time = e.get('time')
        plate = e.get('plate')
        spot = e.get('spot')
        granted = e.get('granted')
        status = 'Dozvoljen' if granted else 'Odbijen'
        print(f"  [{time}] {plate} -> {status} (spot: {spot})")


# ----- GLAVNI PROGRAM (INTERAKTIVNI MENI) -------------------------------------

def main():
    """Jednostavan meni za upravljanje tablicama i verifikaciju."""
    plates = load_plates()

    while True:
        print("\n=== ŠKOLSKI PARKING - MENI ===")
        print("1) Inicijaliziraj 15 tablica (admin)")
        print("2) Prikaži tablice")
        print("3) Verificiraj tablicu (unutar škole)")
        print("4) Dodaj/azuriraj tablicu")
        print("5) Ukloni tablicu")
        print("6) Prikaži log pristupa")
        print("0) Izlaz")
        ch = input("Odaberite opciju: ").strip()

        if ch == '1':
            plates = initialize_plates_interactive()
        elif ch == '2':
            list_plates(plates)
        elif ch == '3':
            plate = input("Unesite tablicu za provjeru: ").strip()
            ok, spot = verify_plate(plates, plate)
            if ok:
                print(f"✅ Dobrodošli! Tablica odgovara mjestu #{spot}.")
            else:
                print("⛔ Tablica nije registrirana. Pristup odbijen.")
        elif ch == '4':
            plates = add_or_update_plate(plates)
        elif ch == '5':
            plates = remove_plate(plates)
        elif ch == '6':
            try:
                n = int(input("Koliko zadnjih zapisa prikazati? (default 50): ") or 50)
            except ValueError:
                n = 50
            show_logs(n)
        elif ch == '0':
            print("Kraj.")
            break
        else:
            print("Nepoznata opcija, pokušajte ponovo.")


if __name__ == '__main__':
    main()
