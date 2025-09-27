def predict_demand(day_of_week: int, is_holiday: bool, temperature_c: float | None) -> float:
    base = 100.0 - (day_of_week * 5)
    if is_holiday:
        base *= 1.2
    if temperature_c is not None:
        base += (temperature_c - 25) * 1.5
    return max(base, 0.0)
