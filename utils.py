from random import randint


def calculate_roll(formula: dict) -> tuple[int, dict]:
    bonus = formula.get('bonus', 0)
    dices = formula.get('dices', {})
    result = bonus
    dices_result = {
        '2': [], '4': [], '6': [], '8': [],
        '10': [], '12': [], '20': []
    }
    for dice in ['2', '4', '6', '8', '10', '12', '20']:
        count = dices.get(dice, 0)
        if count == 0:
            continue
        for _ in range(count):
            roll = randint(1, int(dice))
            dices_result[dice].append(roll)
            result += roll
    return result, dices_result


def formula_to_string(formula: dict) -> str:
    parts = []
    dices = formula.get('dices', {})
    bonus = formula.get('bonus', 0)
    for dice, count in dices.items():
        if count > 0:
            parts.append(f"{count}d{dice}")
    if bonus != 0:
        parts.append(f"{bonus:+}")
    return ' '.join(parts)


if __name__ == "__main__":
    formula = {
        'dices': {'6': 2, '20': 1},
        'bonus': 3
    }
    print(formula_to_string(formula))
    print("result: ", calculate_roll(formula))
