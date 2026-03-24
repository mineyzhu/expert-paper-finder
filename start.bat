@echo off
chcp 65001 >nul
echo ================================================
echo   专家文献检索工具 - v1.0
echo ================================================
echo.

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo [1] 检查环境...
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel%==0 (
    echo [OK] Python:
    python --version
    set PY=python
) else (
    python3 --version >nul 2>&1
    if %errorlevel%==0 (
        echo [OK] Python:
        python3 --version
        set PY=python3
    ) else (
        echo [错误] 未找到 Python！
        echo.
        echo 请按以下步骤操作：
        echo 1. 打开浏览器访问: https://www.python.org/downloads/
        echo 2. 下载 Python 3.8 或更高版本
        echo 3. 安装时勾选 "Add Python to PATH"
        echo 4. 安装完成后重新运行本脚本
        echo.
        pause
        exit /b 1
    )
)

echo.
echo [2] 安装依赖...
%PY% -c "import flask,requests,pypinyin" >nul 2>&1
if %errorlevel%==0 (
    echo [OK] 依赖已就绪
) else (
    echo [安装中] 首次使用，安装依赖包...
    %PY% -m pip install flask flask-cors requests pypinyin --user -q
    if %errorlevel% neq 0 (
        echo [错误] 安装失败！
        echo.
        echo 请检查网络连接后重试。
        echo 或者手动在命令提示符(CMD)中运行：
        echo pip install flask flask-cors requests pypinyin
        echo.
        pause
        exit /b 1
    )
    echo [OK] 依赖安装完成
)

echo.
echo [3] 检查文件...
if not exist "scripts\server.py" (
    echo [错误] 找不到 server.py
    echo 请完整解压文件后重试！
    pause
    exit /b 1
)
echo [OK] server.py 存在

echo.
echo ================================================
echo   准备启动服务器...
echo ================================================
echo.
echo   浏览器访问: http://localhost:5000
echo   如果浏览器没有自动打开，请手动复制上面的网址
echo.
echo   按 Ctrl+C 可以停止服务器
echo.
echo ================================================
echo.
echo 正在启动，请稍候...
echo.

REM 启动服务器
%PY% scripts\server.py

echo.
echo 服务器已退出。
pause
