#!/usr/bin/env python
from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"
NUMBER_OF_DATE_PARTS = 3
DATE_SEP = "-"
FEBRUARY = 2
CategoryStat = tuple[str, float]
CategoryStats = list[CategoryStat]
StatsResult = tuple[float, float, float, CategoryStats]
FIELD_TYPE = "type"
FIELD_AMOUNT = "amount"
FIELD_DATE = "date"
INCOME_VAL = "income"
COST_VAL = "cost"
Date = tuple[int, int, int]

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}

financial_transactions_storage: list[dict[str, Any]] = []


def parsed_date_to_string(date: tuple[int, int, int] | None) -> str | None:
    if date is None:
        return None

    day, month, year = date
    day_str = str(day).rjust(2, "0")
    month_str = str(month).rjust(2, "0")
    year_str = str(year)

    return DATE_SEP.join((day_str, month_str, year_str))


def is_leap_year(year: int) -> bool:
    """
    Для заданного года определяет: високосный (True) или невисокосный (False).

    :param int year: Проверяемый год
    :return: Значение високосности.
    :rtype: bool
    """
    leap = year % 4 == 0 and year % 100 != 0
    return leap or year % 400 == 0


def check_date_format(maybe_dt: str) -> bool:
    parts = maybe_dt.split("-")
    if len(parts) != NUMBER_OF_DATE_PARTS:
        return False
    if [len(part) for part in parts] != [2, 2, 4]:
        return False
    combined = "".join(parts)
    return all(char in "0123456789" for char in combined)


DAYS_IN_MONTH = (
    31,
    28,
    31,
    30,
    31,
    30,
    31,
    31,
    30,
    31,
    30,
    31,
)


def check_date_bounds(day: int, month: int, year: int) -> bool:
    if month < 1 or month > len(DAYS_IN_MONTH):
        return False

    max_day = DAYS_IN_MONTH[month - 1]
    if month == FEBRUARY and is_leap_year(year):
        max_day = 29

    return 1 <= day <= max_day


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    """
    Парсит дату формата DD-MM-YYYY из строки.

    :param str maybe_dt: Проверяемая строка
    :return: typle формата (день, месяц, год) или None, если дата неправильная.
    :rtype: tuple[int, int, int] | None
    """
    if not check_date_format(maybe_dt):
        return None

    day, month, year = map(int, maybe_dt.split("-"))

    if not check_date_bounds(day, month, year):
        return None

    return day, month, year


def income_handler(amount: float, income_date: str) -> str:
    parsed_date = extract_date(income_date)

    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    if parsed_date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append(
        {
            FIELD_TYPE: INCOME_VAL,
            FIELD_AMOUNT: amount,
            FIELD_DATE: parsed_date,
        }
    )
    return OP_SUCCESS_MSG


CORRECT_PARTS_CATEGORIES_NUMBER = 2


def is_valid_category(category: str) -> bool:
    if "::" not in category:
        return False

    parts = category.split("::")
    if len(parts) != CORRECT_PARTS_CATEGORIES_NUMBER:
        return False

    common_category = parts[0]
    target_category = parts[1]

    if common_category not in EXPENSE_CATEGORIES:
        return False

    return target_category in EXPENSE_CATEGORIES[common_category]


def cost_categories_handler() -> str:
    lines: list[str] = []

    for common_category, targets in EXPENSE_CATEGORIES.items():
        lines.extend(f"{common_category}::{target_category}" for target_category in targets)

    return "\n".join(lines)


def cost_handler(category: str, amount: float, cost_date: str) -> str:
    parsed_date = extract_date(cost_date)

    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    if parsed_date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    if not is_valid_category(category):
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY

    financial_transactions_storage.append(
        {
            FIELD_TYPE: COST_VAL,
            "category": category,
            FIELD_AMOUNT: amount,
            FIELD_DATE: parsed_date,
        }
    )
    return OP_SUCCESS_MSG


def is_not_later(first_date_str: str, second_date_str: str) -> bool:
    first = extract_date(first_date_str)
    second = extract_date(second_date_str)
    if first is None or second is None:
        return False
    first_parsed = [first[2], first[1], first[0]]
    second_parsed = [second[2], second[1], second[0]]
    if first and second:
        return first_parsed <= second_parsed
    return False


def get_transaction_value(transaction: dict[str, Any], target_date: str) -> float:
    transaction_date_str = parsed_date_to_string(transaction[FIELD_DATE])

    if transaction_date_str is None or not is_not_later(transaction_date_str, target_date):
        return float(0)

    amount = transaction[FIELD_AMOUNT]
    if transaction[FIELD_TYPE] == INCOME_VAL:
        return float(amount)
    if transaction[FIELD_TYPE] == COST_VAL:
        return -float(amount)

    return float(0)


def count_capital(date: str) -> float:
    return sum(get_transaction_value(transaction, date) for transaction in financial_transactions_storage)


def count_loss(date: str) -> float:
    total = float(0)

    for transaction in financial_transactions_storage:
        if transaction[FIELD_TYPE] != COST_VAL:
            continue

        transaction_date = parsed_date_to_string(transaction[FIELD_DATE])
        if transaction_date is None:
            continue

        if is_earlier_than_target_date(transaction_date, date):
            total += transaction[FIELD_AMOUNT]

    return total


