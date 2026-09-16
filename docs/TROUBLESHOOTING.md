# 故障排除

- `ModuleNotFoundError: job_system`：从项目根目录运行脚本；测试用 `python -m unittest discover -s tests -v`。
- `npm.ps1 cannot be loaded`：使用 `npm.cmd`；不要为此修改系统执行策略。
- Git `dubious ownership`：这是沙箱用户与桌面用户不同造成的。只读查询可用单次 `git -c safe.directory=<完整路径> -C <路径> ...`；不要修改全局配置。
- PDF/DOCX 未提取：标准库脚本会明确标记 `EXTRACTION_NOT_AVAILABLE`。在 Codex 中调用本地 PDF/文档能力并人工核验，不上传在线转换服务。
- 岗位正文过短：粘贴完整职责和要求，或提供 UTF-8 文件。
- 配置解析失败：`.yaml` 文件使用 JSON-compatible YAML；保持合法 JSON 语法。
- 工作区已存在：系统拒绝覆盖。检查是否为重复岗位并使用现有目录。
- 无法标记 `approved`：必须在用户明确批准后加 `--user-approved`；这仍不会提交申请。
- 浏览受登录/验证码/robots/条款限制：停止自动访问，生成搜索词，让用户手动粘贴 URL 或正文。
- LaTeX/Bun 缺失：它们是可选上游依赖，不阻塞 Markdown/Python 核心。

# 文档导出问题

- final 被拒绝：打开 `exports/export-report.md`，检查申请状态、缺失的审核文件和事实阻塞标记；不要手工绕过。
- 浏览器 PDF 后端崩溃：在普通 PowerShell 重试，或手动打印 HTML；在项目 `.venv` 安装 requirements 后可使用 ReportLab 兜底。
- PDF ATS 检查未测试：当前 Python 缺少 pypdf；激活项目 `.venv` 后重试。
- DOCX 无法视觉渲染：没有 LibreOffice 时，用 Microsoft Word 手工打开检查分页。结构有效不代表视觉 QA 已完成。
- 德文乱码：确认 Markdown 为 UTF-8，并使用本机系统字体；不要引入网络字体或 CDN。
