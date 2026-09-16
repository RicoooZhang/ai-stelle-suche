# 在 Codex Desktop 中使用本项目

## 用途与共享方式

打开项目目录后，Codex 会读取根目录 `AGENTS.md`。不同任务/对话只要都指向同一个项目目录，就共享磁盘上的候选人资料、岗位、申请和报告；聊天上下文本身不会自动共享，因此新任务应先读取相关文件。项目级 Skills 的官方自动发现位置是 `.agents/skills/`，普通 `skills/` 保存规范源。

在 Codex Desktop 中创建新任务时，选择本项目目录，然后直接使用 `docs/COMMANDS.md` 中的自然语言请求。若刚创建的 Skill 没显示，重启 Codex 或重新打开项目。

## 标准流程

1. 将个人材料手动复制到 `candidate/source-documents/`，然后说“导入 candidate/source-documents 中的全部文件”。
2. 审核 `master-profile.md`、`verified-skills.md`、`source-index.md` 和冲突表。未经验证的信息不可用于正式材料。
3. 说“分析这个岗位：<粘贴正文或 URL>”。遇到登录、验证码或访问限制时，Codex 应停止网页动作并要求粘贴正文。
4. 对 A/B 岗位说“为这个岗位生成完整申请包”；C 岗位先生成策略；D/E 默认不生成完整材料。
5. 审核 `fact-check.md` 和 `source-traceability.md`，确认后材料状态为 `ready_for_review`。
6. 说“生成当前申请材料的预览版”，得到带 DRAFT 标记的 HTML、DOCX 和 PDF；不会改变状态。
7. 用户明确批准后，将状态设为 `approved`，再说“为这个岗位生成最终投递包”。任何事实阻塞都会拒绝 final。
8. 用户本人投递后，说“将这个岗位标记为已投递”。
9. 说“生成本周求职报告”，或运行报告脚本。

## 文档导出

先运行 `python scripts/check_document_export_environment.py`。预览示例：

```powershell
python scripts/export_documents.py --application ".\applications\<company>\<role>" --document all --language de --formats html docx pdf --mode preview
```

详细规则、后端与人工检查见 `docs/DOCUMENT_EXPORT.md`。导出仅写入本地 `exports/`，不发送、不上传、不投递。

## 必须人工完成

- 登录招聘网站、处理验证码与隐私授权。
- 上传简历/求职信、填写敏感表单、点击最终提交。
- 发送申请或跟进邮件。
- 确认工作许可、语言等级、数字成果和材料冲突。
- 将 `ready_for_review` 明确批准为 `approved`，以及最终投递。

## 安全限制

不要让 Codex 保存密码、Cookie、浏览器配置、证件号码或完整签证文件内容。不得把个人材料推送到公开仓库。网络研究必须记录来源并遵守网站规则；不确定时采用人工搜索和粘贴内容。
