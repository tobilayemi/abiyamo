@echo off
title ABIYAMO - Stop Server
echo.
echo  Stopping ABIYAMO server on port 5000...
echo.
powershell -NoProfile -Command "$conn = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue; if ($conn) { Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host '  Server stopped (PID ' $conn.OwningProcess ').' } else { Write-Host '  No server found running on port 5000.' }"
echo.
pause
