@echo off
cd /D "%~dp0"
cd ..
call ./env/Scripts/activate.bat
cd src
start pythonw screen.py
