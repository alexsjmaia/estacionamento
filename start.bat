@echo off
setlocal

if not exist .venv (
    echo Criando ambiente virtual...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Instalando dependencias...
pip install -r requirements.txt

echo Iniciando sistema...
python app.py
pause