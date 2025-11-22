import datetime
import json
import logging
import os
import re
from collections import Counter
from functools import wraps
from typing import Any, Callable

import pandas as pd
import requests
from dateutil import parser, relativedelta
from dotenv import load_dotenv

if not os.path.exists("./logs"):
    os.mkdir("./logs")
logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("logs/error.log", "w", "utf-8")
formater = logging.Formatter("%(asctime)s - %(funcName)s - %(levelname)s - %(message)s")
handler.setFormatter(formater)
logger.addHandler(handler)


def reading_from_xlsx(path_file: str = "./data/operations.xlsx") -> pd.DataFrame:
    """Функция для считывания данных о банковских операциях из .xlsx-файла (operations.xlsx)
    в табличный формат данных (DataFrame)"""

    ful_path = os.path.abspath(path_file)
    df = pd.read_excel(ful_path)
    return df


def for_df_to_list(df: pd.DataFrame) -> list[dict]:
    """Функция для агрегации и фильтрации данных о банковских операциях. Принимает на вход DataFrame,
    а возвращает преобразованный список словарей, содержащий информацию о транзакциях."""

    result = []
    try:
        df.fillna(0, inplace=True)
        operations = df.to_dict(orient="records")
        for operation in operations:
            operation["Бонусы (включая кэшбэк)"] = round(float(operation["Бонусы (включая кэшбэк)"]), 2)
            operation["Округление на инвесткопилку"] = round(float(operation["Округление на инвесткопилку"]), 2)
            result.append(operation)
        result = sorted(
            result, key=lambda x: datetime.datetime.strptime(x["Дата операции"], "%d.%m.%Y %H:%M:%S"), reverse=True
        )
    except Exception as ex:
        logger.error(ex)
        return result
    return result


def data_range(operations: list[dict], date: str, ranges: str = "M") -> list[dict]:
    """Функция принимает список транзакций, дату в формате 'YYYY-MM-DD HH:MM:SS' и диапазон,
    по которому происходит сортировка исходного списка. По умолчанию диапазон равен одному месяцу (с начала месяца,
    на который выпадает дата, по саму дату). Диапазон значения может быть неделя (W), месяц (M), год (Y),
    на который приходится дата или все данные до указанной даты (ALL).
    Результатом функции является новый отсортированный список операций"""

    new_list = []

    end_date = datetime.datetime.strptime(parser.parse(date).strftime("%d.%m.%Y"), "%d.%m.%Y")

    day_week = int(end_date.strftime("%w"))
    if day_week == 0:
        day_week = 7
    begin_week = (end_date - datetime.timedelta(day_week - 1)).date()
    begin_month = (end_date - datetime.timedelta(int(parser.parse(date).strftime("%d")) - 1)).date()
    begin_year = datetime.datetime(int(end_date.strftime("%Y")), 1, 1).date()

    if ranges == "W":
        for operation in operations:
            day = datetime.datetime.strptime(operation["Дата операции"], "%d.%m.%Y %H:%M:%S")
            if begin_week <= day.date() <= end_date.date():
                new_list.append(operation)
    elif ranges == "M":
        for operation in operations:
            day = datetime.datetime.strptime(operation["Дата операции"], "%d.%m.%Y %H:%M:%S")
            if begin_month <= day.date() <= end_date.date():
                new_list.append(operation)
    elif ranges == "Y":
        for operation in operations:
            day = datetime.datetime.strptime(operation["Дата операции"], "%d.%m.%Y %H:%M:%S")
            if begin_year <= day.date() <= end_date.date():
                new_list.append(operation)
    elif ranges == "ALL":
        for operation in operations:
            day = datetime.datetime.strptime(operation["Дата операции"], "%d.%m.%Y %H:%M:%S")
            if day.date() <= end_date.date():
                new_list.append(operation)

    return new_list


