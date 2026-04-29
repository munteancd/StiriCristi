# Știri Cristi

Aplicație zilnică de buletin de știri vocal în română.

## Categorii de știri

1. **Meteo** - Moșnița Veche, Timișoara și Reșița (raport combinat)
2. **Știri Locale** - Moșnița Veche, Timișoara, Caraș-Severin
3. **Știri Internaționale**
4. **Fotbal România** - Superliga și Liga a II-a
5. **Fotbal Internațional** - Anglia, Italia, Germania, Spania + UCL, Europa League, Conference League, Cupa Mondială, Cupa Europeană

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

Output: `public/latest.mp3` + `public/latest.json`.
