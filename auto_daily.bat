@echo off
chcp 65001 >nul
cd /d "D:\games\blog"
set LOG="D:\games\blog\auto_daily.log"

echo [%date% %time%] ====== Blog Daily Auto Pipeline ====== >> %LOG%

echo.
echo [1/2] Running daily_generator.py...
echo [%date% %time%] [1/2] daily_generator >> %LOG%
python scripts\daily_generator.py --push >> %LOG% 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] daily_generator failed with code %errorlevel%
    echo [ERROR] daily_generator failed >> %LOG%
) else (
    echo [OK] daily_generator completed
    echo [OK] daily_generator completed >> %LOG%
)

echo.
:: Ozon selector: every 3 days (days 3,6,9,12,15,18,21,24,27,30)
set /a DAY_MOD=0
for /f "tokens=2 delims=/" %%a in ("%date%") do set /a DAY_MOD=1%%a %% 3
if %DAY_MOD% equ 0 (
    echo [2/2] Today is 3-day cycle day, running ozon_selector (~10min)...
    echo [%date% %time%] [2/2] ozon_selector >> %LOG%
    python scripts\ozon_selector.py --push >> %LOG% 2>&1
    if %errorlevel% neq 0 (
        echo [WARN] ozon_selector failed
        echo [WARN] ozon_selector failed >> %LOG%
    ) else (
        echo [OK] ozon_selector completed
        echo [OK] ozon_selector completed >> %LOG%
    )
) else (
    echo [2/2] Skipping ozon_selector (next run on 3-day cycle)
    echo [%date% %time%] Skipping ozon_selector (not 3-day cycle) >> %LOG%
)

echo.
echo Pipeline finished. %date% %time%
echo [%date% %time%] Pipeline done >> %LOG%
