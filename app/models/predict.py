from pydantic import BaseModel

class PredictIn(BaseModel):
    day_of_week: int
    is_holiday: bool = False
    temperature_c: float | None = None

class PredictOut(BaseModel):
    demand: float
