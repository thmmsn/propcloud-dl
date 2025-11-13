# propcloud-dl

Dette prosjektet består av tre kommandolinjeverktøy som sammen utgjør en komplett pipeline for nedlasting og behandling av eiendomsdata.

## Verktøy

- **propcloud-get.py** – laster ned rådata fra PropCloud  
- **propcloud-etl.py** – flater ut JSON-data til CSV  
- **propcloud-hist.py** – henter historikk fra Webatlas  
- **postnummer.csv** – kobler kommunenavn ↔ kommunenummer  

## Mappestruktur

```
matrikkelen/   – rå JSON  
etl/           – flate CSV-filer  
historikk/     – historikkfiler  
```

## propcloud-get.py

Laster ned transaksjoner fra PropCloud etter fylke/kommune, år og måned.

Eksempel:

```
python propcloud-get.py --fylke 50 --år 2020:2024 --måned 1:12
```

Output lagres i:

```
matrikkelen/<fylke-navn>/<kommune-navn>/<fylke-kommune-år-måned>.json
```

## propcloud-etl.py

Flater ut JSON-filer fra matrikkelen/ til én CSV.  
Støtter intervaller (2020:2024) og lister (5001 5007).

Eksempel:

```
python propcloud-etl.py --kommune 5001 --år 2021:2024
```

Output:

```
etl/eiendomsoverdragelser_kommune-5001_år-2021-2024_flat.csv
```

## propcloud-hist.py

Henter historiske transaksjoner for gnr/bnr fra Webatlas.  
GID genereres automatisk.

Enkeltoppslag:

```
python propcloud-hist.py --kommune 5001 --gnr 414 --bnr 307
```

CSV-batch:

```
python propcloud-hist.py --fil liste.csv
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
python propcloud-get.py --fylke 50 --år 2020:2024
python propcloud-etl.py --fylke 50
python propcloud-hist.py --fil unike-gnr-bnr.csv
```

## Avhengigheter

```
pip install requests
```
