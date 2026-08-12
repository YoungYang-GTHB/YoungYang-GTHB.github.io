#!/usr/bin/env python3
"""
profile_mapper — 将 docs/ 知识库 + content/resume.yaml 映射为
AI-Resume-Form-Filling-Assistant 标准简历 JSON。

用法:
  python3 profile_mapper.py > profile.json
  python3 profile_mapper.py --compact > profile.json  # 仅非空字段
"""

import sys
import json
import argparse
import re
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def load_resume_yaml() -> dict:
    yaml_path = PROJECT_ROOT / "content" / "resume.yaml"
    if not yaml_path.exists():
        return {}
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize_date(value: str) -> str:
    """把中文或分隔符不一致的日期归一化为 YYYY-MM-DD / YYYY-MM。"""
    text = str(value or "").strip()
    if not text:
        return ""
    numbers = re.findall(r"\d+", text)
    if len(numbers) >= 3:
        return f"{int(numbers[0]):04d}-{int(numbers[1]):02d}-{int(numbers[2]):02d}"
    if len(numbers) >= 2:
        return f"{int(numbers[0]):04d}-{int(numbers[1]):02d}"
    if len(numbers) == 1 and len(numbers[0]) == 4:
        return numbers[0]
    return text


def split_period(value: str) -> tuple[str, str, str]:
    """返回开始时间、结束时间、是否仍在进行。"""
    text = str(value or "").strip()
    parts = re.split(r"\s+-\s+", text, maxsplit=1)
    start = normalize_date(parts[0]) if parts else ""
    raw_end = parts[1].strip() if len(parts) > 1 else ""
    is_current = raw_end in {"至今", "现在", "目前"}
    end = "" if is_current else normalize_date(raw_end)
    return start, end, "是" if is_current else "否"


def join_description(exp: dict) -> str:
    parts = [str(exp.get("description", "")).strip()]
    achievements = [str(item).strip() for item in exp.get("achievements", []) if str(item).strip()]
    if achievements:
        parts.append("；".join(achievements))
    return " ".join(part.replace("\n", " ") for part in parts if part).strip()


