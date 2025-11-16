from typing import Any

import pandas as pd

from src.utils import (
    data_range,
    expenses,
    for_df_to_list,
    get_custom_settings,
    get_exchange_rate,
    get_list_currency,
    get_list_stock_prices,
    get_list_stocks,
    income,
)


def web_pages(date: str, operations: pd.DataFrame, ranges: str = "M") -> Any:
    """
    Функция принимает три параметра дату в формате 'YYYY-MM-DD HH:MM:SS', диапазон данных и DataFrame с транзакциями.
    По умолчанию диапазон данных равен одному месяцу (с начала месяца, на который выпадает дата, по саму дату).
    Диапазон данных может быть неделя (W), месяц (M), год (Y), на который приходится дата
    или все данные до указанной даты (ALL).
    Функция предоставляет JSON-ответ содержащий следующие данные:
    Общая сумма расходов.
    Раздел 'Основные', в котором траты по категориям отсортированы по убыванию. Данные предоставляются по 7 категориям
    с наибольшими тратами, траты по остальным категориям суммируются и попадают в категорию 'Основные'.
    Раздел «Переводы и наличные», в котором сумма по категориям «Наличные» и «Переводы» отсортирована по убыванию.
    Общая сумма поступлений.
    Раздел 'Основные', в котором поступления по категориям отсортированы по убыванию.
    Курс валют которые задаются в отдельном файле пользовательских настроек 'user_settings.json'
    Курс акции 5-и публичных компаний S&P500. Компании задаются в отдельном файле пользовательских настроек
    'user_settings.json'.
    """

    answer = {}
    all_operations = for_df_to_list(operations)
    range_operations = data_range(all_operations, date, ranges)
    answer["expenses"] = expenses(range_operations)
    answer["income"] = income(range_operations)
    user_settings = get_custom_settings()
    currency = get_list_currency(user_settings)
    stocks = get_list_stocks(user_settings)
    currency_rates: Any = get_exchange_rate(currency)
    answer["currency_rates"] = currency_rates
    stock_prices: Any = get_list_stock_prices(stocks)
    answer["stock_prices"] = stock_prices

    return answer
