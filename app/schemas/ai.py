from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    answer: str


class FinanceSummaryOut(BaseModel):
    week_of: str
    summary: str
    highlights: list[str]

