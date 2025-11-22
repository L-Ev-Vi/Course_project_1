from typing import Any

from src.reports import spending_by_weekday
from src.services import investment_bank
from src.utils import date_determination, for_df_to_list, get_json, get_month, reading_date, reading_from_xlsx
from src.views import web_pages


def main() -> Any:
    """Функция отвечает за основную логику программы."""

    result = {}
    operations = reading_from_xlsx()
    transactions = for_df_to_list(operations)
    entering_date = input("Выведите дату для анализа транзакций в формате 'DD.MM.YYYY' \n->")
    if entering_date:
        date = reading_date(entering_date)
    else:
        date = date_determination()

    range_analysis = input(
        "Введите диапазон анализа данных: \nнеделя (W), \nмесяц (M), \nгод (Y) "
        "\nили все данные до указанной даты (ALL)"
        "\n->"
    )
    events = web_pages(date, operations, range_analysis)
    print(events)
    result["events"] = events

    event_request = input("Рассчитать сумму для инвесткопилки? Да/Нет\n ->")
    if event_request.lower() == "да" or "yes":
        month_payment = input(
            "Укажите месяц в формате 'MM.YYYY', " "для которого необходимо рассчитать сумму в инвесткопилку \n->"
        )
        if month_payment:
            month = get_month(month_payment)
        else:
            month = date_determination()
        set_a_limit = input(
            "Укажите лимит до которого нужно округлять суммы транзакций для \n"
            "(укажите целое число от 10 до 100 или ровно 1000 ₽) \n->"
        )
        if set_a_limit:
            limit = int(set_a_limit)
        else:
            limit = 0
        savings = investment_bank(month, transactions, limit)
        print(savings)
        result["savings"] = savings

    show_average_expenses = input(
        "Показать средние траты в день за последние  3-и месяца от указанной даты? Да/Нет " "\n ->"
    )
    if show_average_expenses.lower() == "да" or "yes":
        entering_date = input("Укажите дату в формате 'DD.MM.YYYY', от которой будет производиться расчёт \n->")
        if entering_date:
            end_date = reading_date(entering_date)
        else:
            end_date = date_determination()
        spending_by_day_the_week = spending_by_weekday(operations, end_date)
        print(spending_by_day_the_week)
        result["spending_by_day_the_week"] = spending_by_day_the_week

    return get_json(result)


if __name__ == "__main__":
    main()
