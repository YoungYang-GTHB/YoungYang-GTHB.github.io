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
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def load_resume_yaml() -> dict:
    yaml_path = PROJECT_ROOT / "content" / "resume.yaml"
    if not yaml_path.exists():
        return {}
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


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
        "birthDate": "2002-03",
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
    }

    jobPreferences = {
        "targetRole": "机器人算法工程师 / ROS开发工程师 / 嵌入式软件工程师",
        "targetIndustry": "机器人 / 自动驾驶 / 人工智能 / 高端装备",
        "expectedCity": "西安 深圳 北京",
        "preferredLocations": "西安、深圳、北京、成都、上海",
        "employmentType": "全职",
        "expectedSalary": "面议",
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
        "aiTools": "PyTorch, CNN, 语音识别, 图像处理, 点云处理",
        "databases": "神通数据库",
        "tooling": "Git, Docker, AD, 嘉立创, Inventor, 3D打印",
        "domainKnowledge": "机器人系统设计, 嵌入式开发, 电路设计, 机械设计",
        "notableAchievements": "",
    }

    # ---- 教育经历 ----
    educations = []
    for edu in education:
        educations.append({
            "school": edu.get("school", ""),
            "degree": edu.get("degree", ""),
            "major": edu.get("major", ""),
            "faculty": "",
            "city": "西安" if "西北工业" in edu.get("school", "") else "郑州",
            "country": "中国",
            "startDate": (edu.get("period", " - ").split(" - ")[0] if " - " in edu.get("period", "") else ""),
            "endDate": (edu.get("period", " - ").split(" - ")[1] if " - " in edu.get("period", "") else ""),
            "gpa": edu.get("gpa", ""),
            "ranking": edu.get("rank", ""),
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
            internships.append({
                "company": exp.get("company", ""),
                "title": exp.get("role", ""),
                "city": "",
                "country": "中国",
                "startDate": (exp.get("period", " - ").split(" - ")[0] if " - " in exp.get("period", "") else ""),
                "endDate": (exp.get("period", " - ").split(" - ")[1] if " - " in exp.get("period", "") else ""),
                "description": exp.get("description", "").strip().replace("\n", " "),
                "achievements": "; ".join(exp.get("achievements", [])),
                "technologies": "",
            })

    # ---- 项目经历 ----
    profile_projects = []
    for proj in projects:
        profile_projects.append({
            "name": proj.get("title", ""),
            "role": proj.get("role", ""),
            "organization": "西北工业大学" if "2024" in proj.get("period", "") else "郑州大学",
            "startDate": (proj.get("period", " - ").split(" - ")[0] if " - " in proj.get("period", "") else ""),
            "endDate": (proj.get("period", " - ").split(" - ")[1] if " - " in proj.get("period", "") else ""),
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
        "workExperiences": [],
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
