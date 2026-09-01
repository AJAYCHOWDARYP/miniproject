@echo off
echo =======================================================
echo  Pushing Health AI Assistant to GitHub
echo  Repository: https://github.com/AJAYCHOWDARYP/miniproject.git
echo =======================================================
echo.
cd /d "%~dp0"
"C:\Users\ajayk\.gemini\antigravity\scratch\mingit\cmd\git.exe" push -u origin main
echo.
echo =======================================================
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] All files successfully pushed to GitHub!
) else (
    echo [NOTICE] If prompted for credentials, please sign in with your GitHub account or Personal Access Token.
)
echo =======================================================
pause