def count_profit(date: str) -> float:
    total = float(0)

    for transaction in financial_transactions_storage:
        if transaction[FIELD_TYPE] != INCOME_VAL:
            continue

        transaction_date = parsed_date_to_string(transaction[FIELD_DATE])
        if transaction_date is None:
            continue

        if is_earlier_than_target_date(transaction_date, date):
            total += transaction[FIELD_AMOUNT]

    return total


def extract_target_category(category: str) -> str:
    return category.split("::")[1]


def get_cleaned_expense(
        transaction: dict[str, Any],
        date: str,
) -> tuple[str, float] | None:
    if transaction[FIELD_TYPE] != COST_VAL:
        return None

    transaction_date_str = parsed_date_to_string(transaction[FIELD_DATE])
    if transaction_date_str is None:
        return None

    if not is_earlier_than_target_date(transaction_date_str, date):
        return None

    category = extract_target_category(transaction["category"])
    return category, float(transaction[FIELD_AMOUNT])


def extract_category_and_amount(date: str) -> list[tuple[str, float]]:
    categories: dict[str, float] = {}

    for transaction in financial_transactions_storage:
        result = get_cleaned_expense(transaction, date)
        if result:
            category, amount = result
            categories[category] = categories.get(category, float(0)) + amount

    return list(categories.items())


def is_earlier_than_target_date(transaction_date: str, target_date: str) -> bool:
    transaction = extract_date(transaction_date)
    target = extract_date(target_date)
    if transaction is None or target is None:
        return False
    transaction_parsed = [transaction[2], transaction[1]]
    target_parsed = [target[2], target[1]]
    same_month = transaction_parsed == target_parsed
    not_later = transaction[0] <= target[0]

    return same_month and not_later


def stats_handler(date: str) -> StatsResult:
    parsed_date = extract_date(date)
    if parsed_date is None:
        return 0, 0, 0, []

    category_stats = extract_category_and_amount(date)
    category_stats.sort(key=lambda category: category[0])

    return (
        count_capital(date),
        count_loss(date),
        count_profit(date),
        category_stats,
    )


def sum_into_float(maybe_float: str) -> float | None:
    maybe_float = maybe_float.replace(",", ".")
    if len(maybe_float) == 0:
        return None
    if maybe_float[0] == "." or maybe_float[-1] == ".":
        return None
    num_dots = 0
    for char in maybe_float:
        if char == ".":
            num_dots += 1
        elif not char.isdigit():
            return None
    if num_dots > 1:
        return None

    return float(maybe_float)


def format_category_stats(category_stats: CategoryStats) -> str:
    lines = []

    for index, category_stat in enumerate(category_stats, start=1):
        category, amount = category_stat
        lines.append(f"{index}. {category}: {amount:.2f}")

    return "\n".join(lines)


def expense_or_income(amount: float) -> str:
    return "profit" if amount >= 0 else "loss"


def details_handler(date: str) -> str:
    capital, expenses, income, category_stats = stats_handler(date)
    lines = [
        f"Your statistics as of {date}:",
        f"Total capital: {capital:.2f} rubles",
        f"This month, the {expense_or_income(income - expenses)} amounted to {abs(income - expenses):.2f} rubles.",
        f"Income: {income:.2f} rubles",
        f"Expenses: {expenses:.2f} rubles",
        "",
        "Details (category: amount):",
    ]

    if category_stats:
        lines.append(format_category_stats(category_stats))

    return "\n".join(lines)


LENGTH_OF_INCOME_COMMAND = 3
LENGTH_OF_COST_COMMAND = 4
LENGTH_OF_STATS_COMMAND = 2


def income(parts: list[str]) -> str:
    if len(parts) != LENGTH_OF_INCOME_COMMAND or parts[0] != "income":
        return UNKNOWN_COMMAND_MSG

    amount = sum_into_float(parts[1])
    if amount is None:
        return UNKNOWN_COMMAND_MSG

    return income_handler(amount, parts[2])


LENGTH_OF_COST_CATEGORIES_COMMAND = 2


def cost(parts: list[str]) -> str:
    if len(parts) == LENGTH_OF_COST_CATEGORIES_COMMAND:
        if parts[0] == COST_VAL and parts[1] == "categories":
            return cost_categories_handler()
        return UNKNOWN_COMMAND_MSG

    if len(parts) != LENGTH_OF_COST_COMMAND or parts[0] != COST_VAL:
        return UNKNOWN_COMMAND_MSG

    amount = sum_into_float(parts[2])
    if amount is None:
        return UNKNOWN_COMMAND_MSG

    return cost_handler(parts[1], amount, parts[3])


def stats(parts: list[str]) -> str:
    if len(parts) != LENGTH_OF_STATS_COMMAND or parts[0] != "stats":
        return UNKNOWN_COMMAND_MSG

    if extract_date(parts[1]) is None:
        return INCORRECT_DATE_MSG

    return details_handler(parts[1])


def process_command(parts: list[str]) -> str:
    if not parts:
        return UNKNOWN_COMMAND_MSG

    command_name = parts[0]

    if command_name == COST_VAL:
        return cost(parts)
    if command_name == INCOME_VAL:
        return income(parts)
    if command_name == "stats":
        return stats(parts)

    return UNKNOWN_COMMAND_MSG


def main() -> None:
    command = input()
    while command != "exit":
        parts = command.split()
        print(process_command(parts))
        command = input()


if __name__ == "__main__":
    main()
