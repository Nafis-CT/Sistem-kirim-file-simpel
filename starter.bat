@echo off
echo Mengaktifkan server...
echo :3c ruff awooooooooo

:: 1. Membuat skrip VBS sementara untuk menyembunyikan layar 100%
echo Set WshShell = CreateObject("WScript.Shell") > rahasia.vbs
echo WshShell.Run "cmd /c python app.py", 0, False >> rahasia.vbs
echo WshShell.Run "cmd /c ngrok http 5000", 0, False >> rahasia.vbs

:: 2. Menjalankan skrip rahasia tersebut
wscript rahasia.vbs

:: 3. Menghapus skrip VBS agar rapi kembali
del rahasia.vbs

:: 4. Menunggu 3 detik agar mesin siap
timeout /t 7 /nobreak >nul

:: 5. Membuka Shortcut App Admin di Desktop

start "" "%USERPROFILE%\Desktop\Dashboard Admin.lnk"

exit