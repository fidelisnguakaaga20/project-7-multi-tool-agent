import json
from fastapi import APIRouter

from app.eval.evaluator import run_evaluation

router = APIRouter(prefix="/eval", tags=["eval"])


@router.post("/run")
def run_eval():
    report = run_evaluation()

    with open("reports/eval.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report
