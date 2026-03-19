@echo off
REM run_viewer.bat - 将数据文件拖放到此脚本上以运行实时查看器

REM 检查是否提供了文件参数
if "%~1"=="" (
    echo 请将数据文件（例如 1.txt）拖放到本脚本上运行。
    pause
    exit /b 1
)

REM 切换到脚本所在目录（项目根目录）
pushd "%~dp0"

REM 检查 python 是否可用
where python >nul 2>&1
if errorlevel 1 (
    echo 未在 PATH 中找到 Python。请安装 Python 并确保其位于 PATH 中。
    pause
    popd
    exit /b 1
)

echo 正在使用文件： "%~1"

REM 运行实时查看器（将脚本路径与拖放文件路径都用引号包裹以支持包含空格的路径）
python "%~dp0finger_trajectory_realtime.py" "%~1"




popdpausenecho 程序已退出。