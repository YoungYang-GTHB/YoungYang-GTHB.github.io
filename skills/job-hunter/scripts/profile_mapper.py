#!/usr/bin/env python3
"""
profile_mapper — 将私有或示例 resume.yaml 映射为
AI-Resume-Form-Filling-Assistant 标准简历 JSON。

用法:
  python3 profile_mapper.py > profile.json
  python3 profile_mapper.py --compact > profile.json  # 仅非空字段
"""

import sys
import json
import argparse
import re
import os
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PRIVATE_PROFILE_ENV = "JOB_HUNTER_PRIVATE_PROFILE"
PRIVATE_PROFILE_KEYS = {"schema_version", "resume_overrides", "form_profile", "documents"}


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"YAML root must be an object: {path}")
    return loaded


def _deep_merge(base: dict, overlay: dict) -> dict:
    """Return a recursive merge without mutating either input."""
    result = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_private_profile(path: str | Path | None = None) -> dict:
    """Load explicitly-authorized private form data.

    Private fields are never auto-discovered. Callers must pass a path or set
    JOB_HUNTER_PRIVATE_PROFILE so an ordinary public resume export cannot
    accidentally include identity or family data.
    """
    configured = str(path or os.environ.get(PRIVATE_PROFILE_ENV, "")).strip()
    if not configured:
        return {}
    private_path = Path(configured).expanduser()
    if not private_path.is_absolute():
        private_path = PROJECT_ROOT / private_path
    if not private_path.exists():
        raise FileNotFoundError(f"private profile does not exist: {private_path}")
    profile = _load_yaml(private_path)
    unknown = set(profile) - PRIVATE_PROFILE_KEYS
    if unknown:
        raise ValueError(f"unsupported private profile keys: {', '.join(sorted(unknown))}")
    if profile.get("schema_version") != 1:
        raise ValueError("private profile schema_version must be 1")
    for key in ("resume_overrides", "form_profile"):
        if key in profile and not isinstance(profile[key], dict):
            raise ValueError(f"private profile {key} must be an object")
    if "documents" in profile and not isinstance(profile["documents"], list):
        raise ValueError("private profile documents must be a list")
    return profile


def load_resume_yaml(private_profile: dict | None = None) -> dict:
    configured = os.environ.get("RESUME_DATA_PATH", "")
    yaml_path = Path(configured).expanduser() if configured else PROJECT_ROOT / "career" / "site" / "content" / "resume.yaml"
    if not yaml_path.is_absolute():
        yaml_path = PROJECT_ROOT / yaml_path
    if not yaml_path.exists():
        return {}
    data = _load_yaml(yaml_path)
    overrides = (private_profile or {}).get("resume_overrides", {})
    return _deep_merge(data, overrides)


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


def build_profile(compact: bool = False, private_profile_path: str | Path | None = None) -> dict:
    private_profile = load_private_profile(private_profile_path)
    data = load_resume_yaml(private_profile)
    personal = data.get("personal", {})
    application = data.get("application", {})
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
        "fullName": personal.get("name", ""),
        "email": personal.get("email", ""),
        "phoneNumber": personal.get("phone", ""),
        "currentCity": application.get("currentCity", personal.get("location", "")),
        "currentCountry": application.get("currentCountry", ""),
        "highestEducationLevel": application.get("highestEducationLevel", ""),
        "gender": application.get("gender", ""),
        "birthDate": normalize_date(personal.get("birthday", "")),
        "politicalStatus": personal.get("politicalStatus", ""),
        "summary": personal.get("summary", "").strip().replace("\n", " "),
        "hometownCity": (personal.get("hometown", "") or ""),
        "nationality": application.get("nationality", ""),
    }

    contactAndLocation = {
        "hometownCity": (personal.get("hometown", "") or ""),
        "hometownProvince": application.get("hometownProvince", ""),
        "currentAddressLine1": application.get("currentAddressLine1", personal.get("location", "")),
    }

    identityAndAuthorization = {
        "politicalStatus": personal.get("politicalStatus", ""),
        "workAuthorization": application.get("workAuthorization", ""),
    }

    onlinePresence = {
        "githubUrl": personal.get("github", ""),
        "linkedinUrl": personal.get("linkedin", ""),
        "websiteUrl": personal.get("website", ""),
    }

    jobPreferences = {
        "targetRole": application.get("targetRole", ""),
        "targetIndustry": application.get("targetIndustry", ""),
        "expectedCity": application.get("expectedCity", ""),
        "preferredLocations": application.get("preferredLocations", ""),
        "employmentType": application.get("employmentType", ""),
        "expectedSalary": application.get("expectedSalary", ""),
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
        "programmingLanguages": application.get("programmingLanguages", ""),
        "frameworks": application.get("frameworks", ""),
        "aiTools": application.get("aiTools", ""),
        "databases": application.get("databases", ""),
        "tooling": application.get("tooling", ""),
        "domainKnowledge": application.get("domainKnowledge", ""),
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
            "city": edu.get("city", ""),
            "country": edu.get("country", ""),
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
                "country": exp.get("country", ""),
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
            "industry": exp.get("industry", ""),
            "city": "",
            "country": exp.get("country", ""),
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

    # The private file uses the form-filler output schema directly for fields
    # that do not belong in a public resume (identity, family, document index,
    # exact addresses, and similar ATS-only data).
    profile = _deep_merge(profile, private_profile.get("form_profile", {}))
    if private_profile.get("documents"):
        profile["documents"] = private_profile["documents"]

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
    parser.add_argument(
        "--private-profile",
        help=(
            "显式加载私有表单 YAML；也可设置 JOB_HUNTER_PRIVATE_PROFILE。"
            "未指定时绝不自动加载敏感字段"
        ),
    )
    args = parser.parse_args()

    profile = build_profile(compact=args.compact, private_profile_path=args.private_profile)
    json.dump(profile, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
