# Windows 设置

## 当前可用方案

在项目根目录打开 PowerShell：

```powershell
python scripts/check_environment.py
python scripts/init_project.py
python -m unittest discover -s tests -v
```

HTML 与 DOCX 核心实现使用 Python 3 标准库。PDF 兜底与 ATS 文本检查使用项目本地依赖，创建 `.venv`：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

若执行策略阻止激活，可直接用 `.\.venv\Scripts\python.exe`，不要修改全局执行策略。Node 工具在 Windows PowerShell 中使用 `npm.cmd`，因为 `npm.ps1` 可能被策略阻止。

## 可选工具

Bun 和 LaTeX 当前缺失且不是文档导出所需工具。不要为了 PDF 安装 TeX。PDF 优先使用本机 Chrome/Edge，也可使用项目 `.venv` 中的 ReportLab。

路径由 `pathlib` 处理，不写死用户名。CSV 为 UTF-8 BOM，适合德国 Windows Excel。

# 文档导出补充

文档导出无需 LaTeX 或全局软件。推荐在项目目录创建 `.venv`，再运行 `python -m pip install -r requirements.txt`。HTML/DOCX 不依赖第三方包；PDF 优先使用本机 Chrome/Edge，项目本地 ReportLab 作为兜底。先用 `python scripts/check_document_export_environment.py` 确认实际后端。

手动 PDF：在 Edge/Chrome 打开导出的 HTML，按 `Ctrl+P`，选择 A4、100% 缩放、关闭“页眉和页脚”，再选择“另存为 PDF”。
