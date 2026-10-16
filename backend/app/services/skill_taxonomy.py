from collections import defaultdict

SKILL_ALIASES = {
    "reactjs": "React",
    "react.js": "React",
    "react": "React",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "node": "Node.js",
    "spring boot": "Spring Boot",
    "springboot": "Spring Boot",
    "spring": "Spring Framework",
    "mysql": "MySQL",
    "postgreql": "PostgreSQL",
    "mongodb": "MongoDB",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "redis": "Redis",
    "git": "Git",
    "python": "Python",
    "java": "Java",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "c#": "C#",
    "csharp": "C#",
    "django": "Django",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "vuejs": "Vue",
    "vue.js": "Vue",
    "angular": "Angular",
    "tailwind": "Tailwind CSS",
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "ai": "AI",
    "sql": "SQL",
}


class SkillTaxonomy:
    @staticmethod
    def normalize(skill: str) -> str:
        normalized = (skill or "").strip().lower()
        if not normalized:
            return ""
        return SKILL_ALIASES.get(normalized, skill.strip())

    @staticmethod
    def extract_from_text(text: str):
        found = []
        seen = set()
        for token in text.lower().replace("\n", " ").split():
            candidate = SkillTaxonomy.normalize(token)
            if candidate and candidate not in seen:
                found.append(candidate)
                seen.add(candidate)
        return sorted(found)
