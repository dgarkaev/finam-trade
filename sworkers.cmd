@echo off
taskkill /FI "WINDOWTITLE eq w:*"
cd workers

@REM start "w:ServerStatus" /min python.exe -c "import finam_worker as fw; (fw.workerServerStatus()).do()"
@REM start "w:AllTrades" /min python.exe -c "import finam_worker as fw; (fw.workerAllTrades()).do()"
@REM start "w:Quotes" /min python.exe -c "import finam_worker as fw; (fw.workerQuotes()).do()"
@REM start "w:SimpleCommand" /min python.exe -c "import finam_worker as fw; (fw.workerSimpleCommand()).do()"
@REM start "w:Quotations" /min python.exe -c "import finam_worker as fw; (fw.workerQuotations()).do()"

wt nt --title "w:ServerStatus"  python.exe -c "import finam_worker as fw\; (fw.workerServerStatus()).do()"; ^
nt --title "w:AllTrades" python.exe -c "import finam_worker as fw\; (fw.workerAllTrades()).do()"; ^
nt --title "w:Quotes" python.exe -c "import finam_worker as fw\; (fw.workerQuotes()).do()"; ^
nt --title "w:SimpleCommand" python.exe -c "import finam_worker as fw\; (fw.workerSimpleCommand()).do()"; ^
nt --title "w:Quotations" python.exe -c "import finam_worker as fw\; (fw.workerQuotations()).do()"
@REM nt --title "w:NewsHeader" python.exe -c "import finam_worker as fw\; (fw.workerNewsHeader()).do()"; ^
@REM nt --title "w:Boards" python.exe -c "import finam_worker as fw\; (fw.workerBoards()).do()"; ^
@REM nt --title "w:Securities" python.exe -c "import finam_worker as fw\; (fw.workerSecurities()).do()"; ^
@REM nt --title "w:Pits" python.exe -c "import finam_worker as fw\; (fw.workerPits()).do()"