def expenses(operations: list[dict]) -> dict:
    """Функция принимает список словарей с транзакциями, и возвращает словарь.
    В словаре содержится сумма всех расходов, раздел 'Основные'
    в котором траты по категориям отсортированы по убыванию, а траты по остальным категориям суммируются
    и попадают в категорию 'Остальное', и сумма по категориям «Наличные» и «Переводы» отсортированные по убыванию"""

    operations_ok = [op for op in operations if op["Статус"] == "OK"]
    c: Counter = Counter()
    [
        c.update({key: value})
        for key, value in [(op["Категория"], op["Сумма платежа"]) for op in operations_ok if op["Сумма платежа"] < 0]
    ]
    spending_categories = []

    if c.items():
        for k, v in c.items():
            spending_categories.append({"Категория": k, "Сумма": abs(round(v))})

        full_expenses = sum([category["Сумма"] for category in spending_categories])

        transfers_and_cash = [
            {"category": category["Категория"], "amount": category["Сумма"]}
            for category in spending_categories
            if category.get("Категория") in ["Наличные", "Переводы"]
        ]

        spending_categories = [
            category for category in spending_categories if not category.get("Категория") in ["Наличные", "Переводы"]
        ]

        sor_spending_categories = sorted(spending_categories, key=lambda x: x["Сумма"], reverse=True)

        top_categories = []
        rest = []
        counter = 0
        for category in sor_spending_categories:
            if category["Категория"] == "Различные товары":
                rest.append(category["Сумма"])
            elif counter < 6:
                counter += 1
                top_categories.append({"category": category["Категория"], "amount": category["Сумма"]})
            else:
                rest.append(category["Сумма"])

        if rest:
            top_categories.append({"category": "Остальное", "amount": sum(rest)})

        if transfers_and_cash:
            transfers_and_cash = sorted(transfers_and_cash, key=lambda x: x["amount"], reverse=True)
            result = {"total_amount": full_expenses, "main": top_categories, "transfers_and_cash": transfers_and_cash}
        else:
            result = {
                "total_amount": sum([category["Сумма"] for category in spending_categories]),
                "main": top_categories,
            }
    else:
        result = {"total_amount": 0, "main": []}

    return result


def income(operations: list[dict]) -> dict:
    """Функция принимает список словарей с транзакциями, и возвращает словарь. В словаре содержится общая сумма
    поступлений. Раздел «Основные», в котором поступления по категориям отсортированы по убыванию."""

    operations_ok = [op for op in operations if op["Статус"] == "OK"]
    c: Counter = Counter()
    [
        c.update({key: value})
        for key, value in [(op["Категория"], op["Сумма платежа"]) for op in operations_ok if op["Сумма платежа"] > 0]
    ]
    income_categories = []
    if c.items():
        for k, v in c.items():
            income_categories.append({"Категория": k, "Сумма": round(v)})

        full_income = sum([category["Сумма"] for category in income_categories])

        top_categories = [
            {"category": category["Категория"], "amount": category["Сумма"]} for category in income_categories
        ]
        sort_top_categories = sorted(top_categories, key=lambda x: x["amount"], reverse=True)
        result = {"total_amount": full_income, "main": sort_top_categories}
    else:
        result = {"total_amount": 0}

    return result


def get_custom_settings(path_file_json: str = "./data/user_settings.json") -> dict:
    """Функция преобразует файл-json с ключом 'user_currencies' и 'user_stocks'
    и возвращает словарь пользовательских настроек"""

    path = os.path.abspath(path_file_json)
    with open(path, "r", encoding="utf-8") as file:
        result = json.load(file)
    return dict(result)


def get_list_currency(user_currencies: dict) -> list[str]:
    """Функция принимает словарь с ключом 'user_currencies' и возвращает список пользовательских валют"""

    return list(user_currencies["user_currencies"])


def get_list_stocks(user_stocks: dict) -> list[str]:
    """Функция принимает словарь с ключом 'user_stocks' и возвращает список пользовательских акций"""

    return list(user_stocks["user_stocks"])


def get_currency_exchange(conv_currency: str, base_currency: str = "RUB") -> dict:
    """Функция выполняет API запрос на внешний сервис для получения актуального курса валют, и возвращает словарь с
    курсом переданной валюты ('USD', 'EUR', 'CNY', ...) относительно 'RUB'."""

    load_dotenv(".env")
    aip_key = os.getenv("EXC_AIP_KEY")
    url = f"https://api.apilayer.com/exchangerates_data/latest?symbols={base_currency}&base={conv_currency}"
    payload: dict[str, Any] = {}
    headers = {"apikey": f"{aip_key}"}
    response = requests.get(url, headers=headers, data=payload)
    if response.status_code != 200:
        return {"currency": conv_currency, "rates": "---"}
    else:
        answer = response.json()
        return {"currency": conv_currency, "rates": f"{round(answer["rates"].get('RUB'), 2)} ₽"}


