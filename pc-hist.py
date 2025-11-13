#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import json
import os
import sys
from datetime import datetime

import requests

DATA_SOURCE = "postnummer.csv"
DATA_DIR = "historikk"
WAAPI_TOKEN = "53fd9b78-9bfd-42e5-bea8-ec1b3c47defb"
HIST_URL = "https://www.webatlas.no/WAAPI-Eiendomsomsetning/api/Omsetning/historikk"


def les_postnummerdata():
    data = []
    with open(DATA_SOURCE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for rad in reader:
            data.append(rad)
    return data


def finn_kommune(kommune_arg, postdata):
    kommune_arg = str(kommune_arg).strip()
    for rad in postdata:
        kommunenummer = rad["Kommunenummer"]
        kommunenavn   = rad["Kommunenavn"]
        if kommunenummer == kommune_arg:
            return kommunenummer, kommunenavn
        if kommunenavn.lower() == kommune_arg.lower():
            return kommunenummer, kommunenavn
    print(f"Fant ikke kommune '{kommune_arg}' i {DATA_SOURCE}")
    sys.exit(1)


def les_csv(csv_fil):
    """
    Leser CSV posisjonsbasert, helt uavhengig av kolonnenavn.
    Forventer kolonnerekkefølge:
      1: kommunenummer
      2: gnr
      3: bnr
      4: fnr (valgfri)
      5: snr (valgfri)
    """
    rader = []
    with open(csv_fil, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)

        for linje in reader:
            if not linje or len([c for c in linje if c.strip()]) == 0:
                continue  # hopp over tomme linjer

            try:
                kommunenummer = linje[0].strip()
                gnr = int(linje[1])
                bnr = int(linje[2])
                fnr = int(linje[3]) if len(linje) > 3 and linje[3].strip() else 0
                snr = int(linje[4]) if len(linje) > 4 and linje[4].strip() else 0

                rader.append({
                    "kommunenummer": kommunenummer,
                    "gnr": gnr,
                    "bnr": bnr,
                    "fnr": fnr,
                    "snr": snr
                })

            except Exception:
                print("Ugyldig rad:", linje)
                continue

    return rader


def oppsummer_csv(rader):
    kommuner = sorted(set(r["kommunenummer"] for r in rader))
    gnr_min = min(r["gnr"] for r in rader)
    gnr_max = max(r["gnr"] for r in rader)
    bnr_min = min(r["bnr"] for r in rader)
    bnr_max = max(r["bnr"] for r in rader)

    print("\n=== CSV-oppsummering ===")
    print(f"Antall rader: {len(rader)}")
    print(f"Unike kommuner: {', '.join(kommuner)}")
    print(f"Gnr: {gnr_min} – {gnr_max}")
    print(f"Bnr: {bnr_min} – {bnr_max}")
    print("\nTopp 10 rader:")
    for r in rader[:10]:
        print(f"  {r['kommunenummer']} {r['gnr']}/{r['bnr']} fnr={r['fnr']} snr={r['snr']}")
    print("========================\n")


def lag_gid(kommunenummer, gnr, bnr, fnr=0, snr=0):
    kommunenummer4 = f"{int(kommunenummer):04d}"
    gnr4 = f"{int(gnr):04d}"
    bnr4 = f"{int(bnr):04d}"
    fnr4 = f"{int(fnr):04d}"
    concat = f"{gnr4}{bnr4}{fnr4}0000"
    tail = "0" + concat[:-1]
    return kommunenummer4 + tail


def hent(gid, filnavn):
    url = f"{HIST_URL}/{gid}"
    headers = {"X-WAAPI-Token": WAAPI_TOKEN}

    print(f"Henter: {url} -> {filnavn}")
    start = datetime.now()
    r = requests.get(url, headers=headers)
    varighet = (datetime.now() - start).seconds

    if r.status_code != 200:
        print(f"Feil {r.status_code} fra WAAPI for GID {gid}")
        print(r.text[:500])
        return

    try:
        data = r.json()
    except json.JSONDecodeError:
        print("Klarte ikke å parse JSON")
        print(r.text[:500])
        return

    os.makedirs(os.path.dirname(filnavn), exist_ok=True)
    with open(filnavn, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    size_kb = os.path.getsize(filnavn) // 1024
    entries = len(data) if isinstance(data, list) else 1
    lines = sum(1 for _ in open(filnavn, encoding="utf-8"))

    print(f"Ferdig: {size_kb} KB, {lines} linjer, {entries} entries, varighet={varighet}s")


def main():
    parser = argparse.ArgumentParser(description="Hent historikk fra WAAPI")
    parser.add_argument("--kommune", help="Kommunenavn eller kommunenummer")
    parser.add_argument("--gnr", type=int, help="Gårdsnummer")
    parser.add_argument("--bnr", type=int, help="Bruksnummer")
    parser.add_argument("--fnr", type=int, default=0)
    parser.add_argument("--snr", type=int, default=0)
    parser.add_argument("--fil", help="CSV med: kommunenummer, gnr, bnr, fnr?, snr?")

    args = parser.parse_args()
    postdata = les_postnummerdata()

    # CSV-modus
    if args.fil:
        rader = les_csv(args.fil)
        if not rader:
            print("CSV inneholder ingen gyldige rader.")
            sys.exit(1)

        oppsummer_csv(rader)

        svar = input("Vil du starte nedlasting? (y/n): ").strip().lower()
        if svar != "y":
            print("Avbrutt.")
            sys.exit(0)

        for r in rader:
            kommunenummer = r["kommunenummer"]
            kommunenummer, kommunenavn = finn_kommune(kommunenummer, postdata)
            gid = lag_gid(kommunenummer, r["gnr"], r["bnr"], r["fnr"], r["snr"])
            filnavn = os.path.join(
                DATA_DIR,
                f"{kommunenummer}-{kommunenavn}-{r['gnr']}-{r['bnr']}-{r['fnr']}-{r['snr']}.json",
            )
            hent(gid, filnavn)
        return

    # Enkel én-off henting (original funksjonalitet)
    if not (args.kommune and args.gnr and args.bnr):
        print("Bruk enten --fil eller --kommune + --gnr + --bnr")
        sys.exit(1)

    kommunenummer, kommunenavn = finn_kommune(args.kommune, postdata)
    gid = lag_gid(kommunenummer, args.gnr, args.bnr, args.fnr, args.snr)
    filnavn = os.path.join(
        DATA_DIR,
        f"{kommunenummer}-{kommunenavn}-{args.gnr}-{args.bnr}-{args.fnr}-{args.snr}.json"
    )
    hent(gid, filnavn)


if __name__ == "__main__":
    main()