# Știri Cristi

Aplicație zilnică de buletin de știri vocal în română.

## Categorii de știri

1. **Știri AI** - TechCrunch AI, VentureBeat AI, The Verge AI
2. **Meteo** - Moșnița Veche, Timișoara și Reșița (raport combinat)
3. **Știri Locale** - Moșnița Veche, Timișoara, Caraș-Severin
4. **Știri Internaționale**
5. **Fotbal România** - Superliga și Liga a II-a
6. **Fotbal Internațional** - Anglia, Italia, Germania, Spania + UCL, Europa League, Conference League, Cupa Mondială, Cupa Europeană

## Web PWA (instalabil pe telefon)

### Site live

Aplicația este disponibilă la: **https://munteancd.github.io/StiriCristi/**

### Generare automată

Buletinul este generat automat zilnic la ora **10:00 AM** prin GitHub Actions.

### Instalare pe telefon

1. Deschide https://munteancd.github.io/StiriCristi/ în browserul telefonului
2. În browser, folosește opțiunea "Add to Home Screen" (iOS) sau "Instalează aplicația" (Android)
3. Aplicația va fi accesibilă ca o aplicație nativă

## Dev setup

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements-dev.txt
cp .env.example .env  # completează cheile
pytest
```

## Rulare manuală locală

```bash
python -m generator.main
```

## GitHub Repository

Codul este stocat pe GitHub: https://github.com/munteancd/StiriCristi

Output: `public/latest.mp3` + `public/latest.json`.
