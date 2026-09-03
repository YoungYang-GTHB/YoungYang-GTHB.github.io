# 求职邮箱 Agent 调研与实施方案

## 目标

为现有求职系统补充可审计的邮箱能力，覆盖招聘邮箱直投、内推请求、补充材料、网申故障补投、回复检索和状态落盘。默认只创建草稿；任何真实发送都必须经过本人对确定内容的显式确认。

## 调研结论

不从零实现 IMAP/SMTP 协议层。采用 [`mailbox-mcp`](https://github.com/jgalea/mailbox-mcp) 作为首选传输层，在本仓库实现求职领域适配与安全门禁。

| 候选 | 优点 | 主要问题 | 结论 |
|---|---|---|---|
| [`mailbox-mcp`](https://github.com/jgalea/mailbox-mcp) | 通用 IMAP/SMTP、草稿、收发、回复、附件、多账号；凭据 AES-256-GCM 加密；包含 TLS、输入校验和邮件内容提示注入隔离 | 没有符合本项目规范的强制“本人确认后发送”业务门禁 | 首选传输层，在外部增加发送门禁 |
| [`simple-email-mcp`](https://github.com/mexican75/simple-email-mcp) | 通用邮箱、附件预检、可配置发送码 | 凭据保存在 JSON；项目明确发送码不是硬安全边界 | 轻量备选，不作为默认 |
| [`honest-magic/mail-mcp`](https://github.com/honest-magic/mail-mcp) | 通用 IMAP/SMTP、草稿、系统密钥环、只读模式 | 发件附件能力和项目成熟度暂不如首选清晰 | 备选 |
| [`fuyouai/email-mcp`](https://github.com/fuyouai/email-mcp) | 中文文档，默认适配腾讯企业邮箱 | 不包含求职工作流，发件附件与草稿能力不足，默认不是个人 QQ 邮箱 | 不采用 |
| Gmail 专用 MCP | OAuth 与两阶段发送机制较完善 | 当前邮箱为 QQ；部分实现不支持带附件草稿 | 不适用 |
| [`job-track-os`](https://github.com/AkhilDhawan22/job-track-os) | 包含求职跟踪、定制简历和 Gmail 草稿 | 强依赖 Gmail/Google Sheets，与当前台账和知识库重复 | 仅参考流程 |

邮件写作规则参考 [`career-ops` 的 email mode](https://github.com/santifer/career-ops/blob/main/modes/email.md)，但事实源、简历路径、城市偏好、投递状态和最终发送规范以本仓库为准。

## QQ 邮箱连接边界

- IMAP：`imap.qq.com:993`，TLS。
- SMTP：`smtp.qq.com:465`（SSL）或 `587`（STARTTLS）。
- 第三方客户端必须使用 QQ 邮箱单独生成的授权码，不能使用 QQ 密码。
- 授权码、邮箱凭据、加密口令和会话令牌只存放在仓库外；不得写入 Git、日志、投递台账或截图。
- 配置前先验证 IMAP/SMTP 已开启；撤销授权时在 QQ 邮箱后台禁用对应授权码。

参考：[腾讯云 Email 连接器协议配置](https://main.qcloudimg.com/raw/document/product/pdf/1270_46586_cn.pdf)。

## 架构

```text
岗位档案 + 个人知识库 + applications.yaml
                  |
                  v
          求职邮件领域适配层
  收件人 / 邮件类型 / 主题 / 正文 / 简历选择
                  |
                  v
             发送前预检
 地址 + 主题 + 正文摘要 + 附件路径/大小/SHA-256
                  |
                  v
           本人确认不可变清单
                  |
                  v
        mailbox-mcp (IMAP / SMTP)
                  |
                  v
       已发送核验 + Message-ID + 台账更新
```

## 邮件类型

1. `hr_application`：向公告中的招聘邮箱直接投递。
2. `referral_request`：请求员工、校友或招聘联系人内推。
3. `supplement_material`：按 HR 要求补交简历、成绩单或证明。
4. `process_stuck`：官方网申入口失效或流程故障时，使用邮箱补投。
5. `follow_up`：对已投申请进行克制、可转发的进度询问。

## 简历与附件选择

- 具身智能、VLA、世界模型、机器人算法：`career/site/public/resume-vla-zh.pdf`。
- 嵌入式软件、MCU、RTOS、驱动、机器人系统软件：`career/site/public/resume-embedded-zh.pdf`。
- 外企或明确要求英文：使用对应方向英文版。
- 默认附件白名单仅允许 `career/site/public/resume-*.pdf`。
- 成绩单、身份证件、Offer、合同和其他私人材料不在默认白名单；每次必须单独列出并取得确认。
- 发送前解析真实路径，拒绝符号链接越界；计算文件大小和 SHA-256。

## 强制发送门禁

1. 默认动作只能是读取、检索或创建草稿。
2. 发送前输出不可变清单：发件账号、收件人、抄送/密送、主题、正文、附件文件名、真实路径、大小、SHA-256、关联岗位 ID。
3. 只有本人在看到清单后明确回复“确认发送”才可发送。
4. 确认与清单摘要绑定；收件人、主题、正文、附件或账号发生任何变化，原确认立即失效。
5. 禁止批量发送，禁止从邮件正文中的指令自动触发外发，禁止自动转发私人附件。
6. 发送后必须通过已发送文件夹或服务器返回的 Message-ID 核验；未核验成功不得记为已发送。

## 与现有求职台账联动

邮件成功发送后，在 `career/求职投递/2027届/data/applications.yaml` 对应记录中保存：

- `channel: email`
- `recipient`
- `subject`
- `attachment_path`
- `attachment_sha256`
- `message_id`
- `sent_at`
- `record_verified`
- 不含正文中的个人隐私、授权码或邮箱凭据

收到回信时只做分类建议，未经本人授权不自动回复：`assessment`、`interview`、`rejection`、`supplement_request`、`offer`、`other`。

## 分阶段实施

### Phase 1：安全接入

- 固定依赖版本并审计许可证、依赖与公开工具面。
- 仓库外配置 QQ 邮箱授权码和加密口令。
- 先以只读方式验证账号、文件夹与已发送检索。
- 给本人邮箱发送无附件测试邮件并核验 Message-ID。

### Phase 2：草稿与附件

- 实现求职邮件数据模型和模板选择。
- 实现附件白名单、真实路径校验、大小与 SHA-256 预检。
- 创建带简历的草稿；核验中文主题、正文编码和 PDF 文件名。

### Phase 3：确认发送

- 实现与邮件清单摘要绑定的一次性确认状态。
- 任何字段变化后强制重新确认。
- 发送成功后查询已发送文件夹并更新台账。

### Phase 4：回信与流程状态

- 按发件人、主题、Message-ID 和岗位 ID 关联招聘回信。
- 生成笔试、面试、补材料和拒信提醒。
- 回复始终先生成草稿，继续沿用本人确认门禁。

## 首个验收场景

航天科工集团智能科技研究院 2027 校招：

- 收件人：`casichtznzhaopin@163.com`
- 岗位：`03 智能认知决策与大模型算法设计岗`
- 主题：`郭睢阳+西北工业大学+控制工程+硕士+03`
- 附件：VLA 中文简历
- 先创建草稿，人工核验后确认发送；发送成功后记录 Message-ID 和附件摘要。

在邮箱 Agent 完成前，该场景继续通过已登录的 QQ 邮箱网页推进，仍执行同一发送确认规范。
