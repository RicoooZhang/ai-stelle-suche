# 申请文档导出

## 默认德文简历模板

德文 CV 在未指定模板时默认使用 `german-professional`：

- 注册表：`templates/resume/templates.json`
- 模板配置：`templates/resume/german-professional/template.json`
- HTML/CSS：`templates/resume/german-professional/`
- 支持：德文 CV、A4、单栏、两页目标、preview/final 共用版式
- preview：显示 `DRAFT`
- final：不显示任何水印或草稿标记

模板使用系统 Arial/Helvetica 字体、单行联系方式、统一章节分隔线、右对齐日期、真实标题与编号、分组技能。不得加入照片、图标、技能条、复杂侧栏、外部字体、CDN 或隐藏 ATS 文本。

可显式选择模板；不指定时德文 CV 仍会自动选择它：

```powershell
python scripts/export_documents.py --application ".\candidate\resumes\de" --document cv --language de --formats html docx pdf --mode preview
python scripts/export_documents.py --application ".\candidate\resumes\de" --document cv --language de --formats html docx pdf --mode preview --template german-professional
```

直接候选人简历目录可使用 `export-config.json` 指向同目录中的唯一 Markdown 内容源，避免复制或从 PDF 回写。final 仍要求同目录存在 `status.md`、`fact-check.md` 和 `source-traceability.md`。

## 支持格式与结构

导出链路为 Markdown → 结构化文档模型 → HTML/DOCX/PDF → 本地申请包。支持 `md`、`html`、`docx`、`pdf`，默认输出到 `applications/<company>/<job-title>/exports/`。HTML/DOCX 使用单栏 A4、系统字体、清晰标题和真实列表顺序，不使用照片、图标、技能条、主要内容表格、网络字体或外部 CDN。

当前代码按 Chrome、Edge、WeasyPrint、ReportLab 的顺序尝试 PDF。当前 Codex 会话的浏览器后端因 GPU 沙箱失败，样例实际由 ReportLab 成功生成。Word/LibreOffice/Typst 不作为当前自动后端；完整审计见 `DOCUMENT_EXPORT_AUDIT.md`。

## 项目本地依赖

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

这只安装到项目 `.venv`。HTML 与 DOCX 本身仅用标准库；ReportLab 提供 PDF 兜底，pypdf 提供页数和 ATS 文本检查。不要使用管理员权限或全局安装。

## 生成预览

`draft`、`preparing`、`ready_for_review` 只能预览，文件名包含 `DRAFT` 或文档带 DRAFT 水印：

```powershell
python scripts/export_documents.py --application ".\applications\<company>\<job-title>" --document all --language de --formats md html docx pdf --mode preview
python scripts/export_documents.py --application ".\applications\<company>\<job-title>" --document cv --language de --formats pdf --mode preview
```

## 生成最终版

```powershell
python scripts/build_application_package.py --application ".\applications\<company>\<job-title>" --language de --mode final
```

final 只允许 `approved`/`applied`。`rejected`/`withdrawn` 还需要明确传入 `--force-closed`，事实门禁仍不可绕过。导出不会把状态改成 approved。已有文件默认不覆盖；只有用户明确要求时使用 `--overwrite`。

德文候选人主简历的 final 命令：

```powershell
python scripts/export_documents.py --application ".\candidate\resumes\de" --document cv --language de --formats html docx pdf --mode final
```

只有用户完成内容和 preview 审核后，才可手动把该目录的 `status.md` 改为：

```markdown
- status: approved
```

模板确认、排版确认或要求尝试 final 均不能自动替代该状态批准。

final 可能因以下原因阻止：状态不允许、缺少 `fact-check.md`/`source-traceability.md`、存在 `NOT_SUPPORTED`/`DO_NOT_USE`/未解决 `CONFLICTING`/关键 `NEEDS_CONFIRMATION`、安全档案缺失或材料含禁止字段。原因写入 `export-report.md`。

## 人工检查

- PDF：确认 A4、页数、无裁切/重叠、德文字符正确、文字可选择复制、DRAFT 状态正确；抽取文本核对姓名与至少一个经历标题。
- DOCX：用 Word 打开并确认标题、项目符号、A4、分页和字体；可继续人工编辑，但不要加入未经来源支持的事实。
- HTML：用 Chrome/Edge 打开，打印时关闭浏览器“页眉和页脚”，纸张选 A4、缩放 100%，再另存为 PDF。
- 求职信：确认收件人、地址、日期、Betreff、Anrede 和一页限制。`NEEDS_CONFIRMATION` 必须人工补全，不能猜测。

## 常见问题

- 乱码：保持 Markdown 为 UTF-8，使用系统 Arial/Helvetica；检查目标机器字体。
- 分页异常：缩短冗余文字或调整自然段，不要把正文字号压到 10 pt 以下；避免手工空行堆叠。
- Chrome/Edge 失败：先在普通 PowerShell 运行；也可打开 HTML 后手动打印，或在 `.venv` 安装 requirements 后使用 ReportLab 兜底。
- PDF 检查显示未测试：激活 `.venv` 并安装 requirements，再重新导出。
- DOCX 视觉渲染不可用：用本机 Word 人工打开检查；结构校验通过不等于分页视觉校验通过。

所有导出只保存在本地。工具不发送邮件、不上传、不登录、不点击最终提交。

## 导出报告

成功包中的 `export-report.md` 至少记录：源 Markdown、模板 id/name、preview/final 模式、状态、生成时间、PDF backend、文件列表、PDF 页数和大小、SHA-256 checksums、ATS 验证结果以及 `NOT_SENT_NOT_UPLOADED`。阻塞的 final 尝试记录所有门禁原因，不生成无标记 final 文件。
