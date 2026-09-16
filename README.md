# AI Job Suche — 德国本地 AI 求职系统

这是一个面向德国就业市场、由 Codex Desktop 维护的本地优先求职工作区。它把候选人事实、岗位、公司、评分、申请草稿、状态和周报分离管理。系统不会自动登录、上传、发送邮件或提交申请。

## 快速开始

```powershell
python scripts/check_environment.py
python scripts/init_project.py
python -m unittest discover -s tests -v
```

1. 将简历、Arbeitszeugnis、Reference Letter 和证书放入 `candidate/source-documents/`。
2. 在 Codex 中说“导入 candidate/source-documents 中的全部文件”。
3. 人工确认 `candidate/profile/` 中的事实、冲突和来源。
4. 粘贴岗位正文，或保存为 UTF-8 文件后运行 `python scripts/analyze_job.py --file <路径> --save`。
5. 人工补全十个评分维度，再评分、去重、创建申请工作区。
6. 审核材料后由用户本人在招聘网站完成最终投递。

## 目录

- `candidate/`：候选人原始材料、事实主档和简历草稿；敏感子目录被 Git 忽略。
- `config/`：目标岗位/地区、来源政策和评分权重。
- `data/`：岗位、公司、申请、搜索、归档和 CSV 导出。
- `applications/`：按公司/岗位组织的申请草稿工作区。
- `reports/`：排名、跟踪和周报。
- `scripts/` 与 `job_system/`：标准库 Python 实现。
- `skills/`：实施方案指定的规范源；`.agents/skills/`：Codex 自动发现入口。
- `upstream-ai-job-search/`：只读参考仓库，不属于正式实现。

详细操作见 `docs/USER_GUIDE_ZH.md`，Codex 使用见 `README_CODEX.md`。
