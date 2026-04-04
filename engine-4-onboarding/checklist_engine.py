import yaml
from datetime import date, timedelta
from pathlib import Path

TEMPLATES_DIR = Path("templates")

def load_template(template_name: str) -> dict:
    path = TEMPLATES_DIR / f"{template_name}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)

def generate_tasks(template_name: str, start_date: date, employee_id: int) -> list[dict]:
    template = load_template(template_name)
    tasks = []
    for task_def in template.get("tasks", []):
        offset = task_def.get("due_offset", 0)
        due_date = start_date + timedelta(days=offset)
        tasks.append({
            "employee_id": employee_id,
            "title": task_def["title"],
            "description": task_def.get("description", ""),
            "assignee": task_def["assignee"],
            "category": task_def.get("category", "general"),
            "due_date": due_date.isoformat(),
            "status": "todo",
        })
    return tasks

def get_available_templates() -> list[str]:
    return [p.stem for p in TEMPLATES_DIR.glob("*.yaml")]