def get_exchange_rate(list_currencies: list[str]) -> list[dict[str, str]]:
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
        return {"stock": name_action, "price": "---"}
    else:
        answer = response.json()
        return {"stock": name_action, "price": f"{round(answer[0]["price"], 2)} $"}


def get_list_stock_prices(list_stocks: list[str]) -> list:
    """Функция принимает список пользовательских валют, и возвращает список с
    курсом валют ('USD', 'EUR', 'CNY', ...) относительно 'RUB'."""

    result = []
    for stock_price in list_stocks:
        result.append(get_stock_price(stock_price))
    return result


def get_json(result: list | dict) -> Any:
    """Функция принимает данные в виде списка или словаря и возвращает данные в формате json."""

    json_response = json.dumps(result, indent=4, ensure_ascii=False)
    return json_response


def get_billing_month(operations: list[dict], date: str) -> list[dict[str, Any]]:
    """Функция принимает список транзакций, и дату в формате 'YYYY-MM' по которой происходит сортировка
    исходного списка. Результатом функции является новый отсортированный список с банковскими операциями совершёнными
    в указанном месяце"""

    new_list = []
    pattern = re.compile(f"{parser.parse(date).strftime('%m.%Y')}")
    for operation in operations:
        str_date = parser.parse(operation["Дата операции"], dayfirst=True).strftime("%d.%m.%Y")
        if pattern.search(str_date):
            new_list.append(operation)
    return new_list


def get_rounding_difference(operations: list[dict[str, Any]], date: str, limit: int) -> dict:
    """Функция принимает список транзакций, дату в формате 'YYYY-MM' и предел,
    до которого нужно округлять суммы операций (целое число).
    Функция фильтрует список по статусу операций 'ОК', и рассчитывает остаток округления суммы по каждой
    успешной операции. Результатом функции является словарь с суммой общего остатка от операций за месяц."""

    amount_of_savings = 0.0
    operations_expenses = [op for op in operations if op.get("Статус") == "OK" if op["Сумма платежа"] < 0]
    for operation in operations_expenses:
        if limit < 100:
            if abs(operation["Сумма платежа"]) > limit:
                remains = ((abs(operation["Сумма платежа"]) * 100) % 100) / 100
                if (abs(operation["Сумма платежа"]) - remains) % 100 < limit:
                    rounding_up = limit - (((abs(operation["Сумма платежа"]) - remains) % 100) + remains)
                    amount_of_savings += rounding_up
        elif limit == 100:
            if abs(operation["Сумма платежа"]) > limit:
                remains = ((abs(operation["Сумма платежа"]) * 100) % 100) / 100
                if (abs(operation["Сумма платежа"]) - remains) % 100 != 0:
                    rounding_up = limit - (((abs(operation["Сумма платежа"]) - remains) % 100) + remains)
                    amount_of_savings += rounding_up
        elif limit == 1000:
            if abs(operation["Сумма платежа"]) > limit:
                remains = ((abs(operation["Сумма платежа"]) * 100) % 100) / 100
                if (abs(operation["Сумма платежа"]) - remains) % 1000 != 0:
                    rounding_up = limit - (((abs(operation["Сумма платежа"]) - remains) % 1000) + remains)
                    amount_of_savings += rounding_up
    date = parser.parse(date).strftime("%m.%Y")
    return {date: {"amount_of_savings": round(amount_of_savings, 2)}}


