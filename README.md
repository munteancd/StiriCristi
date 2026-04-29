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

## Web PWA (instalabil pe telefon)

### Generare și server local

```bash
# Windows
generate_and_serve.bat

# Sau manual:
python -m generator.main
python run_server.py
```

Serverul va fi accesibil la:
- **Local:** http://localhost:8000
- **Rețea:** http://[IP-ul-tău]:8000 (pentru acces de pe telefon pe aceeași rețea WiFi)

### Instalare pe telefon

1. Asigură-te că telefonul și PC-ul sunt pe aceeași rețea WiFi
2. Rulează `generate_and_serve.bat` sau `python run_server.py`
3. Pe telefon, deschide browserul și accesează URL-ul de rețea afișat
4. În browser, folosește opțiunea "Add to Home Screen" sau "Instalează aplicația"

### GitHub Repository

Codul este stocat pe GitHub: https://github.com/munteancd/StiriCristi

Note: GitHub Pages nu este disponibil pe planul curent, deci folosim server local pentru PWA.

Output: `public/latest.mp3` + `public/latest.json`.
