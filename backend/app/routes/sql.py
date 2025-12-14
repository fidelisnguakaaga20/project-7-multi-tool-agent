# /// Stage 5: debug endpoint for SQL tool
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.tools.sql_tool import SQLTool

router = APIRouter(prefix="/sql", tags=["sql"])
tool = SQLTool()


class SQLQueryIn(BaseModel):
    sql: str


@router.post("/query")
def query_sql(payload: SQLQueryIn):
    try:
        return tool.run({"sql": payload.sql})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
