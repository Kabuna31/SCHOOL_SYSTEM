"""Generate natural-language comments from averages."""


A_LEVEL_COMMENTS = {
    (5.5, 6.0): "An exceptional performance. Keep it up.",
    (4.5, 5.4): "Outstanding results. Maintain this standard.",
    (3.5, 4.4): "Very good work. Aim even higher.",
    (2.5, 3.4): "Satisfactory. More effort needed.",
    (1.5, 2.4): "Basic. There is room for improvement.",
    (0.0, 1.4): "Needs significant improvement. Seek help.",
}

O_LEVEL_COMMENTS = {
    (80, 100): "An exceptional performance. Keep it up.",
    (70, 79.9): "Outstanding results. Maintain this standard.",
    (60, 69.9): "Very good work. Aim even higher.",
    (50, 59.9): "Satisfactory. More effort needed.",
    (40, 49.9): "Basic. There is room for improvement.",
    (0, 39.9): "Needs significant improvement. Seek help.",
}


def generate_comment(average, is_a_level):
    if average is None:
        return ""
    average = float(average)

    if is_a_level:
        # Use 0–6 scale for A Level points → not grade. Simpler: use percentage.
        # Use O_LEVEL_COMMENTS for consistency.
        table = O_LEVEL_COMMENTS
    else:
        table = O_LEVEL_COMMENTS

    for (low, high), text in table.items():
        if low <= average <= high:
            return text
    return ""