"""Core application entry points for ZentroMart VoiceOps."""

from typing import Any, Callable


def answer_customer(
    question: str,
    answer_generator: Callable[[str], str],
) -> dict[str, Any]:
    """Generate a customer answer and return a structured result."""
    if not isinstance(question, str) or not question.strip():
        return {
            "success": False,
            "question": question,
            "answer": "Please provide your question so I can help.",
            "error": "empty_question",
        }

    answer = answer_generator(question)

    return {
        "success": True,
        "question": question,
        "answer": str(answer),
        "error": None,
    }
