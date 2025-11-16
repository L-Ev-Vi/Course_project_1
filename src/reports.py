from typing import Any

import pandas as pd

from src.utils import (
    for_df_to_list,
    get_average_expenses_per_day,
    get_data_for_last_three_months,
    output_average_expenses_for_day,
)


def spending_by_weekday(operations: pd.DataFrame, date: Any = None) -> Any:
    """Функция принимает на вход: DataFrame с транзакциями, опциональную дату, в формате 'YYYY-MM-DD'.
    Если дата не передана, то берется текущая дата.
    Функция возвращает JSON-ответ и формирует отчёт в файле формата .xlsx содержащий данные
    с указанием дня недели, даты и средними значениями трат за каждый из дней,
    за последние три месяца от переданной даты."""

    all_operations = for_df_to_list(operations)
    three_month_transactions = get_data_for_last_three_months(all_operations, date)
    average_spending_per_day = get_average_expenses_per_day(three_month_transactions)
    result = output_average_expenses_for_day(average_spending_per_day)

    return result
