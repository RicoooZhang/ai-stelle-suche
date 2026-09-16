# 申请文档导出审计

审计日期：2026-08-05（Europe/Berlin）

## 现有项目结论

- 审计前没有 DOCX、HTML 或 PDF 导出实现；`requirements.txt` 声明核心运行时无第三方依赖。
- `generate-application-package`、`tailor-cv`、`write-cover-letter` 只规定生成 Markdown 草稿、事实追踪和审核状态，没有正式文档渲染。
- 根目录当时没有 `applications/` 实例。已有一份德文 CV 位于 `data/jobs/job-85176a16b4bb7cf17b2c/cv-de.md`，包含姓名、联系方式、ENTWURF 引用块、Profil、Berufserfahrung、职位/公司、日期、Schwerpunkt、项目、技能组、Ausbildung、Sprachen、列表和粗体字段。
- 未发现现有求职信 Markdown 实例；工作区生成器支持 `cover-letter-de.md`/`cover-letter-en.md` 名称。

## 本机真实检查

| 工具/库 | 结果 | 位置或说明 |
|---|---|---|
| Microsoft Word | 已安装 | `C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE` |
| Chrome | 已安装 | `C:\Program Files\Google\Chrome\Application\chrome.exe` |
| Edge | 已安装 | `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` |
| LibreOffice | 未发现 | PATH 与常见安装目录均未发现 |
| Pandoc | 未发现 | PATH 未发现 |
| wkhtmltopdf | 未发现 | PATH 未发现 |
| Typst | 未发现 | PATH 未发现 |
| python-docx | 活动系统 Python 未安装 | Codex 随附运行时可用，仅用于样例结构打开验证 |
| WeasyPrint / Playwright / Jinja2 | 未安装 | 活动系统 Python 未发现；实现不要求 Jinja2 |
| pypdf / pdfplumber / reportlab | 活动系统 Python 未安装 | Codex 随附运行时可用 |

活动系统 Python 为 3.13.4。检查是只读的，没有安装软件或修改系统设置。

## PDF 后端评估

1. HTML + Chrome/Edge 是正常 Windows 环境的首选，已实现自动发现和顺序尝试。但在当前 Codex 沙箱会话中，两者均因 GPU 子进程崩溃而失败，未产出 PDF。
2. WeasyPrint 未安装，因此当前不可用；可在项目 `.venv` 中自行安装后由实现自动发现。
3. Word 已安装，但 COM 自动化一次报登录会话错误、两次转换超时。遗留的两个无窗口 Word 进程已按精确 PID 清理，因此当前会话不把 Word 声称为可用自动后端。
4. Typst 未安装。
5. 为完成真实样例验证，使用 Codex 随附的 ReportLab 作为最后兜底。它生成原生文本 A4 PDF，不依赖 LaTeX、网络字体或全局安装。项目 `requirements.txt` 声明 ReportLab 和 pypdf，供项目 `.venv` 使用。

当前样例实际成功后端：`reportlab`。Chrome/Edge 仍保持代码中的优先后端；用户在普通终端运行时可能不受 Codex 沙箱 GPU 限制。

## 无需全局安装的方式

- HTML：Python 标准库 + 仓库内 CSS。
- DOCX：Python 标准库直接写入 OOXML ZIP；不要求 python-docx。
- PDF：本机 Chrome/Edge；或项目 `.venv` 中的 WeasyPrint/ReportLab。
- PDF 文本检查：项目 `.venv` 中的 pypdf。

审计没有改写真实候选人 Markdown，也没有发送、上传或投递任何材料。
