import datetime
import json
import logging
import os
from collections import Counter

import pandas as pd
import requests
from dateutil import parser
from dotenv import load_dotenv
from pandas.core.interchange.dataframe_protocol import DataFrame

logging.basicConfig(
    level=logging.INFO,
    filemode="w",
    filename="logs/x.log",
    encoding="utf-8",
    format="%(asctime)s - %(funcName)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def reading_from_xlsx(path_file: str = "./data/operations.xlsx") -> DataFrame:
    """Функция для считывания данных о банковских операциях из .xlsx-файла (operations.xlsx)
    в табличный формат данных (DataFrame)"""

    ful_path = os.path.abspath(path_file)
    df = pd.read_excel(ful_path)
    return df


def for_df_to_list(df: DataFrame) -> list[dict]:
    """Функция для агрегации и фильтрации данных о банковских операциях. Принимает на вход DataFrame,
    а возвращает преобразованный список"""

    result = []
    try:
        df.fillna(0, inplace=True)
        operations = df.to_dict(orient='records')
        for operation in operations:
            operation["MCC"] = int(operation["MCC"])
            operation["Бонусы (включая кэшбэк)"] = round(float(operation["Бонусы (включая кэшбэк)"]), 2)
            operation["Округление на инвесткопилку"] = round(float(operation["Округление на инвесткопилку"]), 2)
            result.append(operation)
        result = sorted(result, key=lambda x: datetime.datetime.strptime(x["Дата операции"], '%d.%m.%Y %H:%M:%S'),
                        reverse=True)
    except Exception as ex:
        logger.error(ex)
        return result
    return result


def data_range(operations: list[dict], date: str, ranges: str = 'M') -> list[dict]:
    """Функция принимает список транзакций, дату в формате 'YYYY-MM-DD HH:MM:SS' и диапазон,
    по которому происходит сортировка исходного списка. По умолчанию диапазон равен одному месяцу (с начала месяца,
    на который выпадает дата, по саму дату). Диапазон значения может быть неделя (W), месяц (M), год (Y),
    на который приходится дата или все данные до указанной даты (ALL).
    Результатом функции является новый отсортированный список операций"""

    new_list = []

    end_date = datetime.datetime.strptime(parser.parse(date).strftime('%d.%m.%Y'), '%d.%m.%Y')

    day_week = int(end_date.strftime('%w'))
    if day_week == 0:
        day_week = 7
    begin_week = (end_date - datetime.timedelta(day_week - 1)).date()
    begin_month = (end_date - datetime.timedelta(int(parser.parse(date).strftime('%d')) - 1)).date()
    begin_year = datetime.datetime(int(end_date.strftime('%Y')), 1, 1).date()

    if ranges == 'W':
        for operation in operations:
            day = datetime.datetime.strptime(operation["Дата операции"], '%d.%m.%Y %H:%M:%S')
            if begin_week <= day.date() <= end_date.date():
                new_list.append(operation)
    elif ranges == 'M':
        for operation in operations:
            day = datetime.datetime.strptime(operation["Дата операции"], '%d.%m.%Y %H:%M:%S')
            if begin_month <= day.date() <= end_date.date():
                new_list.append(operation)
    elif ranges == 'Y':
        for operation in operations:
            day = datetime.datetime.strptime(operation["Дата операции"], '%d.%m.%Y %H:%M:%S')
            if begin_year <= day.date() <= end_date.date():
                new_list.append(operation)
    elif ranges == 'ALL':
        for operation in operations:
            day = datetime.datetime.strptime(operation["Дата операции"], '%d.%m.%Y %H:%M:%S')
            if day.date() <= end_date.date():
                new_list.append(operation)

    return new_list


def expenses(operations: list[dict]) -> dict:
    """Функция принимает список словарей с транзакциями, и возвращает словарь. В словаре содержится сумма всех расходов,
    раздел 'Основные' в котором траты по категориям отсортированы по убыванию, а траты по остальным категориям
    суммируются и попадают в категорию 'Остальное', и сумма по категориям
    «Наличные» и «Переводы» отсортированные по убыванию"""

    operations_ok = [op for op in operations if op['Статус'] == 'OK']
    c = Counter()
    [c.update({key: value}) for key, value in
     [(op['Категория'], op['Сумма платежа']) for op in operations_ok if op['Сумма платежа'] < 0]]
    spending_categories = []

    if c.items():
        for k, v in c.items():
            spending_categories.append({'Категория': k, 'Сумма': abs(round(v))})

        full_expenses = sum([category['Сумма'] for category in spending_categories])

        transfers_and_cash = [{"category": category['Категория'], "amount": category['Сумма']} for category in
                              spending_categories if category.get('Категория') in ['Наличные', 'Переводы']]

        spending_categories = [category for category in spending_categories if
                               not category.get('Категория') in ['Наличные', 'Переводы']]

        sor_spending_categories = sorted(spending_categories, key=lambda x: x['Сумма'], reverse=True)

        top_categories = []
        rest = []
        for i, category in enumerate(sor_spending_categories):
            if i < 7:
                top_categories.append({"category": category['Категория'],
                                       "amount": category['Сумма']})
            else:
                rest.append(category['Сумма'])

        if rest:
            top_categories.append({"category": 'Остальное',
                                   "amount": sum(rest)})

        if transfers_and_cash:
            transfers_and_cash = sorted(transfers_and_cash, key=lambda x: x['amount'], reverse=True)
            result = {'total_amount': full_expenses, 'main': top_categories, 'transfers_and_cash': transfers_and_cash}
        else:
            result = {'total_amount': sum([category['Сумма'] for category in spending_categories]),
                      'main': top_categories}
    else:
        result = {'total_amount': 0, 'main': []}

    return result


def income(operations: list[dict]) -> dict:
    """Функция принимает список словарей с транзакциями, и возвращает словарь. В словаре содержится общая сумма
    поступлений. Раздел «Основные», в котором поступления по категориям отсортированы по убыванию."""

    operations_ok = [op for op in operations if op['Статус'] == 'OK']
    c = Counter()
    [c.update({key: value}) for key, value in
     [(op['Категория'], op['Сумма платежа']) for op in operations_ok if op['Сумма платежа'] > 0]]
    income_categories = []
    if c.items():
        for k, v in c.items():
            income_categories.append({'Категория': k, 'Сумма': round(v)})

        full_income = sum([category['Сумма'] for category in income_categories])

        top_categories = [{"category": category['Категория'],
                           "amount": category['Сумма']} for category in income_categories]
        sort_top_categories = sorted(top_categories, key=lambda x: x['amount'], reverse=True)
        result = {"total_amount": full_income, "main": sort_top_categories}
    else:
        result = {"total_amount": 0}

    return result


def get_custom_settings(path_file_json: str = './data/user_settings.json') -> dict:
    """Функция преобразует файл-json с ключом 'user_currencies' и 'user_stocks'
    и возвращает словарь пользовательских настроек"""

    path = os.path.abspath(path_file_json)
    with open(path, 'r', encoding='utf-8') as file:
        result = json.load(file)
    return result


def get_list_currency(user_currencies: dict) -> list[str]:
    """Функция принимает словарь с ключом 'user_currencies' и возвращает список пользовательских валют"""

    return user_currencies.get('user_currencies')


def get_list_stocks(user_stocks: dict) -> list[str]:
    """Функция принимает словарь с ключом 'user_stocks' и возвращает список пользовательских акций"""

    return user_stocks.get('user_stocks')


def get_currency_exchange(conv_currency: str, base_currency: str = 'RUB') -> dict:
    """Функция выполняет API запрос на внешний сервис для получения актуального курса валют, и возвращает словарь с
    курсом переданной валюты ('USD', 'EUR', 'CNY', ...) относительно 'RUB'."""

    load_dotenv(".env")
    aip_key = os.getenv("EXC_AIP_KEY")
    url = f"https://api.apilayer.com/exchangerates_data/latest?symbols={base_currency}&base={conv_currency}"
    payload = {}
    headers = {"apikey": f"{aip_key}"}
    response = requests.get(url, headers=headers, data=payload)
    if response.status_code != 200:
        return {
            "currency": conv_currency,
            "rates": '---'}
    else:
        answer = response.json()
        return {
            "currency": conv_currency,
            "rates": round(answer["rates"].get('RUB'), 2)}


def get_exchange_rate(list_currencies: list[str]) -> list:
    """Функция принимает список пользовательских валют, и возвращает список с
        курсом валют ('USD', 'EUR', 'CNY', ...) относительно 'RUB'."""

    result = []
    for conv_currency in list_currencies:
        result.append(get_currency_exchange(conv_currency))
    return result


def get_stock_price(name_action: str) -> dict:
    """Функция выполняет API запрос на внешний сервис для получения актуального курса курс акции
    публичных компаний S&P500 ('AAPL', 'AMZN', 'GOOGL', 'MSFT', 'TSLA', ...)
    и возвращает словарь с курсом акций в 'USD'."""

    load_dotenv(".env")
    aip_key = os.getenv("FMP_AIP_KEY")
    url = f"https://financialmodelingprep.com/stable/aftermarket-trade?symbol={name_action}&apikey={aip_key}"
    response = requests.get(url)
    if response.status_code != 200:
        return {
            "stock": name_action,
            "price": '---'}
    else:
        answer = response.json()
        return {
            "stock": name_action,
            "price": f"{round(answer[0]["price"], 2)} $"}


def get_list_stock_prices(list_stocks: list[str]) -> list:
    """Функция принимает список пользовательских валют, и возвращает список с
        курсом валют ('USD', 'EUR', 'CNY', ...) относительно 'RUB'."""

    result = []
    for stock_price in list_stocks:
        result.append(get_stock_price(stock_price))
    return result
