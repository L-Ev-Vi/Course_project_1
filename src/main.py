from typing import Any

from src.reports import spending_by_weekday
from src.services import investment_bank
from src.utils import date_determination, for_df_to_list, get_json, reading_date, reading_from_xlsx
from src.views import web_pages


def main() -> Any:
    """Функция отвечает за основную логику программы."""

    operations = reading_from_xlsx()

    entering_date = input("Выведите дату для анализа транзакций в формате 'DD.MM.YYYY'" "->")
    if entering_date:
        date = reading_date(entering_date)
    else:
        date = date_determination()

    range_analysis = input(
        "Введите диапазон анализа данных: "
        "неделя (W), "
        "месяц (M), "
        "год (Y) "
        "или все данные до указанной даты (ALL) "
        "->"
    )
    events = web_pages(date, operations, range_analysis)
    transactions = for_df_to_list(operations)

    set_a_limit = input(
        "Укажите лимит до которого нужно округлять суммы транзакций "
        "(укажите целое число от 10 до 100 или ровно 1000 ₽) "
        "->"
    )
    if set_a_limit:
        limit = int(set_a_limit)
    else:
        limit = 0
    savings = investment_bank(date, transactions, limit)
    spending_by_day_the_week = spending_by_weekday(operations, date)

    result = get_json({"events": events, "savings": savings, "spending_by_day_the_week": spending_by_day_the_week})
    return result


if __name__ == "__main__":
    print(main())
