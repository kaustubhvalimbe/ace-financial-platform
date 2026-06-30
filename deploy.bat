@echo off
echo.
echo ========================================
echo   Ace Financial Services - Git Deploy
echo ========================================
echo.

cd /d "C:\Kv\Ace\AIS\Claude Development\AFS Website\Ver 61"

echo Adding all files...
git add .

echo.
set /p msg=Enter commit message (or press Enter for "Update"): 
if "%msg%"=="" set msg=Update

echo.
echo Committing: %msg%
git commit -m "%msg%"

echo.
echo Pushing to GitHub...
git push --force

echo.
echo ========================================
echo   DONE! Site will update in 1-2 mins
echo ========================================
echo.
pause
