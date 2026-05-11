@echo off
cd /d D:\games\blog
echo ===== %date% %time% Ozon选品采集 ===== >> update_log.txt
python scripts\ozon_selector.py >> update_log.txt 2>&1
echo ===== %date% %time% 每日内容生成 ===== >> update_log.txt
python scripts\daily_generator.py --push >> update_log.txt 2>&1
