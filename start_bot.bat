@echo off
echo Starting Crypto Paper Trading Bot...
echo.
echo Webhook URL: http://localhost:8080/webhook
echo Status URL: http://localhost:8080/status
echo Report URL: http://localhost:8080/report
echo.
echo Press Ctrl+C to stop the bot
echo.
python webhook_handler.py
pause
