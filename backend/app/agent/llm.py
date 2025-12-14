import os

def llm_reply(message: str) -> str:
    """
    // Stage 1: placeholder LLM implementation.
    // We keep this minimal and swappable.
    """
    mode = os.getenv("LLM_MODE", "mock").lower()

    if mode == "mock":
        return (
            "Mock LLM reply (Stage 1). "
            "Ask me to 'calculate 19*23' to see the calculator tool in Stage 2."
        )

    # // If you later plug a real local model, replace here.
    return "LLM mode not configured. Set LLM_MODE=mock for now."