def build_profile(compact: bool = False) -> dict:
    data = load_resume_yaml()
    personal = data.get("personal", {})
    education = data.get("education", [])
    projects = data.get("projects", [])
    experience = data.get("experience", [])
    skills = data.get("skills", {})
    awards = data.get("awards", [])
    honors = data.get("honors", [])
    patents = data.get("patents", [])
    certifications = data.get("certifications", [])

    # ---- 基本信息 ----
    profile_personal = {
        "fullName": personal.get("name", "郭睢阳"),
        "email": personal.get("email", "1327217178@qq.com"),
        "phoneNumber": personal.get("phone", "15893346463"),
        "currentCity": (personal.get("location", "") or "").replace("陕西·", "").replace("·", ""),
        "currentCountry": "中国",
        "highestEducationLevel": "硕士",
        "gender": "男",
        "birthDate": normalize_date(personal.get("birthday", "")),
        "politicalStatus": personal.get("politicalStatus", "共青团员"),
        "summary": personal.get("summary", "").strip().replace("\n", " "),
        "hometownCity": (personal.get("hometown", "") or ""),
        "nationality": "汉族",
    }

    contactAndLocation = {
        "hometownCity": (personal.get("hometown", "") or ""),
        "hometownProvince": "河南",
        "currentAddressLine1": (personal.get("location", "") or ""),
    }

    identityAndAuthorization = {
        "politicalStatus": personal.get("politicalStatus", "共青团员"),
        "workAuthorization": "在中国合法工作，无限制",
    }

    onlinePresence = {
        "githubUrl": personal.get("github", "https://github.com/guosuiyang"),
        "linkedinUrl": personal.get("linkedin", ""),
        "websiteUrl": personal.get("website", ""),
    }

    jobPreferences = {
        "targetRole": "具身智能 / VLA / 机器人学习算法工程师 / 嵌入式软件工程师",
        "targetIndustry": "机器人 / 自动驾驶 / 人工智能 / 高端装备",
        "expectedCity": "西安 深圳 北京",
        "preferredLocations": "西安、深圳、北京、成都、上海",
        "employmentType": "全职",
        "expectedSalary": "面议",
        "willingToRelocate": "是" if personal.get("accepts_city_transfer") else "否",
    }

    # ---- 技能 ----
    all_skills = []
    for category, skill_list in skills.items():
        if isinstance(skill_list, list):
            for s in skill_list:
                all_skills.append(f"{s.get('name', '')} ({s.get('level', '')}): {s.get('description', '')}")
    skills_str = "; ".join(all_skills)

    profile_skills = {
        "primarySkills": skills_str,
        "programmingLanguages": "C/C++ (精通), Python (熟练), MATLAB (熟练)",
        "frameworks": "ROS1/ROS2, PyTorch, PyQt5, FreeRTOS",
        "aiTools": "PyTorch, JAX, VLA, WAM, π0.5, X-VLA, Triton, CUDA Graphs",
        "databases": "神通数据库",
        "tooling": "Git, Docker, AD, 嘉立创, Inventor, 3D打印",
        "domainKnowledge": "机器人学习, 算法训练与部署, ROS/ROS2, 嵌入式开发, 电路设计",
        "notableAchievements": "",
    }

    # ---- 教育经历 ----
    educations = []
    for edu in education:
        laboratory = edu.get("laboratory", {}) or {}
        start_date, end_date, _ = split_period(edu.get("period", ""))
        educations.append({
            "school": edu.get("school", ""),
            "degree": edu.get("degree", ""),
            "major": edu.get("major", ""),
            "faculty": edu.get("faculty", ""),
            "city": "西安" if "西北工业" in edu.get("school", "") else "郑州",
            "country": "中国",
            "startDate": start_date,
            "endDate": end_date,
            "gpa": edu.get("gpa", ""),
            "ranking": edu.get("rank", ""),
            "hasLaboratoryExperience": "是" if laboratory.get("has_experience") else "否",
            "laboratory": laboratory.get("name", ""),
            "laboratoryLevel": laboratory.get("level", ""),
            "advisor": laboratory.get("advisor", ""),
            "laboratoryResponsibleTeacher": laboratory.get("responsible_teacher", ""),
            "researchDirection": edu.get("direction", ""),
            "graduationStatus": "预计毕业" if "2027" in edu.get("period", "") else "已毕业",
            "courses": "",
            "description": ", ".join(edu.get("tags", [])),
            "educationType": "统招全日制",
        })

    # ---- 实习经历 ----
    internships = []
    for exp in experience:
        if exp.get("type") == "实习":
            start_date, end_date, is_current = split_period(exp.get("period", ""))
            internships.append({
                "company": exp.get("company", ""),
                "title": exp.get("role", ""),
                "city": "",
                "country": "中国",
                "startDate": start_date,
                "endDate": end_date,
                "isCurrent": is_current,
                "description": join_description(exp),
                "achievements": "; ".join(exp.get("achievements", [])),
                "technologies": "",
            })

    # ---- 正式 / 兼职工作经历 ----
    work_experiences = []
    for exp in experience:
        if exp.get("type") not in {"全职", "兼职", "合同", "自由职业"}:
            continue
        start_date, end_date, is_current = split_period(exp.get("period", ""))
        work_experiences.append({
            "company": exp.get("company", ""),
            "title": exp.get("role", ""),
            "department": "",
            "employmentType": exp.get("type", ""),
            "industry": "机器人 / 人工智能",
            "city": "",
            "country": "中国",
            "startDate": start_date,
            "endDate": end_date,
            "isCurrent": is_current,
            "locationMode": "",
            "description": join_description(exp),
            "achievements": "; ".join(exp.get("achievements", [])),
            "technologies": "",
        })

    # ---- 项目经历 ----
    profile_projects = []
    for proj in projects:
        start_date, end_date, _ = split_period(proj.get("period", ""))
        profile_projects.append({
            "name": proj.get("title", ""),
            "role": proj.get("role", ""),
            "organization": "西北工业大学" if "2024" in proj.get("period", "") else "郑州大学",
            "startDate": start_date,
            "endDate": end_date,
            "description": proj.get("description", "").strip().replace("\n", " "),
            "highlights": "; ".join(proj.get("achievements", [])),
            "technologies": "; ".join(proj.get("technologies", [])),
            "url": "",
        })

    # ---- 补充信息 ----
    awards_text = ""
    for a in awards:
        awards_text += f"{a.get('name', '')} ({a.get('level', '')}, {a.get('year', '')}); "
    for h in honors:
        awards_text += f"{h.get('name', '')} ({h.get('year', '')}); "

    patents_text = ""
    for p in patents:
        patents_text += f"{p.get('name', '')}: {p.get('count', 0)}项; "

    certs_text = ""
    for c in certifications:
        certs_text += f"{c.get('name', '')}: {c.get('score', '')}; "

    additional = {
        "awards": awards_text,
        "patents": patents_text,
        "competitions": awards_text,
    }

    # ---- 证书 ----
    certificates = []
    for c in certifications:
        certificates.append({
            "name": c.get("name", ""),
            "score": c.get("score", ""),
        })

    # ---- 语言 ----
    languages = [
        {"name": "英语", "proficiency": "工作熟练", "testScore": "CET-6 473" if certifications else ""},
        {"name": "中文", "proficiency": "母语", "testScore": ""},
    ]

    profile = {
        "personal": profile_personal,
        "contactAndLocation": contactAndLocation,
        "identityAndAuthorization": identityAndAuthorization,
        "onlinePresence": onlinePresence,
        "jobPreferences": jobPreferences,
        "skills": profile_skills,
        "educations": educations,
        "internships": internships,
        "workExperiences": work_experiences,
        "projects": profile_projects,
        "campusExperiences": [],
        "certificates": certificates,
        "languages": languages,
        "additional": additional,
    }

    if compact:
        return _compact(profile)
    return profile


def _compact(obj):
    """递归删除空值。"""
    if isinstance(obj, dict):
        return {k: _compact(v) for k, v in obj.items() if _not_empty(v)}
    if isinstance(obj, list):
        return [_compact(v) for v in obj if _not_empty(v)]
    return obj


def _not_empty(v):
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, (int, float, bool)):
        return True
    if isinstance(v, (dict, list)):
        return bool(v)
    return True


def main():
    parser = argparse.ArgumentParser(description="生成 form-filler 标准简历 JSON")
    parser.add_argument("--compact", action="store_true", help="去除空字段")
    args = parser.parse_args()

    profile = build_profile(compact=args.compact)
    json.dump(profile, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
