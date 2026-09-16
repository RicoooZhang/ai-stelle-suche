# 工作流

1. 用户把原始文件放入 `candidate/source-documents/`。
2. 本地提取并建立 `master-profile.md`、技能、冲突和来源索引。
3. 通过 URL、粘贴文本或本地文件输入岗位；受限网页改为人工粘贴。
4. 标准化到 `data/jobs/`，然后按公司、标题、地点、URL、编号和描述去重。
5. 基于已验证候选人事实计算十维 0–100 分，并解释硬条件、偏好、迁移能力和真实差距。
6. 研究公司并按事实/推测/未知分类。
7. 为非重复岗位创建 `applications/<company>/<role>/`。
8. 先决定是否申请、语言、简历调整和求职信需求，再生成草稿。
9. 对经历、技能、软件、职责、项目、成果、数字、语言、证书、学历和工作许可逐项核查来源。
10. 材料进入 `ready_for_review`，用户人工审核；只有明确批准才标记 `approved`。
11. 在 `ready_for_review` 阶段可用 `export-application-documents` 生成带 DRAFT 标记的 HTML/DOCX/PDF 预览；导出不改变状态。
12. 明确批准并通过 `fact-check.md`、`source-traceability.md`、禁止声明和冲突检查后，才可生成无 DRAFT 的 final 包。
13. 用户本人登录、上传并最终投递；系统不执行这些动作。
14. 用户报告结果后更新状态，生成排名、CSV 和周报；`applied` 可重新导出并由 checksum 记录版本。
