from src.utils import for_df_to_list, get_billing_month, get_json, get_rounding_difference, reading_from_xlsx


def investment_bank(month: str, limit: int, transactions: list = None) -> dict:
    """Функция принимает на вход три аргумента: месяц, для которого рассчитывается отложенная сумма
    (строка в формате 'YYYY-MM'). Список словарей, содержащий информацию о транзакциях,
    в которых содержатся следующие поля:
    'Дата операции' — дата, когда произошла транзакция (строка в формате 'YYYY-MM-DD');
    'Сумма операции' — сумма транзакции в оригинальной валюте (число).
    Третий аргумент это предел, до которого нужно округлять суммы операций (целое число 10, 50 или 100 ₽).
    Функция возвращает сумму, которую удалось бы отложить в 'Инвесткопилку'
    """
    if transactions is None:
        transactions = for_df_to_list(reading_from_xlsx())
    monthly_data = get_billing_month(transactions, month)
    amount_of_savings = get_rounding_difference(monthly_data, month, limit)
    json_response = get_json(amount_of_savings)

    return json_response
