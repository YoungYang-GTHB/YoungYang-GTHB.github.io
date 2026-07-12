# Intake Flow

Use intake to prevent shallow recommendations. Do not recommend jobs, rewrite resumes, or score fit until the minimum profile is clear.

## Minimum Required Information

- Name or alias.
- Education: school, degree, major, graduation year or expected graduation.
- Target city or remote preference.
- Target role direction, even if uncertain.
- Hard constraints: internship/full-time, availability, salary floor, visa/work permit if relevant.
- Existing resume or raw experience notes.
- At least three experience assets: project, internship, coursework, competition, club, volunteer, part-time work, self-study, portfolio, or content output.

## Conversation Stages

1. **Snapshot**
   - "你现在最想解决的是优势不清、岗位不清、简历弱、投递少、还是面试表达差？"
   - "你目前最想投的 1-3 类岗位是什么？为什么？"
2. **Experience Mining**
   - Ask about projects, internships, coursework, club work, competitions, portfolio, self-study, and failure/repair stories.
   - For each experience, ask: background, task, personal action, method/tool, result, evidence, and what others trusted them to do.
3. **Preference And Constraints**
   - City, industry, company size, job type, salary, schedule, internship duration, unacceptable work.
4. **Evidence Gap Check**
   - Identify claims that sound attractive but lack proof.
   - Ask for artifacts: links, screenshots, course project files, reports, metrics, teacher/client feedback, or demo.

## Stop Conditions

Stop and ask more if:

- The user only gives personality words such as "responsible" or "hard-working".
- The user asks for resume bullets without real actions/results.
- The user wants "high-paying jobs" but gives no target city, role, or constraints.
- The user asks to fabricate projects, internships, metrics, or awards.

## Intake Output

Write or update:

- `profile.yaml` for stable profile fields.
- `experience-assets.md` for evidence-backed stories.
- `review-log.md` for missing information and next questions.
