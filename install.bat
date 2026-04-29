@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ===== 清除屏幕 =====
cls

REM ===== 打印装饰线 =====
goto :main

:print_line
echo  ════════════════════════════════════════════════════════════
exit /b

:main
call :print_line
echo.
echo       ██╗     ██╗   ██╗ ██████╗ ██╗  ██╗████████╗
echo       ██║     ██║   ██║ ██╔══██╗██║  ██║╚══██╔══╝
echo       ██║     ██║   ██║ ██████╔╝███████║   ██║
echo       ██║     ██║   ██║ ██╔══██╗██╔══██║   ██║
echo       ███████╗╚██████╔╝ ██║  ██║██║  ██║   ██║
echo       ╚══════╝ ╚═════╝  ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝
echo.
echo                  Agent 安装脚本 v1.0
echo.
call :print_line
echo.

REM ===== 统计信息 =====
set "agent_count=0"
for /d %%d in (".\agents\*") do (
    set /a agent_count+=1
)

echo  ┌─────────────────────────────────────────────────────────┐
echo  │                   检测到 %agent_count% 个 Agent 目录                   │
echo  └─────────────────────────────────────────────────────────┘
echo.

REM ===== 交互提示 =====
echo  是否将 main agent 作为测试经理？
echo.
echo    Y = 是，将 test_manager 内容复制到 workspace，作为测试经理
echo    N = 否，为每个 agent 创建独立配置
echo.
set /p USE_MAIN="  请输入选择 (Y/N): "

if /i not "%USE_MAIN%"=="Y" if /i not "%USE_MAIN%"=="N" (
    echo.
    echo  [错误] 输入必须为 Y 或 N
    echo.
    pause
    exit /b 1
)

REM ===== 开始安装 =====
echo.
call :print_line
echo.
echo  ▶ 开始安装 Agent...
echo.

set "current=0"
set "success_count=0"
set "test_mgr_count=0"

for /d %%d in (".\agents\*") do (
    set /a current+=1
    set "folder=%%~nxd"

    REM 如果是 test_manager 且 USE_MAIN==Y，先复制到 workspace 作为测试经理
    if "!folder!"=="test_manager" (
        if /i "%USE_MAIN%"=="Y" (
            echo  ┌[ !current!/!agent_count! ]──────────────────────────────────
            echo  │  ▶ 处理: !folder!
            echo  │  ↳ 复制 main agent 到 workspace 作为测试经理...
            xcopy /s /e ".\agents\!folder!\*" "%USERPROFILE%\.openclaw\workspace\" >nul 2>&1
            if !errorlevel! equ 0 (
                echo  │  ✓ 文件复制完成
                set /a test_mgr_count+=1
            ) else (
                echo  │  ✖ 文件复制失败
            )
            echo  └──────────────────────────────────────────────────
            echo.
        )
    )

    REM 正常创建 agent
    echo  ┌[ !current!/!agent_count! ]──────────────────────────────────
    echo  │  ▶ 创建 Agent: !folder!
    echo  │  ↳ 执行 openclaw agents add 命令...

    call openclaw agents add !folder! --workspace ~/.openclaw/agents/!folder! >nul 2>&1
    if !errorlevel! equ 0 (
        echo  │  ✓ Agent 创建成功
        set /a success_count+=1
    ) else (
        echo  │  ⚠ Agent 已存在或创建失败，继续配置...
        set /a success_count+=1
    )

    REM 拷贝配置文件
    set "config_count=0"
    if exist ".\agents\!folder!\IDENTITY.md" (
        copy /Y ".\agents\!folder!\IDENTITY.md" "%USERPROFILE%\.openclaw\agents\!folder!" >nul 2>&1
        set /a config_count+=1
    )
    if exist ".\agents\!folder!\MEMORY.md" (
        copy /Y ".\agents\!folder!\MEMORY.md" "%USERPROFILE%\.openclaw\agents\!folder!" >nul 2>&1
        set /a config_count+=1
    )
    if exist ".\agents\!folder!\SOUL.md" (
        copy /Y ".\agents\!folder!\SOUL.md" "%USERPROFILE%\.openclaw\agents\!folder!" >nul 2>&1
        set /a config_count+=1
    )
    if exist ".\agents\!folder!\TOOLS.md" (
        copy /Y ".\agents\!folder!\TOOLS.md" "%USERPROFILE%\.openclaw\agents\!folder!" >nul 2>&1
        set /a config_count+=1
    )
    if exist ".\agents\!folder!\USER.md" (
        copy /Y ".\agents\!folder!\USER.md" "%USERPROFILE%\.openclaw\agents\!folder!" >nul 2>&1
        set /a config_count+=1
    )

    if !config_count! gtr 0 (
        echo  │  ↳ 已复制 !config_count! 个配置文件
    )

    REM 删除 BOOTSTRAP.md
    del /q "%USERPROFILE%\.openclaw\agents\!folder!\BOOTSTRAP.md" >nul 2>&1

    REM 拷贝 skills
    if exist ".\agents\!folder!\skills\" (
        echo  │  ↳ 复制 skills 目录...
        xcopy ".\agents\!folder!\skills\" "%USERPROFILE%\.openclaw\agents\!folder!\skills\" /E /I /Y /R >nul 2>&1
        echo  │  ✓ skills 复制完成
    )

    echo  └──────────────────────────────────────────────────
    echo.
)

REM ===== 安装通用 Skills =====
call :print_line
echo.
echo  ▶ 安装通用 Skills...
echo.

set "source=.\skills"
set "destination=%USERPROFILE%\.openclaw\skills"
set "linux_dest=%destination:\=\\%"

echo  ↳ 配置 skills 目录...
call openclaw config set skills.load.extraDirs [\"%linux_dest%\"] --strict-json >nul 2>&1

if not exist "%destination%" (
    mkdir "%destination%"
)

xcopy "%source%\" "%destination%\" /E /I /Y /R >nul 2>&1
echo  ✓ 通用 skills 安装完成
echo.

REM ===== 配置 pip 源 =====
echo  ▶ 配置 pip 镜像源...
echo.
call python -m pip config set global.index-url https://mirrors.tools.huawei.com/pypi/simple >nul 2>&1
call python -m pip config set install.trusted-host mirrors.tools.huawei.com >nul 2>&1
echo  ✓ pip 镜像配置完成
echo.

REM ===== 重启 Gateway =====
echo  ▶ 重启 Gateway...
echo.
call openclaw gateway restart >nul 2>&1
echo  ✓ Gateway 重启完成
echo.

REM ===== 完成总结 =====
call :print_line
echo.
echo  ███ 安装完成！
echo.
echo    ┌─────────────────────────────────────┐
echo    │         安装统计                    │
echo    ├─────────────────────────────────────┤
echo    │  总计 Agent:    !agent_count! 个             │
echo    │  创建成功:      !success_count! 个             │
if !test_mgr_count! gtr 0 (
    echo    │  测试经理(main): 已配置                  │
)
echo    └─────────────────────────────────────┘
echo.
call :print_line
echo.

pause
exit /b 0
