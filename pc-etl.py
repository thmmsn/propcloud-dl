#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, csv, json, argparse
from glob import iglob

INPUT_ROOT = "matrikkelen"
OUTPUT_ROOT = "etl"


# -----------------------------
# Hjelpefunksjoner
# -----------------------------
def parse_cadestral_id(cid):
    if not cid:
        return (None, None, None, None, None)
    parts = cid.split("-")
    while len(parts) < 5:
        parts.append(None)
    return parts[0], parts[1], parts[2], parts[3], parts[4]


def safe_load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def parse_intervall_eller_liste(verdi):
    if not verdi:
        return []
    if ":" in verdi:
        start, slutt = verdi.split(":")
        return [str(i) for i in range(int(start), int(slutt) + 1)]
    return verdi.split()


def collect(fylker, kommuner, postnumre, år, måneder):
    from glob import iglob
    import json

    def safe_load(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Feil ved lesing av {path}: {e}")
            return []

    def parse_cadestral_id(cid):
        parts = (cid or "").split("-")
        parts += ["0"] * (5 - len(parts))
        return parts[0], parts[1], parts[2], parts[3], parts[4]

    seen = set()
    for f in iglob(os.path.join("matrikkelen", "**", "*-*.json"), recursive=True):
        print(f"Sjekker {f}")
        for t in safe_load(f):
            if not isinstance(t, dict):
                continue

            raw_pc = str(t.get("postalCode") or "").strip()
            if postnumre and (not raw_pc.isdigit() or raw_pc == ""):
                continue
            pc = raw_pc.zfill(4)

            if postnumre and pc not in postnumre:
                continue
            else:
                print(f"Inkluderer {f} (postnummer={pc})")

            key = t.get("documentNumber")
            if key in seen:
                continue
            seen.add(key)

            k, g, b, fn, s = parse_cadestral_id(t.get("cadestralId"))
            yield {
                "date": t.get("date"),
                "år": (t.get("date") or "")[:4],
                "municipalityCode": t.get("municipalityCode"),
                "municipality": t.get("municipality"),
                "postalCode": pc,
                "postalArea": t.get("postalArea"),
                "streetName": t.get("streetName"),
                "houseNumber": t.get("houseNumber"),
                "houseLetter": t.get("houseLetter"),
                "buildingType": t.get("buildingType"),
                "propertyType": t.get("propertyType"),
                "saleType": t.get("saleType"),
                "price": t.get("price"),
                "propertyArea_m2": t.get("propertyArea"),
                "livingArea_m2": t.get("livingArea"),
                "pricePerSquareMeter": t.get("pricePerSquareMeter"),
                "latitude": t.get("latitude"),
                "longitude": t.get("longitude"),
                "countyCode": t.get("countyCode"),
                "gnr": g,
                "bnr": b,
                "fnr": fn,
                "snr": s,
                "documentNumber": key,
                "saleId": t.get("saleId"),
                "source": f,
                "sellerList": t.get("sellerList"),
                "buyerList": t.get("buyerList"),
                "housingCoopNumber": t.get("housingCoopNumber"),
                "housingCoopName": t.get("housingCoopName"),
                "housingCoopUnitCode": t.get("housingCoopUnitCode"),
                "housingCoopId": t.get("housingCoopId"),
                "floor": t.get("floor"),
            }

  # {
  #   "id": 687239,
  #   "contentId": "propcloud-legacy-transaction-2023-15356-1",
  #   "sensorId": "propcloudLegacyTransaction-propcloud-legacy-transaction-2023-15356-1-version1",
  #   "municipality": "Åmli",
  #   "geometry": {
  #     "x": 8.631879676333128,
  #     "y": 58.65904416002613
  #   },
  #   "imageUrl": "",
  #   "sellerList": "[\"Gunvor Helene Oland\",\"Tellef Brødsjømoen\"]",
  #   "buyerList": "[\"Gunvor Helene Oland\"]",
  #   "sellerOrgNumber": "",
  #   "buyerOrgNumber": "",
  #   "fromCompany": 0,
  #   "toCompany": 0,
  #   "cadestralId": "4217-57-22-0-0",
  #   "groupCount": 1,
  #   "housingCoopNumber": "",
  #   "housingCoopName": "",
  #   "housingCoopUnitCode": "H0101",
  #   "housingCoopId": "",
  #   "saleType": "Skifteoppgjør",
  #   "saleId": "2023-15356-1",
  #   "lineId": 1,
  #   "price": 0,
  #   "pricePerSquareMeter": 0,
  #   "livingArea": 144,
  #   "numberOfRooms": 0,
  #   "floor": 1,
  #   "buildingDate": "",
  #   "propertyDate": "1951-09-08",
  #   "propertyArea": 982.2,
  #   "builtUpArea": 0,
  #   "share": 1,
  #   "infoText": "",
  #   "date": "2023-01-05T20:00:00",
  #   "documentNumber": 15356,
  #   "includesBuilding": 0,
  #   "newsletterFormatText": "",
  #   "isHousingCoop": 0,
  #   "groupSaleId": "2023-15356",
  #   "municipalityCode": "4217",
  #   "postalCode": "4863",
  #   "postalArea": "Nelaug",
  #   "country": "Norge",
  #   "streetName": "Nelaugvegen",
  #   "houseNumber": "438",
  #   "houseLetter": "",
  #   "county": "",
  #   "countyCode": "42",
  #   "region": "",
  #   "citySector": "",
  #   "boroughCode": "",
  #   "cityArea": "",
  #   "tradeArea": "",
  #   "tradeAreaId": 0,
  #   "latitude": 58.65904416002613,
  #   "longitude": 8.631879676333128,
  #   "streetId": "",
  #   "streetIdExt": "",
  #   "propertyId": "",
  #   "propertyType": "Bolig",
  #   "buildingId": "",
  #   "buildingType": "Frittliggende enebolig",
  #   "attachedTransactions": "[]",
  #   "syntheticGeography": "0",
  #   "lat_property": 58.65904416002507,
  #   "lon_property": 8.63187967633314,
  #   "withdrawn": "0"
  # },

# -----------------------------
# Hovedfunksjon
# -----------------------------
def main():
    parser = argparse.ArgumentParser(description="Flater ut og dedupliserer eiendomsoverdragelser.")
    parser.add_argument("--fylke", type=str, nargs="*", help="Fylkesnavn eller fylkesnummer (liste eller intervall)")
    parser.add_argument("--kommune", type=str, nargs="*", help="Kommunenavn eller kommunenummer (liste eller intervall)")
    parser.add_argument("--postnummer", type=str, nargs="*", help="Postnummer (liste eller intervall)")
    parser.add_argument("--år", type=str, nargs="*", help="År (liste eller intervall f.eks. 2022:2025)")
    parser.add_argument("--måned", type=str, nargs="*", help="Måned (liste eller intervall 1:12)")
    args = parser.parse_args()

    # Parse alle intervaller/lister
    fylker = []
    kommuner = []
    postnumre = []
    år = []
    måneder = []

    for f in (args.fylke or []):
        fylker.extend(parse_intervall_eller_liste(f))
    for k in (args.kommune or []):
        kommuner.extend(parse_intervall_eller_liste(k))
    for p in (args.postnummer or []):
        postnumre.extend(parse_intervall_eller_liste(p))
    for y in (args.år or []):
        år.extend(parse_intervall_eller_liste(y))
    for m in (args.måned or []):
        måneder.extend(parse_intervall_eller_liste(m))

    # Output-filnavn
    parts = []
    if fylker: parts.append(f"fylke-{'-'.join(fylker)}")
    if kommuner: parts.append(f"kommune-{'-'.join(kommuner)}")
    if postnumre: parts.append(f"postnr-{'-'.join(postnumre)}")
    if år: parts.append(f"år-{'-'.join(år)}")
    if måneder: parts.append(f"mnd-{'-'.join(måneder)}")

    base = "eiendomsoverdragelser"
    if parts:
        base += "_" + "_".join(parts)
    OUTPUT_FILE = os.path.join(OUTPUT_ROOT, f"{base}_flat.csv")

    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    data = list(collect(fylker, kommuner, postnumre, år, måneder))
    if not data:
        print("Ingen data funnet under matrikkelen/")
        return

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        w.writeheader()
        w.writerows(data)

    print(f"Skrev {len(data)} rader til {OUTPUT_FILE}")


if __name__ == "__main__":
    main()