@echo off
chcp 65001 >nul
cd /d "D:\games\blog"
set LOG="D:\games\blog\auto_daily.log"

echo [%date% %time%] ====== Blog Daily Auto Pipeline ====== >> %LOG%

echo.
echo [1/3] Running daily_generator.py...
echo [%date% %time%] [1/3] daily_generator >> %LOG%
python scripts\daily_generator.py --push >> %LOG% 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] daily_generator failed with code %errorlevel%
    echo [ERROR] daily_generator failed >> %LOG%
) else (
    echo [OK] daily_generator completed
    echo [OK] daily_generator completed >> %LOG%
)

echo.
echo [2/3] Quick WB API connectivity check...
curl -s --connect-timeout 10 -o NUL "https://catalog.wb.ru/catalog" 2>&1
if %errorlevel% neq 0 (
    echo [WARN] WB API unreachable (VPN?), skipping ozon_selector
    echo [WARN] WB API unreachable, skipping ozon_selector >> %LOG%
) else (
    echo [OK] WB API reachable, running ozon_selector (timeout 10min)...
    echo [%date% %time%] [2/3] ozon_selector >> %LOG%
    timeout /t 600 /nobreak >nul 2>&1 & python scripts\ozon_selector.py --push >> %LOG% 2>&1
    if %errorlevel% neq 0 (
        echo [WARN] ozon_selector failed or timed out
        echo [WARN] ozon_selector failed >> %LOG%
    ) else (
        echo [OK] ozon_selector completed
        echo [OK] ozon_selector completed >> %LOG%
    )
)

echo.
echo [3/3] Pipeline finished. %date% %time%
echo [%date% %time%] Pipeline done >> %LOG%
