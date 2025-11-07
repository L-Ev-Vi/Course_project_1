import pandas as pd
import pytest
from unittest.mock import patch
import datetime

from src.utils import for_xlsx_to_list, data_range, expenses, income, exchange_rate, share_price
from tests.conftest import date_data


@patch('pandas.read_excel')
def test_for_xlsx_to_list(mock_df, file_xlsx):
    mock_df.return_value = pd.DataFrame(file_xlsx)
    assert for_xlsx_to_list() == [
        {
            'Дата операции': '01.01.2018 20:27:51',
            'Дата платежа': '04.01.2018',
            'Номер карты': '*7197',
            'Статус': 'OK',
            'Сумма операции': -316.0,
            'Валюта операции': 'RUB',
            'Сумма платежа': -316.0,
            'Валюта платежа': 'RUB',
            'Кэшбэк': 5.0,
            'Категория': 'Красота',
            'MCC': 5977,
            'Описание': 'OOO Balid',
            'Бонусы (включая кэшбэк)': 6.0,
            'Округление на инвесткопилку': 0.0,
            'Сумма операции с округлением': 316.0
        },
        {
            'Дата операции': '01.01.2018 12:49:53',
            'Дата платежа': '01.01.2018',
            'Номер карты': 0,
            'Статус': 'OK',
            'Сумма операции': -3000.0,
            'Валюта операции': 'RUB',
            'Сумма платежа': -3000.0,
            'Валюта платежа': 'RUB',
            'Кэшбэк': 0.0,
            'Категория': 'Переводы',
            'MCC': 0,
            'Описание': 'Линзомат ТЦ Юность',
            'Бонусы (включая кэшбэк)': 0.0,
            'Округление на инвесткопилку': 0.0,
            'Сумма операции с округлением': 3000.0
        }
    ]


def test_for_xlsx_to_list_error():
    assert for_xlsx_to_list('data/transactions.xlsx') == []


@pytest.mark.parametrize(
    'date, ranges, result', [
        ('2025-10-10 19:47:12', 'W', [{'Дата операции': ((
                (datetime.datetime.strptime('10.10.2025 00:00:00', '%d.%m.%Y %H:%M:%S')) - datetime.timedelta(
            days=x)).strftime('%d.%m.%Y %H:%M:%S'))} for x in range(0, 5)]),
        ('2025-10-12 19:47:12', 'W', [{'Дата операции': ((
                (datetime.datetime.strptime('12.10.2025 00:00:00', '%d.%m.%Y %H:%M:%S')) - datetime.timedelta(
            days=x)).strftime('%d.%m.%Y %H:%M:%S'))} for x in range(0, 7)]),
        ('2025-10-10 19:47:12', 'M', [{'Дата операции': ((
                (datetime.datetime.strptime('10.10.2025 00:00:00', '%d.%m.%Y %H:%M:%S')) - datetime.timedelta(
            days=x)).strftime('%d.%m.%Y %H:%M:%S'))} for x in range(0, 10)]),
        ('2025-10-10 19:47:12', 'Y', [{'Дата операции': ((
                (datetime.datetime.strptime('10.10.2025 00:00:00', '%d.%m.%Y %H:%M:%S')) - datetime.timedelta(
            days=x)).strftime('%d.%m.%Y %H:%M:%S'))} for x in range(0, 283)]),
        ('2025-10-10 19:47:12', 'ALL', [{'Дата операции': ((
                (datetime.datetime.strptime('10.10.2025 00:00:00', '%d.%m.%Y %H:%M:%S')) - datetime.timedelta(
            days=x)).strftime('%d.%m.%Y %H:%M:%S'))} for x in range(0, 283)])
    ]
)
def test_data_range(date_data, date, ranges, result):
    assert data_range(date_data, date, ranges) == result


def test_expenses(full_operations):
    assert expenses(full_operations) == {
        "total_amount": 4801,
        "main": [
            {
                "category": "Красота",
                "amount": 316
            },
            {
                "category": "Кредит",
                "amount": 200
            },
            {
                "category": "Продукты",
                "amount": 100
            },
            {
                "category": "Подписка",
                "amount": 100
            },
            {
                "category": "Транспорт",
                "amount": 50
            },
            {
                "category": "Отдых",
                "amount": 20
            },
            {
                "category": "Обучение",
                "amount": 10
            },
            {
                "category": "Остальное",
                "amount": 5
            }

        ],
        "transfers_and_cash": [
            {
                "category": "Переводы",
                "amount": 3000
            },
            {
                "category": "Наличные",
                "amount": 1000
            }
        ]
    }


def test_expenses_not_transfers_and_cash(operations):
    assert expenses(operations) == {
        "total_amount": 801,
        "main": [
            {
                "category": "Красота",
                "amount": 316
            },
            {
                "category": "Кредит",
                "amount": 200
            },
            {
                "category": "Продукты",
                "amount": 100
            },
            {
                "category": "Подписка",
                "amount": 100
            },
            {
                "category": "Транспорт",
                "amount": 50
            },
            {
                "category": "Отдых",
                "amount": 20
            },
            {
                "category": "Обучение",
                "amount": 10
            },
            {
                "category": "Остальное",
                "amount": 5
            }

        ]
    }


def test_expenses_not_transactions(replenishment):
    assert expenses(replenishment) == {
        "total_amount": 0,
        "main": []
    }


def test_income(replenishment):
    assert income(replenishment) == {
        "total_amount": 450,
        "main": [
            {
                "category": "Пополнение",
                "amount": 300
            },
            {
                "category": "Проценты на остаток",
                "amount": 100
            },
            {
                "category": "Кэшбэк",
                "amount": 50
            }
        ]
    }


def test_not_income(full_operations):
    assert income(full_operations) == {"total_amount": 0}


@patch('request.get')
def test_exchange_rate(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "base": "RUB",
        "date": "2021-03-17",
        "rates": {
            "USD": 100.0,
            "EUR": 100.0,
            "CNY": 100.0
        },
        "success": True,
        "timestamp": 1519296206
    }
    assert exchange_rate() == [
        {
            "currency": "USD",
            "rate": 100
        },
        {
            "currency": "EUR",
            "rate": 100
        },
        {
            "currency": "CNY",
            "rate": 100
        }
    ]


@patch('request.get')
def test_share_price(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [
        {
            "symbol": "S&P500",
            "name": "S&P500",
            "price": 100.0,
            "changePercentage": -0.4337,
            "change": -1.17,
            "volume": 20587870,
            "dayLow": 267.27,
            "dayHigh": 272.29,
            "yearHigh": 277.32,
            "yearLow": 169.21,
            "marketCap": 3968941040000,
            "priceAvg50": 251.534,
            "priceAvg200": 224.17345,
            "exchange": "NASDAQ",
            "open": 269.795,
            "previousClose": 269.77,
            "timestamp": 1762535738
        }
    ]
    assert share_price() == [
        {
            "stock": "S&P500",
            "price": 100.0
        }]
