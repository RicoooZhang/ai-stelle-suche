# AI 求职系统项目规则

## 事实规则

- 所有匹配结论和正式材料只能使用候选人真实来源材料支持的事实。
- 不得虚构经历、项目、技能、证书、学历、语言水平、管理经验、成果或数字。
- 可以优化表达，不可以创造事实。无法确认的信息标记为 `NEEDS_CONFIRMATION`。
- 材料冲突时不得自行取舍；记录到 `candidate/profile/profile-conflicts.md` 供用户确认。
- `master-profile.md` 是唯一事实主档；`verified-skills.md` 只包含有来源支持的技能。

## 申请安全规则

- 不得自动投递、点击最终提交、发送邮件、上传材料、注册或登录网站。
- 不得绕过验证码、权限、robots.txt 或反自动化机制；不得保存密码、Cookie 或浏览器资料。
- 遇到验证码、隐私授权、登录、上传或最终提交步骤必须停止该动作。
- 材料先进入 `ready_for_review`；只有用户明确批准才能标记 `approved`。
- 即使为 `approved`，最终提交仍必须由用户本人完成。
- 文档导出不得改变申请状态；`draft`、`preparing`、`ready_for_review` 只能生成带 DRAFT 文件名或水印的预览。
- 无标记 final 导出只允许 `approved`/`applied`，且必须通过事实、冲突、禁止声明和关键确认项检查。

## 语言规则

- 项目说明和分析默认中文。德国本地岗位优先德文，国际或英语岗位可用英文。
- 正式材料不得无目的混用语言。德文自然专业、不过度夸张；英文自然明确、非模板化。

## 来源规则

- 岗位记录来源、URL、发现日期；公司研究记录来源及访问日期。
- 区分已确认事实、合理推测和未确认信息；不得把推测写成事实。
- 以公司、岗位、地点、URL、平台编号和描述摘要去重；重复来源保留但只生成一套材料。

## 项目行为规则

- 优先修改正式目录；`upstream-ai-job-search/` 仅作只读参考，不修改其内容。
- 不安装全局软件，不修改系统设置，不上传个人材料，不将个人资料提交到 Git。
- 执行脚本前说明用途；失败必须给出清晰错误，不得伪造成功。
- 脚本使用相对路径、跨平台路径、ISO 日期；核心入口必须可重复执行。
- 不覆盖重要数据；明确更新时先创建备份。不得删除非测试文件。

## Skills

- 可发现的仓库级 Skills 位于 `.agents/skills/`；规范源位于 `skills/`，两者保持同步。
- 使用自然语言或 `$skill-name` 调用，不依赖 Claude slash commands。
- Skills 必须遵守本文件中的事实、隐私和人工提交边界。
- 申请文档导出使用 `export-application-documents`；规范源与 `.agents/skills/` 发现入口必须同时存在。

## 验证命令

- 运行全部测试：`python -m unittest discover -s tests -v`
- 检查环境：`python scripts/check_environment.py`
- 初始化缺失目录：`python scripts/init_project.py`
- 所有脚本均应支持 `--help`。
