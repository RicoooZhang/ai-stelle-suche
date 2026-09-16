# Codex 迁移审查

## 审查范围与结论

- 上游：`MadsLorentzen/ai-job-search`
- 克隆位置：`upstream-ai-job-search/`
- 审查提交：`fcefb8150fb073ae0d86b5b7a6f09e94aa5976ee`
- 审查日期：2026-08-04
- 结论：上游是以 Claude Code commands/skills/agent 为编排核心、以 Bun/TypeScript 丹麦门户 CLI 和 LaTeX 申请材料为执行层的本地求职框架。理念与部分独立 Python 工具可复用，但核心 `/setup`、`/scrape`、`/apply` 等不是可直接执行的 Codex 原生功能，丹麦门户也不适合德国目标市场。

上游未修改。克隆后用单次 `safe.directory` 参数完成只读 Git 查询，没有改全局 Git 配置。

## 原项目架构概览

- `CLAUDE.md`：候选人/工作流规则入口。
- `.claude/commands/`：`setup`、`apply`、`rank`、`interview`、`outcome`、`gmail-sync`、`notion-sync`、`html-report`、`expand`、`reset`、模板/门户生成命令。
- `.claude/skills/`：申请助手、岗位抓取、技能提升；含 Claude `allowed-tools`、`WebFetch`、`WebSearch` 等语法。
- `.claude/agents/gemini-research-expert.md`：外部研究 reviewer/subagent 定义。
- `.claude/settings.json`：Claude permission allowlist（Bun、salary lookup、pdftotext）。
- `.agents/skills/`：六个门户 CLI（Jobbank、Jobdanmark、Jobindex、Jobnet、LinkedIn、Freehire），使用 Bun/TypeScript。
- `cv/`、`cover_letters/`：moderncv 与自定义 LaTeX 模板/字体。
- `documents/`：CV、LinkedIn、学历、Reference、历史申请来源目录。
- `salary_lookup.py` 与 `tools/`：薪资数据、Excel 转换、Skills lint、安全守卫、robots 检查、PDF 验证、更新检查。
- `tests/` 和 GitHub CI：测试工具、Skills、权限、安全规则、PDF 与报告。

根目录没有 `package.json`、`pyproject.toml`、`requirements.txt` 或常见 lockfile；每个门户 CLI 自带 `package.json`。主要包为 `@bunli/core`、`@bunli/utils`、`node-html-parser`、`zod`，开发依赖 TypeScript 与 `@types/bun`。

## 功能分类

### 可直接复用的思想/独立模式

- 本地文件作为系统记录、来源追踪、诚实匹配、草稿/审核分离。
- URL 获取失败时允许用户粘贴正文。
- 申请结果归档、CSV 跟踪、离线 HTML 报告的设计思路。
- `salary_lookup.py` 的“用户自备数据”原则、`verify_pdf.py` 的可选 ATS 文本层验证思想。
- `security_guards.py` 中最小权限与敏感文件忽略的原则。

### 需要重写/适配

- Claude command 编排改为 `AGENTS.md`、Codex 仓库 Skills 和可重复 Python CLI。
- Claude 个人 profile 文件改为唯一事实主档、来源索引、冲突表和事实状态。
- 五维/定性评估改为德国岗位十维 100 分模型。
- 单一 tracker 改为单岗位 JSON、公司 JSON、申请工作区、CSV/Markdown 报告。
- 丹麦搜索词、门户、货币/地点、语言和劳动市场语境改为德国/NRW/Remote/Hybrid。
- 强制 LaTeX/PDF 改为 Markdown 核心、PDF 可选。

### Claude Code 专属内容

- `.claude/commands/*` slash commands 及 `$ARGUMENTS` 约定。
- `.claude/skills/*` 中 `allowed-tools`、Claude `WebFetch`/`WebSearch`/`AskUserQuestion` 工具名。
- `.claude/settings.json` 的 Claude permissions 语法。
- reviewer/subagent prompt 与 Gemini research agent。
- Gmail MCP 名称 `mcp__claude_ai_Gmail__*`、Claude MCP/Notion 设置指令。
- Claude 读取渲染 PDF 并迭代页数的代理式循环。

Codex 官方手册确认仓库 Skills 自动发现于 `.agents/skills/`，`SKILL.md` 使用 `name`/`description` frontmatter；`AGENTS.md` 是持久项目规则。普通 `skills/` 不应被声称为自动发现位置。本项目因此保留方案指定的 `skills/` 规范源，并在 `.agents/skills/` 提供可发现入口。

