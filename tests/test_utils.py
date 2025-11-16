import datetime
import json
import os
from unittest.mock import mock_open, patch

import pandas as pd
import pytest
from dotenv import load_dotenv

from src.utils import (
    data_range,
    date_determination,
    expenses,
    for_df_to_list,
    get_average_expenses_per_day,
    get_billing_month,
    get_currency_exchange,
    get_custom_settings,
    get_data_for_last_three_months,
    get_exchange_rate,
    get_json,
    get_list_currency,
    get_list_stock_prices,
    get_list_stocks,
    get_rounding_difference,
    get_stock_price,
    income,
    output_average_expenses_for_day,
    reading_date,
    reading_from_xlsx,
    report,
)


@patch("pandas.read_excel")
def test_reading_from_xlsx(mock_df, file_xlsx):
    mock_df.return_value = file_xlsx
    assert reading_from_xlsx("./data/operations.xlsx") == file_xlsx
    mock_df.assert_called_once_with(os.path.abspath("./data/operations.xlsx"))


def test_for_df_to_list(file_xlsx):
    arg = pd.DataFrame(file_xlsx)
    assert for_df_to_list(arg) == [
        {
            "Дата операции": "01.01.2018 20:27:51",
            "Дата платежа": "04.01.2018",
            "Номер карты": "*7197",
            "Статус": "OK",
            "Сумма операции": -316.0,
            "Валюта операции": "RUB",
            "Сумма платежа": -316.0,
            "Валюта платежа": "RUB",
            "Кэшбэк": 5.0,
            "Категория": "Красота",
            "MCC": 5977,
            "Описание": "OOO Balid",
            "Бонусы (включая кэшбэк)": 6.0,
            "Округление на инвесткопилку": 0.0,
            "Сумма операции с округлением": 316.0,
        },
        {
            "Дата операции": "01.01.2018 12:49:53",
            "Дата платежа": "01.01.2018",
            "Номер карты": 0,
            "Статус": "OK",
            "Сумма операции": -3000.0,
            "Валюта операции": "RUB",
            "Сумма платежа": -3000.0,
            "Валюта платежа": "RUB",
            "Кэшбэк": 0.0,
            "Категория": "Переводы",
            "MCC": 0,
            "Описание": "Линзомат ТЦ Юность",
            "Бонусы (включая кэшбэк)": 0.0,
            "Округление на инвесткопилку": 0.0,
            "Сумма операции с округлением": 3000.0,
        },
    ]


def test_for_xlsx_to_list_error():
    arg = pd.DataFrame({"name": ["empty frame"]})
    assert for_df_to_list(arg) == []


@pytest.mark.parametrize(
    "date, ranges, result",
    [
        (
            "2025-10-10 19:47:12",
            "W",
            [
                {
                    "Дата операции": (
                        (
                            (datetime.datetime.strptime("10.10.2025 00:00:00", "%d.%m.%Y %H:%M:%S"))
                            - datetime.timedelta(days=x)
                        ).strftime("%d.%m.%Y %H:%M:%S")
                    )
                }
                for x in range(0, 5)
            ],
        ),
        (
            "2025-10-12 19:47:12",
            "W",
            [
                {
                    "Дата операции": (
                        (
                            (datetime.datetime.strptime("12.10.2025 00:00:00", "%d.%m.%Y %H:%M:%S"))
                            - datetime.timedelta(days=x)
                        ).strftime("%d.%m.%Y %H:%M:%S")
                    )
                }
                for x in range(0, 7)
            ],
        ),
        (
            "2025-10-10 19:47:12",
            "M",
            [
                {
                    "Дата операции": (
                        (
                            (datetime.datetime.strptime("10.10.2025 00:00:00", "%d.%m.%Y %H:%M:%S"))
                            - datetime.timedelta(days=x)
                        ).strftime("%d.%m.%Y %H:%M:%S")
                    )
                }
                for x in range(0, 10)
            ],
        ),
        (
            "2025-10-10 19:47:12",
            "Y",
            [
                {
                    "Дата операции": (
                        (
                            (datetime.datetime.strptime("10.10.2025 00:00:00", "%d.%m.%Y %H:%M:%S"))
                            - datetime.timedelta(days=x)
                        ).strftime("%d.%m.%Y %H:%M:%S")
                    )
                }
                for x in range(0, 283)
            ],
        ),
        (
            "2025-10-10 19:47:12",
            "ALL",
            [
                {
                    "Дата операции": (
                        (
                            (datetime.datetime.strptime("10.10.2025 00:00:00", "%d.%m.%Y %H:%M:%S"))
                            - datetime.timedelta(days=x)
                        ).strftime("%d.%m.%Y %H:%M:%S")
                    )
                }
                for x in range(0, 283)
            ],
        ),
    ],
)
def test_data_range(date_data, date, ranges, result):
    assert data_range(date_data, date, ranges) == result


