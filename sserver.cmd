@echo off
taskkill /FI "WINDOWTITLE eq FinamServer0"

start "FinamServer0" /min python.exe server/finam_server0.py
