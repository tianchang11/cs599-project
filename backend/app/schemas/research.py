from pydantic import BaseModel
from typing import Optional


class ResearchStart(BaseModel):
    query: str
    deviceId: Optional[str] = None
    fileId: Optional[str] = None
    strategy: Optional[str] = None


class ResearchResponse(BaseModel):
    taskId: str
    strategy: str = "analytical"


class ResearchStatus(BaseModel):
    taskId: str
    status: str
    progress: int = 0
    currentStep: Optional[str] = None
    strategy: str = "analytical"
    qualityScore: Optional[float] = None
    coverageScore: Optional[float] = None
    reportQuality: Optional[float] = None
    iteration: int = 0