def report(file: str = "result_report") -> Any:
    """Декоратор для регистрации выполнения функций.
    Формирует отчёт в файле формата .xlsx из данных которые можно преобразовать в DataFrame.
    Сообщение о результате работы декоратора выводится в файл .txt с тем же названием, что .xlsx файл."""

    def wrapper(func: Callable) -> Any:
        @wraps(func)
        def inner(*args: Any, **kwargs: Any) -> Any:
            log_result = logging.getLogger("log_result")
            log_result.setLevel(logging.INFO)
            log_handler = logging.FileHandler(f"data/{file}.txt", "w", "utf-8")
            log_format = logging.Formatter("%(asctime)s - %(funcName)s - %(levelname)s - %(message)s")
            log_handler.setFormatter(log_format)
            log_result.addHandler(log_handler)
            try:
                result = func(*args, **kwargs)
                df = pd.DataFrame(result)
            except Exception as ex:
                log_result.error(f"The report has not been generated {ex}")
                return {}
            else:
                log_result.info(f"The report in the data/{file}.xlsx file has been successfully generated")
                df.to_excel(f"data/{file}.xlsx", sheet_name="ОТЧЁТ", index=False)
                return result

        return inner

    return wrapper


def get_data_for_last_three_months(operations: list[dict], date: Any = None) -> list[dict[str, Any]]:
    """Функция принимает список транзакций, и дату в формате 'YYYY-MM-DD' от которой происходит выборка данных из
    исходного списка. Если дата не передана, то берется текущая дата.
    Результатом функции является новый отсортированный список с банковскими операциями,
    совершёнными за последние три месяца (от переданной даты)."""

    if date is None:
        date = datetime.datetime.today()
        date = parser.parse(date.strftime("%d.%m.%Y %H:%M:%S")[:11], dayfirst=True)
    else:
        date = datetime.datetime.strptime(date, "%Y-%m-%d")
    three_months_ago = date - relativedelta.relativedelta(months=3)
    operations_in_three_months = []
    operations = [op for op in operations if op["Статус"] == "OK" if op["Сумма платежа"] < 0]
    for op in operations:
        if three_months_ago <= parser.parse(op["Дата операции"][:11], dayfirst=True) <= date:
            operations_in_three_months.append(op)
    return operations_in_three_months


@report()
def get_average_expenses_per_day(operations: list[dict]) -> dict[str, list]:
    """Функция принимает список транзакций. Результатом функции является словарь в виде DataFrame содержащий данные
    с указанием дня недели, даты и средними значениями трат за каждый из дней."""

    dates = []
    for op in operations:
        if op["Дата операции"]:
            if parser.parse(op["Дата операции"][:11], dayfirst=True).strftime("%d.%m.%Y") in dates:
                continue
            else:
                dates.append(parser.parse(op["Дата операции"][:11], dayfirst=True).strftime("%d.%m.%Y"))
    day_week = []
    average_expenses = []
    for date in dates:
        amount_expenses = []
        for op in operations:
            if parser.parse(op["Дата операции"][:11], dayfirst=True) == parser.parse(date, dayfirst=True):
                amount_expenses.append(abs(op["Сумма платежа"]))
        day_week.append(parser.parse(date, dayfirst=True).strftime("%A %d.%m.%Y"))
        average_expenses.append(round(sum(amount_expenses) / len(amount_expenses), 2))

    return {"day_week": day_week, "average_expenses": average_expenses}


def output_average_expenses_for_day(expenses_per_day: dict) -> list[dict]:
    """Функция принимает словарь со средними значениями трат за каждый из дней.
    Результатом функции является словарь содержащий данные с указанием дня недели,
    даты и средними значениями трат за каждый из дней."""

    result = []
    for day_week, average_expenses in zip(expenses_per_day["day_week"], expenses_per_day["average_expenses"]):
        result.append({"day_week": day_week, "average_expenses": average_expenses})
    return result


def date_determination() -> str:
    """Функция возвращает строку в виде даты в формате YYYY-MM-DD"""
    return datetime.datetime.today().strftime("%Y-%m-%d")


def reading_date(date_str: str) -> str:
    """Функция принимает строку в виде даты в формате DD.MM.YYYY,
    и возвращает строку в виде даты в формате YYYY-MM-DD"""

    return parser.parse(date_str, dayfirst=True).strftime("%Y-%m-%d")


def get_month(date_str: str) -> str:
    """Функция принимает строку в виде даты в формате MM.YYYY,
    и возвращает строку в виде даты в формате YYYY-MM-DD"""

    return datetime.datetime.strptime(date_str, "%m.%Y").strftime("%Y-%m-%d")
