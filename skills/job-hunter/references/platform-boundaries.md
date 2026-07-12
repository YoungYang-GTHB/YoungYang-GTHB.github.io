# Platform Boundaries

Use job platforms as user-authorized information sources, not automation targets.

## Allowed In V1

- User pastes JD text from Boss直聘、猎聘、领英、拉勾、智联、前程无忧、学校就业网, company career pages, or other sources.
- User uploads screenshots, exports, copied tables, or manually saved pages.
- User opens a page in a browser and asks the agent to analyze visible information.
- User manually confirms each external application, message, or profile edit.

## Not Allowed In V1

- No background mass scraping.
- No bypassing login, CAPTCHA, anti-bot, rate limits, or platform restrictions.
- No automatic application submission.
- No automatic recruiter messaging.
- No storing account cookies or credentials inside the skill.
- No claiming platform endorsement or official API access unless the user provides verified integration credentials and terms.

## Recommended Wording

Use:

- "监督式精准投递助手"
- "岗位整理与匹配"
- "生成投递准备清单"
- "用户确认后手动投递"

Avoid:

- "全自动海投"
- "自动刷岗位"
- "保证面试"
- "绕过平台限制"

## Source Handling

For every job post, record:

- platform;
- company;
- title;
- url if available;
- observed_at date;
- source_type: user_paste | screenshot | csv_export | browser_visible | manual_entry;
- raw JD text or summary.
