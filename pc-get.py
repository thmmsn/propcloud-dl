#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import os
import sys
import requests
from datetime import datetime
import json

# -------------------------------------------
# KONSTANTER OG FILSTIER
# -------------------------------------------
DATA_DIR = "matrikkelen"
DATA_SOURCE = "postnummer.csv"
API_URL = "https://services.api.no/api/acies/v1/custom/PropcloudLegacyTransaction"


# -------------------------------------------
# LAST INN POSTNUMMERDATA FRA CSV
# -------------------------------------------
def les_postnummerdata():
    data = []
    with open(DATA_SOURCE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    return data


# -------------------------------------------
# FINN FYLKE (county) I CSV
# -------------------------------------------
def finn_info_fylke(fylke, data):
    for rad in data:
        if rad["Fylkesnavn"].lower() == fylke.lower() or rad["Fylkesnummer"] == fylke:
            return rad
    return None


# -------------------------------------------
# FINN KOMMUNE (municipality) I CSV
# -------------------------------------------
def finn_info_kommune(kommune, data):
    for rad in data:
        if rad["Kommunenavn"].lower() == kommune.lower() or rad["Kommunenummer"] == kommune:
            return rad
    return None


# -------------------------------------------
# HJELPEFUNKSJON: liste eller intervall
# -------------------------------------------
def parse_intervall_eller_liste(verdi):
    if not verdi:
        return []
    if ":" in verdi:
        start, slutt = verdi.split(":")
        return [str(i) for i in range(int(start), int(slutt) + 1)]
    return verdi.split()


# -------------------------------------------
# LAST NED JSON OG PRETTIFY
# -------------------------------------------
def hent_data(url, destinasjon):
    os.makedirs(os.path.dirname(destinasjon), exist_ok=True)
    start = datetime.now()

    r = requests.get(url)
    varighet = (datetime.now() - start).seconds

    if r.status_code == 200:
        with open(destinasjon, "w", encoding="utf-8") as f:
            f.write(r.text)

        size_kb = os.path.getsize(destinasjon) // 1024

        # Prettify
        prettify_json(destinasjon)

        # Tell linjer etter formatering
        with open(destinasjon, encoding="utf-8") as f:
            lines_after = sum(1 for _ in f)

        # Tell entries i JSON
        with open(destinasjon, encoding="utf-8") as f:
            import json
            data = json.load(f)
            entries = len(data)

        print(f"Ferdig: {size_kb} KB, {lines_after} linjer etter prettify, {entries} entries, varighet={varighet}s")

    else:
        print(f"Feil ved henting ({r.status_code}): {url}")


# -------------------------------------------
# BYGG API URL (for både fylke og kommune)
# -------------------------------------------
def bygg_url(code, år, måned=None):
    # countyCode = 2 siffer
    # municipalityCode = 4 siffer
    if len(code) == 2:
        base = f"{API_URL}?equal=countyCode:{code}"
    else:
        base = f"{API_URL}?equal=municipalityCode:{code}"

    if måned:
        fra = f"{år}-{str(måned).zfill(2)}-01"
        if int(måned) == 12:
            til = f"{int(år)+1}-01-01"
        else:
            til = f"{år}-{str(int(måned)+1).zfill(2)}-01"
    else:
        fra = f"{år}-01-01"
        til = f"{int(år)+1}-01-01"

    return f"{base}&greaterThanOrEqual=date:{fra}&lessThan=date:{til}"


# -------------------------------------------
# JSON FORMATERING
# -------------------------------------------
def prettify_json(filepath):
    def fix_nested_json(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str) and v.strip().startswith("[{"):
                    try:
                        obj[k] = json.loads(v)
                    except json.JSONDecodeError:
                        pass
                else:
                    obj[k] = fix_nested_json(v)
        elif isinstance(obj, list):
            return [fix_nested_json(x) for x in obj]
        return obj

    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        data = fix_nested_json(data)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Prettified: {filepath}")

    except Exception as e:
        print(f"Feil ved formatering av {filepath}: {e}")


# -------------------------------------------
# MAIN
# -------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Last ned og strukturer eiendomsoverdragelser fra API.no")

    parser.add_argument("--fylke", type=str, nargs="*", help="Fylkesnavn eller fylkesnummer")
    parser.add_argument("--kommune", type=str, nargs="*", help="Kommunenavn eller kommunenummer")
    parser.add_argument("--år", required=True, type=str, nargs="+", help="År eller intervall")
    parser.add_argument("--måned", type=str, nargs="*", help="Måned eller intervall")

    args = parser.parse_args()

    postdata = les_postnummerdata()
    kombinasjoner = []

    # -------------------------------------------
    # PARSE ÅR OG MÅNED
    # -------------------------------------------
    år_liste = []
    for y in args.år:
        år_liste.extend(parse_intervall_eller_liste(y))

    måneder = []
    for m in (args.måned or []):
        måneder.extend(parse_intervall_eller_liste(m))
    måneder = [int(m) for m in måneder] if måneder else [None]

    # -------------------------------------------
    # HENT ALLE FYLKER OG KOMMUNER FRA CSV
    # -------------------------------------------
    alle_fylker = sorted({(rad["Fylkesnummer"], rad["Fylkesnavn"]) for rad in postdata})
    alle_kommuner = sorted({(rad["Fylkesnummer"], rad["Kommunenummer"], rad["Kommunenavn"]) for rad in postdata})

    # -------------------------------------------
    # REGELSETT FOR KOMBINASJON AV PARAMETERE
    # -------------------------------------------

    if args.fylke == ["alle"] and not args.kommune:
        # HENT KUN FYLKESNIVÅ (countyCode direkte)
        for fylkesnummer, fylkesnavn in alle_fylker:
            kombinasjoner.append({
                "countyCode": fylkesnummer,
                "countyName": fylkesnavn
            })

    elif args.fylke and args.kommune == ["alle"]:
        # ALLE KOMMUNER I ANGITT FYLKE (eller liste over fylker)
        for f in args.fylke:
            for fylkesnummer, kommunenummer, kommunenavn in alle_kommuner:
                if fylkesnummer == f:
                    kombinasjoner.append({
                        "countyCode": fylkesnummer,
                        "countyName": next(x[1] for x in alle_fylker if x[0] == fylkesnummer),
                        "municipalityCode": kommunenummer,
                        "municipalityName": kommunenavn
                    })

    elif args.kommune == ["alle"] and not args.fylke:
        # ALLE KOMMUNER I HELE NORGE
        for fylkesnummer, kommunenummer, kommunenavn in alle_kommuner:
            kombinasjoner.append({
                "countyCode": fylkesnummer,
                "countyName": next(x[1] for x in alle_fylker if x[0] == fylkesnummer),
                "municipalityCode": kommunenummer,
                "municipalityName": kommunenavn
            })

    else:
        # DIREKTE FYLKE OG KOMMUNE (uten "alle")
        if args.fylke:
            for f in args.fylke:
                info = finn_info_fylke(f, postdata)
                if info:
                    kombinasjoner.append({
                        "countyCode": info["Fylkesnummer"],
                        "countyName": info["Fylkesnavn"]
                    })

        if args.kommune:
            for k in args.kommune:
                info = finn_info_kommune(k, postdata)
                if info:
                    kombinasjoner.append({
                        "countyCode": info["Fylkesnummer"],
                        "countyName": info["Fylkesnavn"],
                        "municipalityCode": info["Kommunenummer"],
                        "municipalityName": info["Kommunenavn"]
                    })

    # -------------------------------------------
    # HENT DATA BASERT PÅ KOMBINASJONENE
    # -------------------------------------------
    for item in kombinasjoner:
        countyCode = item["countyCode"]
        countyName = item["countyName"]
        municipalityCode = item.get("municipalityCode")
        municipalityName = item.get("municipalityName")

        for y in år_liste:
            for m in måneder:

                # BYGG RIKTIG API URL
                code = municipalityCode if municipalityCode else countyCode
                url = bygg_url(code, y, m)

                # MAPPE-STRUKTUR
                if municipalityCode:
                    dest_dir = os.path.join(DATA_DIR, f"{countyCode}-{countyName}", f"{municipalityCode}-{municipalityName}")
                else:
                    dest_dir = os.path.join(DATA_DIR, f"{countyCode}-{countyName}")

                os.makedirs(dest_dir, exist_ok=True)

                # FILNAVN
                if municipalityCode:
                    filename = f"{countyCode}-{municipalityCode}-{y}.json" if m is None else f"{countyCode}-{municipalityCode}-{y}-{str(m).zfill(2)}.json"
                else:
                    filename = f"{countyCode}-{y}.json" if m is None else f"{countyCode}-{y}-{str(m).zfill(2)}.json"

                dest = os.path.join(dest_dir, filename)

                print(f"Henter: {url} -> {dest}")
                hent_data(url, dest)


if __name__ == "__main__":
    main()