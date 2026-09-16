# 中文用户指南

## 1. 初次检查

在项目根目录运行：

```powershell
python scripts/check_environment.py
python scripts/init_project.py
python -m unittest discover -s tests -v
```

## 2. 导入个人资料

手动把简历、Arbeitszeugnis、Reference Letter 和证书复制到 `candidate/source-documents/`。不要放密码或浏览器数据。然后在 Codex 中说“导入 candidate/source-documents 中的全部文件”，或运行：

```powershell
python scripts/import_candidate_documents.py
```

脚本能本地读取 TXT/MD/JSON/CSV；PDF/DOCX 会明确要求使用本地文档能力。逐项审核 `candidate/profile/`，尤其是来源、冲突、语言等级、工作许可和数字成果。

## 3. 分析第一个岗位

最安全的方法是把完整岗位正文保存为 UTF-8 文本：

```powershell
python scripts/analyze_job.py --file .\job.txt --url "https://来源地址" --source manual --save
```

也可以在 Codex 中直接说“分析这个岗位：<正文>”。如果网站要求登录或验证码，手动复制正文，不允许绕过限制。

根据真实证据给十个维度设置 0–1 评分，保存到岗位 JSON 的 `dimension_ratings`，然后：

```powershell
python scripts/score_job.py .\data\jobs\<job>.json --write
python scripts/deduplicate_jobs.py --write
```

## 4. 生成申请材料

A/B 岗位可创建完整草稿；C 先做策略；D/E 默认不做。运行：

```powershell
python scripts/create_application_workspace.py .\data\jobs\<job>.json
```

在 Codex 中依次要求公司研究、申请策略、简历修改计划、德文或英文草稿、求职信和事实核查。检查 `fact-check.md`、`source-traceability.md` 和所有 `NEEDS_CONFIRMATION`。材料只能到 `ready_for_review`。

## 5. 人工投递与状态

由你本人登录招聘网站、接受隐私条款、上传文件并点击最终提交。完成后再更新本地状态：

```powershell
python scripts/update_application_status.py .\applications\<公司>\<岗位>\status.md applied
```

## 6. 报告与导出

```powershell
python scripts/generate_reports.py
python scripts/export_csv.py
```

CSV 在 `data/exports/`，周报在 `reports/`。测试 SAMPLE 数据不会进入真实统计。
