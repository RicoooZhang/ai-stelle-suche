# 环境检查（2026-08-04）

| 工具 | 存在 | 版本 | 可执行文件 | 必需性 | 缺失影响 | 推荐安装方式（仅手动） |
|---|---|---|---|---|---|---|
| Git | 是 | 2.49.0.windows.1 | `D:\Git\cmd\git.EXE` | 审查参考仓库必需 | 无法克隆/更新参考仓库 | Git for Windows 官方安装器 |
| Python | 是 | 3.13.4 | `C:\Python313\python.exe` | 核心必需 | 核心脚本不可运行 | python.org Windows 安装器 |
| pip | 是 | 25.1.1 | `C:\Python313\Scripts\pip.exe` | 可选 | 当前标准库实现不受影响 | 随 Python 安装；依赖只装入 `.venv` |
| Node.js | 是 | 22.16.0 | `D:\Python\node.EXE` | 可选 | 不影响 Python 核心 | nodejs.org LTS 安装器 |
| npm | 是 | 10.9.2 | `D:\Python\npm.cmd` | 可选 | 不影响 Python 核心；PowerShell 中优先用 `npm.cmd` | 随 Node.js 安装 |
| Bun | 否 | — | — | 上游门户 CLI 才需要 | 不运行丹麦/Bun 门户 CLI | 仅在确需上游 CLI 时按 bun.sh 官方说明手动安装 |
| pdflatex/lualatex/xelatex | 否 | — | — | PDF 可选 | 使用 Markdown；不生成 LaTeX PDF | 仅在需要 PDF 时手动安装 MiKTeX/TeX Live |
| Windows PowerShell | 是 | 5.1.26100.8875 | `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe` | Windows 操作必需 | — | Windows 自带 |
| PowerShell 7 (`pwsh`) | 否 | — | — | 可选 | 使用 Windows PowerShell 5.1 | Microsoft 官方安装说明 |

未安装任何全局软件。重复检查：`python scripts/check_environment.py`。
