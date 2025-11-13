# propcloud-dl

Dette prosjektet består av tre kommandolinjeverktøy som sammen utgjør en komplett pipeline for nedlasting og behandling av eiendomsdata.

## Verktøy

- **pc-get.py** – laster ned rådata fra PropCloud  
- **pc-etl.py** – flater ut JSON-data til CSV  
- **pc-hist.py** – henter historikk fra Webatlas  
- **postnummer.csv** – kobler kommunenavn ↔ kommunenummer  

## Mappestruktur

```
matrikkelen/   – rå JSON  
etl/           – flate CSV-filer  
historikk/     – historikkfiler  
```

## pc-get.py

Laster ned transaksjoner fra PropCloud etter fylke/kommune, år og måned.

Eksempel:

```
python pc-get.py --fylke 50 --år 2020:2024 --måned 1:12
```

Output lagres i:

```
matrikkelen/<fylke-navn>/<kommune-navn>/<fylke-kommune-år-måned>.json
```

## pc-etl.py

Flater ut JSON-filer fra matrikkelen/ til én CSV.  
Støtter intervaller (2020:2024) og lister (5001 5007).

Eksempel:

```
python pc-etl.py --kommune 5001 --år 2021:2024
```

Output:

```
etl/eiendomsoverdragelser_kommune-5001_år-2021-2024_flat.csv
```

## pc-hist.py

Henter historiske transaksjoner for gnr/bnr fra Webatlas.  
GID genereres automatisk.

Enkeltoppslag:

```
python pc-hist.py --kommune 5001 --gnr 414 --bnr 307
```

CSV-batch:

```
python pc-hist.py --fil liste.csv
```

CSV må være på formen:

```
kommune,gnr,bnr
```

Output:

```
historikk/kommunenummer-kommunenavn-gnr-bnr-fnr-snr.json
```

## Komplett flyt

```
python pc-get.py --fylke 50 --år 2020:2024
python pc-etl.py --fylke 50
python pc-hist.py --fil unike-gnr-bnr.csv
```

## Avhengigheter

```
pip install requests
```
