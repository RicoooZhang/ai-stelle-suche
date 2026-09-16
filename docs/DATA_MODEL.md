# 数据模型

## 岗位

每个岗位为 `data/jobs/<job_id>.json`。字段包括：`job_id`、`fingerprint`、标题/公司标准化值、地点/距离、远程类型、来源/URL/发现及发布日期、语言、合同/资历、薪资、工作许可/签证要求、必需/偏好技能、经验、职责、公司/行业/软件、分数/等级/评分明细、满足/缺失硬条件、可迁移技能、优势、差距、风险、建议、申请语言/状态、`duplicate_of`、备注和更新时间。

岗位指纹使用标准化公司、标题、地点、无追踪参数 URL、平台编号和描述哈希。重复记录保留，`duplicate_of` 指向主记录，主记录保存 `all_source_urls`。

## 公司

每个公司为 `data/companies/<company_id>.json`，字段：`company_id`、`company_name`、`official_name`、`website`、总部/德国地点、行业、产品/服务、规模、所有权、德国实体、中国关联、国际布局、技术/ERP 环境、客户、文化信号、招聘重点、近期信息、来源、更新时间和置信度。事实项标记 `CONFIRMED_FACT`、`REASONABLE_INFERENCE` 或 `UNCONFIRMED`。

## 申请

状态固定为 `discovered`、`reviewing`、`recommended`、`skip`、`preparing`、`ready_for_review`、`approved`、`applied`、`interview`、`rejected`、`withdrawn`、`offer`、`archived`。`approved` 需要用户明确批准；最终投递仍由用户本人完成。

跟踪字段含公司、岗位、来源/URL、发现/截止日期、分数、语言、材料版本、状态、投递日期、最少联系人信息、面试/跟进日期、反馈、拒绝原因、下一步和更新时间。

## 事实

事实状态为 `VERIFIED`、`PARTIALLY_VERIFIED`、`NEEDS_CONFIRMATION`、`CONFLICTING`、`NOT_SUPPORTED`、`DO_NOT_USE`。后四种不得进入正式申请材料；部分验证必须注明边界和来源。
