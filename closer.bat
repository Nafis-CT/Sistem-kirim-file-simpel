@echo off


:: Mematikan semua proses yang bernama python.exe dan ngrok.exe secara paksa (/F)
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM ngrok.exe /T >nul 2>&1

echo Server dan Ngrok telah berhasil dimatikan
echo 3: awoooo...

echo Jendela ini akan tertutup otomatis...
timeout /t 3 >nul
exit