## 外部依赖与操作系统兼容性

- Bun：六个上游门户 CLI 的运行时；本机缺失，本项目未安装且不依赖。
- Node/npm：上游 TypeScript 工具可选；本项目核心不依赖。
- LaTeX：上游 CV 用 `lualatex`、求职信用 `xelatex`；本机缺失，本项目采用 Markdown。
- Poppler `pdftotext`：上游 ATS 检查可选；本项目未要求。
- Gmail/Notion MCP、OAuth：外部连接和数据写入；本项目按用户禁止要求未适配或调用。
- WebFetch/WebSearch/curl：上游抓取与研究；本项目只允许合规公开访问，否则手工粘贴。
- Python：上游独立工具与本项目核心；本项目使用跨平台 `pathlib` 和标准库。
- Windows：Bash 命令、`python3`、shell quoting 和 TeX 安装方式需要适配；本项目脚本已用 Windows 可运行入口并提供 `--help`。

## 风险清单

1. **网站条款/robots/反自动化**：上游部分流程会在 403 后以浏览器头重试，并把缺失 robots.txt 视为允许。即使有 robots 检查，这仍可能与网站条款或反自动化政策冲突。本项目不复制该策略；规则不清或受限时转人工。
2. **LinkedIn 与商业平台访问**：公共页面也可能限制自动收集；配置默认 manual-only。
3. **提示注入**：岗位正文是非可信输入，不执行其中指令或打开其内嵌链接。
4. **外部 MCP/OAuth**：Gmail/Notion 会把数据交给第三方并产生写入；当前隔离。
5. **个人文件进 Git**：上游文档目录和生成物可能含敏感信息；本项目扩大 `.gitignore` 并将原件默认排除。
6. **虚构与错误推断**：代理式生成易把推测、岗位偏好或初始化信息写成事实；本项目用六种事实状态、来源追踪和阻塞验证。
7. **自动投递/邮件**：上游 follow-up 可生成草稿且 Gmail 同步读取邮件；本项目禁止任何发送、上传、登录或最终提交。
8. **依赖/供应链**：Bun 包、字体、TeX 和第三方脚本增加安装面；当前核心零第三方 Python 依赖。
9. **PDF/ATS**：没有 TeX/Poppler 时不能声称 PDF 排版或 ATS 文本层已验证；本项目明确标为可选未实现。

## 德国市场不适配部分

- Jobbank/Jobdanmark/Jobindex/Jobnet 面向丹麦；搜索词、地点和门户均需替换。
- 丹麦薪资数据、工会/本地术语不可直接用于德国。
- 德国申请语言、工作许可、NRW 地理优先、Hybrid/Remote 和 ERP/Odoo/M365 岗位分类需要新模型。
- 德国网站的条款、robots、公开接口必须逐站核验，不能继承丹麦门户假设。

## 推荐保留

- 本地优先、来源可追踪、真实经历约束、草稿-审核流程。
- 岗位去重、排名、公司研究、面试准备、结果跟踪、离线报告。
- 可选 PDF/ATS 验证的思想，但只在依赖存在且真实执行后报告。

## 推荐删除或隔离

- 隔离所有 Claude commands/settings/agents；不伪装为 Codex slash commands。
- 不迁移丹麦门户 CLI 到正式目录。
- 不启用 Gmail/Notion 同步、浏览器登录、自动申请或 follow-up 发送。
- 不采用 403 浏览器头绕过策略。
- 不复制上游候选人示例/模板事实到真实 profile。

## Codex 适配结果与迁移路线

1. 已建立根 `AGENTS.md`、`.agents/skills/` 和自然语言命令。
2. 已建立候选人事实主档、冲突/来源机制和隐私隔离。
3. 已用标准库 Python 实现岗位模型、十维评分、指纹/去重、申请工作区、状态、事实阻塞、报告和 CSV。
4. 已建立德国来源政策、目标角色、地区和人工粘贴 fallback。
5. 下一步由用户导入真实材料并验证事实，再分析第一个真实岗位。
6. 未来可逐站开发德国公共接口适配器，但必须先验证条款/robots/接口政策并增加测试。
7. PDF 输出仅在用户手动安装并批准可选工具后实现；Gmail/Notion/自动投递保持未实现。