def test_expenses(full_operations):
    assert expenses(full_operations) == {
        "total_amount": 4801,
        "main": [
            {"category": "Красота", "amount": 316},
            {"category": "Кредит", "amount": 200},
            {"category": "Продукты", "amount": 100},
            {"category": "Подписка", "amount": 100},
            {"category": "Транспорт", "amount": 50},
            {"category": "Отдых", "amount": 20},
            {"category": "Остальное", "amount": 15},
        ],
        "transfers_and_cash": [{"category": "Переводы", "amount": 3000}, {"category": "Наличные", "amount": 1000}],
    }


def test_expenses_not_transfers_and_cash(operations):
    assert expenses(operations) == {
        "total_amount": 3511,
        "main": [
            {"category": "Красота", "amount": 3016},
            {"category": "Кредит", "amount": 200},
            {"category": "Продукты", "amount": 100},
            {"category": "Подписка", "amount": 100},
            {"category": "Транспорт", "amount": 50},
            {"category": "Отдых", "amount": 20},
            {"category": "Остальное", "amount": 25},
        ],
    }


def test_expenses_not_transactions(replenishment):
    assert expenses(replenishment) == {"total_amount": 0, "main": []}


def test_income(replenishment):
    assert income(replenishment) == {
        "total_amount": 450,
        "main": [
            {"category": "Пополнение", "amount": 300},
            {"category": "Проценты на остаток", "amount": 100},
            {"category": "Кэшбэк", "amount": 50},
        ],
    }


def test_not_income(full_operations):
    assert income(full_operations) == {"total_amount": 0}


@patch("builtins.open")
def test_get_custom_settings(mock_op, file_json):
    read_data = json.dumps(file_json)
    mock_open(mock=mock_op, read_data=read_data)
    assert get_custom_settings("./data/user_settings.json") == file_json
    mock_op.assert_called_once_with(os.path.abspath("./data/user_settings.json"), "r", encoding="utf-8")


def test_get_list_currency(file_json):
    assert get_list_currency(file_json) == ["USD", "EUR"]


def test_get_list_stocks(file_json):
    assert get_list_stocks(file_json) == ["AAPL", "MSFT"]


@patch("requests.get")
def test_get_currency_exchange(mock_get):
    load_dotenv(".env")
    api_key = os.getenv("EXC_AIP_KEY")
    url = f"https://api.apilayer.com/exchangerates_data/latest?symbols={"RUB"}&base={"USD"}"
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "success": True,
        "timestamp": 1519296206,
        "base": "USD",
        "date": "2021-03-17",
        "rates": {
            "RUB": 100.0,
        },
    }
    assert get_currency_exchange("USD") == {"currency": "USD", "rates": "100.0 ₽"}
    mock_get.assert_called_once_with(url, headers={"apikey": f"{api_key}"}, data={})


@patch("requests.get")
def test_get_currency_exchange_error(mock_get):
    load_dotenv(".env")
    api_key = os.getenv("EXC_AIP_KEY")
    url = f"https://api.apilayer.com/exchangerates_data/latest?symbols={"RUB"}&base={"EUR"}"
    mock_get.return_value.status_code = 404
    assert get_currency_exchange("EUR") == {"currency": "EUR", "rates": "---"}
    mock_get.assert_called_once_with(url, headers={"apikey": f"{api_key}"}, data={})


@patch("requests.get")
def test_get_exchange_rate(mock_exc):
    mock_exc.return_value.status_code = 200
    mock_exc.return_value.json.return_value = {
        "success": True,
        "timestamp": 1519296206,
        "base": "USD",
        "date": "2021-03-17",
        "rates": {
            "RUB": 100.0,
        },
    }
    assert get_exchange_rate(["USD"]) == [{"currency": "USD", "rates": "100.0 ₽"}]


@patch("requests.get")
def test_get_stock_price(mock_get):
    load_dotenv(".env")
    api_key = os.getenv("FMP_AIP_KEY")
    url = f"https://financialmodelingprep.com/stable/aftermarket-trade?symbol=AAPL&apikey={api_key}"
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [
        {"symbol": "AAPL", "price": 200.0, "tradeSize": None, "timestamp": 1762563587000}
    ]
    assert get_stock_price("AAPL") == {"stock": "AAPL", "price": "200.0 $"}
    mock_get.assert_called_once_with(url)


