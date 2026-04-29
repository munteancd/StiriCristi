@echo off
echo Generating bulletin...
python -m generator.main

echo Copying audio to PWA directory...
if not exist "pwa\public" mkdir "pwa\public"
copy /Y "public\latest.mp3" "pwa\public\"
copy /Y "public\latest.json" "pwa\public\"

echo Starting web server...
python run_server.py
