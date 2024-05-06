from random import randint

import time
import requests
import hashlib
import hmac

SECRET_KEY = 'flk3409refn54t54t*FNJRET'
domain_name = '34.173.108.210'
merchantAccount = 'test_merch_n1'
WAYFORPAY_API = "https://api.wayforpay.com/api"


# Функция для создания подписи HMAC_MD5
def generate_hmac(data, secret_key):
    message = ';'.join(data).encode('utf-8')
    secret_key = secret_key.encode('utf-8')
    return hmac.new(secret_key, message, hashlib.md5).hexdigest()


# Функция для формирования параметров запроса
def create_request_params(price, email, ticket_count, order_id):
    orderReference = f"DH{randint(1000000000, 9999999999)}"
    orderDate = int(time.time())

    params = {
        "transactionType": "CREATE_INVOICE",
        "merchantAccount": merchantAccount,
        "merchantDomainName": domain_name,
        "apiVersion": 1,
        "language": "en",
        "serviceUrl": "http://34.173.108.210/api/v1/wayforpay_callback/",
        "orderReference": orderReference,
        "orderDate": orderDate,
        "amount": price,
        "currency": "UAH",
        "orderTimeout": 86400,
        "productName": ["Air Ticket"],
        "productPrice": [21.1],
        "productCount": [ticket_count],
        "paymentSystems": "card;privat24",
        "clientEmail": email,
        "order_id": order_id,
    }

    # Формирование подписи HMAC_MD5
    data_to_sign = [
        params["merchantAccount"],
        params["merchantDomainName"],
        params["orderReference"],
        str(params["orderDate"]),
        str(params["amount"]),
        params["currency"]
    ]
    for product in params["productName"]:
        data_to_sign.append(product)
    for count in params["productCount"]:
        data_to_sign.append(str(count))
    for price in params["productPrice"]:
        data_to_sign.append(str(price))

    params["merchantSignature"] = generate_hmac(data_to_sign, SECRET_KEY)

    return params


# Функция для отправки запроса
def send_request(params):
    response = requests.post(WAYFORPAY_API, json=params)
    return response


# Функция для обработки ответа
def handle_response(response):
    if response.status_code == 200:
        response_data = response.json()
        # Обработка данных ответа согласно вашим потребностям
        return response_data
    else:
        return {"error": f"Ошибка при выполнении запроса: {response.status_code}"}


def generate_response_signature(orderReference, status, time, secret_key):
    data = f"{orderReference};{status};{time}".encode('utf-8')
    signature = hashlib.md5(data + secret_key.encode('utf-8')).hexdigest()
    return signature
