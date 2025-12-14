from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health():
    # // Stage 0: baseline health check
    return {"ok": True}
