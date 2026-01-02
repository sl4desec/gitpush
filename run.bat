@echo off
echo GitPush Araci Baslatiliyor...
python gitpush_app.py
if %errorlevel% neq 0 (
    echo Bir hata olustu. Python yuklu oldugundan emin olun.
    pause
)
