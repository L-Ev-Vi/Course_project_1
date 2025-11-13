import pandas as pd

from utils import (
    for_df_to_list,
    get_average_expenses_per_day,
    get_data_for_last_three_months,
    get_json,
    reading_from_xlsx,
)


def spending_by_weekday(date: str = None, operations: pd.DataFrame = None) -> list:
    """Функция принимает на вход: DataFrame с транзакциями, опциональную дату, в формате 'YYYY-MM-DD'.
    Если дата не передана, то берется текущая дата.
    Функция возвращает JSON-ответ и формирует отчёт в файле формата .xlsx содержащий данные
    с указанием дня недели, даты и средними значениями трат за каждый из дней,
    за последние три месяца от переданной даты."""

    if operations is None:
        operations = reading_from_xlsx()
    all_operations = for_df_to_list(operations)
    three_month_transactions = get_data_for_last_three_months(all_operations, date)
    average_spending_per_day = get_average_expenses_per_day(three_month_transactions)
    json_response = get_json(average_spending_per_day)

    return json_response
