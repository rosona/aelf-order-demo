from aelf import AElf
from flask import Flask, request, render_template
from google.protobuf.timestamp_pb2 import Timestamp

from types2_pb2 import OrderInput, FetchOrdersInput, Orders

app = Flask(__name__)

_client = AElf("http://127.0.0.1:1235", '027862701344eaa2a947c8caeddbcd338ded3f6d9b29c795630f24f2d5c5c06c')

_order_id = 100

_ACCOUNT_ID = 200


def _create_order(order_input):
    """Create order
    """
    order_contract_address = _client.get_system_contract_address('AElf.ContractNames.OrderContract')
    create_order_transaction = _client.build_transaction(order_contract_address, 'CreateOrder',
                                                         order_input.SerializeToString())
    result = _client.send_transaction(create_order_transaction.SerializePartialToString().hex())
    print('create order transaction', result)
    return result['TransactionId']


def _fetch_order(account_id):
    """Fetch order
    """
    fetch_orders_input = FetchOrdersInput()
    fetch_orders_input.account_id = int(account_id)
    fetch_orders_input.start_order_id = 100
    fetch_orders_input.limit = 20

    order_contract_address = _client.get_system_contract_address('AElf.ContractNames.OrderContract')
    fetch_orders_transaction = _client.build_transaction(order_contract_address, 'FetchOrders',
                                                         fetch_orders_input.SerializeToString())
    raw_orders = _client.execute_transaction(fetch_orders_transaction)
    orders = Orders()
    orders.ParseFromString(bytes.fromhex(raw_orders.decode()))
    for order in orders.value:
        print(order)
    return orders


@app.route('/order/create', methods=['POST', 'GET'])
def create_order():
    """Create order
    """
    global _order_id
    transaction_id = None
    if request.method == 'POST':
        order_input = OrderInput()
        for item in request.form:
            if item == 'memo':
                order_input.memo = request.form[item]
                continue
            item_details = request.form[item].split(';')
            order_input.items[item_details[0]] = int(item_details[1])
        if order_input.items != {}:
            create_time = Timestamp()
            create_time.GetCurrentTime()
            # order_input.create_time.CopyFrom(create_time)
            order_input.account_id = _ACCOUNT_ID
            _order_id += 1
            order_input.id = _order_id
            transaction_id = _create_order(order_input)
    return render_template('create_order.html', account_id=_ACCOUNT_ID, transaction_id=transaction_id)


@app.route('/orders/<account_id>', methods=['GET'])
def fetch_orders(account_id):
    orders = _fetch_order(account_id)
    orders_for_display = []
    for order in orders.value:
        items = []
        for key in order.items:
            items.append({'name': key, 'price': order.items[key]})
        orders_for_display.append({
            'order_id': order.id,
            'account_id': order.account_id,
            'item': items,
            'memo': order.memo
        })
    return render_template('orders.html', orders=orders_for_display)


def main():
    """Main process
    """
    app.config.from_pyfile('config.py')
    app.run()


if __name__ == '__main__':
    main()