@patch("requests.get")
def test_get_stock_price_error(mock_get):
    load_dotenv(".env")
    api_key = os.getenv("FMP_AIP_KEY")
    url = f"https://financialmodelingprep.com/stable/aftermarket-trade?symbol=AAPL&apikey={api_key}"
    mock_get.return_value.status_code = 404
    assert get_stock_price("AAPL") == {"stock": "AAPL", "price": "---"}
    mock_get.assert_called_once_with(url)


@patch("requests.get")
def test_get_list_stock_prices(mock_fmp):
    mock_fmp.return_value.status_code = 200
    mock_fmp.return_value.json.return_value = [
        {"symbol": "AAPL", "price": 200.0, "tradeSize": None, "timestamp": 1762563587000}
    ]
    assert get_list_stock_prices(["AAPL"]) == [{"stock": "AAPL", "price": "200.0 $"}]


def test_get_json(file_json):
    assert get_json(file_json) == json.dumps(file_json, indent=4, ensure_ascii=False)


@pytest.mark.parametrize(
    "date, result",
    [
        (
            "2025-08",
            [
                {
                    "Дата операции": (
                        (
                            (datetime.datetime.strptime("31.08.2025 00:00:00", "%d.%m.%Y %H:%M:%S"))
                            - datetime.timedelta(days=x)
                        ).strftime("%d.%m.%Y %H:%M:%S")
                    )
                }
                for x in range(31)
            ],
        ),
        (
            "2025-02",
            [
                {
                    "Дата операции": (
                        (
                            (datetime.datetime.strptime("28.02.2025 00:00:00", "%d.%m.%Y %H:%M:%S"))
                            - datetime.timedelta(days=x)
                        ).strftime("%d.%m.%Y %H:%M:%S")
                    )
                }
                for x in range(28)
            ],
        ),
    ],
)
def test_get_billing_month(date_data, date, result):
    assert get_billing_month(date_data, date) == result


@pytest.mark.parametrize(
    "date, limit, result",
    [
        ("2018-01", 50, {"01.2018": {"amount_of_savings": 184.0}}),
        ("2018-01", 100, {"01.2018": {"amount_of_savings": 84.0}}),
        ("2018-01", 1000, {"01.2018": {"amount_of_savings": 984.0}}),
    ],
)
def test_get_rounding_difference(operations, date, limit, result):
    assert get_rounding_difference(operations, date, limit) == result


def test_get_rounding_difference_not_operation():
    assert get_rounding_difference([], "2018-01", 500) == {"01.2018": {"amount_of_savings": 0.0}}


def test_report():
    @report()
    def add(a, b):
        return {"equation": [f"{a} + {b}"], "result": [a + b]}

    assert add(2, 2) == {"equation": [f"{2} + {2}"], "result": [4]}


def test_report_error():
    @report()
    def add(a, b):
        return a + b

    assert add(2, 2) == {}


def test_report_error_func():
    @report()
    def sub(a, b):
        return a + b

    assert sub("2", 2) == {}


def test_get_data_for_last_three_months(operations_in_three_months):
    assert get_data_for_last_three_months(operations_in_three_months, "2018-03-01") == operations_in_three_months


def test_get_data_for_last_three_months_without_date(operations_in_three_months):
    assert get_data_for_last_three_months(operations_in_three_months) == []


def test_get_average_expenses_per_day(operations_in_three_months):
    assert get_average_expenses_per_day(operations_in_three_months) == {
        "day_week": [
            "Thursday 01.03.2018",
            "Sunday 18.02.2018",
            "Sunday 04.02.2018",
            "Saturday 03.02.2018",
            "Monday 08.01.2018",
            "Sunday 07.01.2018",
            "Monday 01.01.2018",
        ],
        "average_expenses": [3016.0, 75.0, 110.0, 100.0, 10.0, 5.0, 10.0],
    }


def test_get_average_expenses_per_day_error():
    assert get_average_expenses_per_day([]) == {
        "average_expenses": [],
        "day_week": [],
    }


def test_output_average_expenses_for_day(get_average_expenses):
    assert output_average_expenses_for_day(get_average_expenses) == [
        {"day_week": "Thursday 01.03.2018", "average_expenses": 3016.0},
        {"day_week": "Sunday 18.02.2018", "average_expenses": 75.0},
        {"day_week": "Sunday 04.02.2018", "average_expenses": 110.0},
        {"day_week": "Saturday 03.02.2018", "average_expenses": 100.0},
        {"day_week": "Monday 08.01.2018", "average_expenses": 10.0},
        {"day_week": "Sunday 07.01.2018", "average_expenses": 5.0},
        {"day_week": "Monday 01.01.2018", "average_expenses": 10.0},
    ]


def test_date_determination():
    assert date_determination() == datetime.datetime.today().strftime("%Y-%m-%d")


def test_reading_date():
    assert reading_date("11.09.2001") == "2001-09-11"
