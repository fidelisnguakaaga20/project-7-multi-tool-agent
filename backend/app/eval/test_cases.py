TEST_CASES = [
    {
        "name": "calculator_basic",
        "message": "calculate 19*23",
        "expect": {
            "tool": "calculator",
            "has_answer": True,
        },
    },
    {
        "name": "sql_top_customers",
        "message": "Show top 3 customers by total orders",
        "expect": {
            "tool": "sql",
            "has_answer": True,
        },
    },
    {
        "name": "rag_docs_question",
        "message": "According to my documents, what is my professional summary?",
        "expect": {
            "tool": "rag",
            "citations_required": True,
        },
    },
    {
        "name": "web_latest",
        "message": "latest news about OpenAI",
        "expect": {
            "tool": "web",
            "has_answer": True,
        },
    },
]
