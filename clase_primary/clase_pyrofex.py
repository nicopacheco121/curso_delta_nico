import pyRofex
import json
import time
import threading

# https://apihub.primary.com.ar/assets/docs/Primary-API.pdf
# https://github.com/matbarofex/pyRofex


class PyRofexClient:

    ### INICIO Y AUTENTICAION
    # def __init__(self, user, password, account, environment=pyRofex.Environment.REMARKET):
    #     """
    #     Inicializa el cliente de pyRofex con las credenciales provistas.
    #     :param user:
    #     :param password:
    #     :param account:
    #     :param environment:
    #     """
    #     self.user = user
    #     self.password = password
    #     self.account = account
    #     self.environment = environment
    #     self.authenticate()

    def __init__(self, config_file="keys.json", environment=pyRofex.Environment.REMARKET):
        """
        Inicializa el cliente de pyRofex con las credenciales provistas en un archivo JSON.
        :param config_file:
        :param environment:
        """
        self.config_file = config_file
        self.environment = environment
        self.load_credentials()
        self.authenticate()

        # Para la market data
        self.market_data_cache = {}  # Para almacenar los últimos datos recibidos
        self.running = False  # Control flag para el hilo
        self.execution_running = False  # Control flag para el hilo de ejecución

    def load_credentials(self):
        """
        Abrimos el arhivo json con las credenciales
        :return:
        """
        with open(self.config_file, 'r') as file:
            config = json.load(file)
            self.user = config['user']
            self.password = config['password']
            self.account = config['account']

    def authenticate(self):
        pyRofex.initialize(user=self.user,
                           password=self.password,
                           account=self.account,
                           environment=self.environment)
        print("Authenticated successfully.")

    ### INSTRUMENTS
    def get_and_save_instruments(self, filename="instruments_detailed.json"):
        # instruments = pyRofex.get_all_instruments()
        instruments = pyRofex.get_detailed_instruments()
        with open(filename, 'w') as file:
            json.dump(instruments, file, indent=4)
        print(f"Instruments saved to {filename}.")

    ### MARKET DATA
    def get_market_data(self, ticker):
        market_data = pyRofex.get_market_data(ticker=ticker,
                                              entries=[pyRofex.MarketDataEntry.BIDS,
                                                       pyRofex.MarketDataEntry.OFFERS,
                                                       pyRofex.MarketDataEntry.LAST])
        print(f"Market data for {ticker}: {market_data}")
        return market_data

    ### ORDENES
    def place_limit_order(self, ticker, side, size, price):
        order = pyRofex.send_order(ticker=ticker,
                                   side=side,
                                   size=size,
                                   price=price,
                                   order_type=pyRofex.OrderType.LIMIT)
        print(f"Limit order placed: {order}")
        return order

    def place_market_order(self, ticker, side, size):
        order = pyRofex.send_order(ticker=ticker,
                                   side=side,
                                   size=size,
                                   order_type=pyRofex.OrderType.MARKET)
        print(f"Market order placed: {order}")
        return order

    def query_order(self, client_order_id, proprietary='ISV_PBCP'):
        order_status = pyRofex.get_order_status(client_order_id=client_order_id, proprietary=proprietary)
        print(f"Order status: {order_status}")
        return order_status

    def cancel_order(self, client_order_id, proprietary='ISV_PBCP'):
        cancel_response = pyRofex.cancel_order(client_order_id=client_order_id, proprietary=proprietary)
        print(f"Cancel order response: {cancel_response}")
        return cancel_response

    # POSITIONS
    def check_positions(self):
        positions = pyRofex.get_account_position()
        print(f"Current positions: {positions}")
        return positions

    ### MARKET DATA WEB SOCKETS
    def market_data_handler(self, message):
        """Callback para manejar los mensajes de market data"""
        print(f"Message received: {message}")
        if message['type'] == 'Md':
            self.market_data_cache[message['instrumentId']['symbol']] = message

    def error_handler(self, message):
        """Callback para manejar errores"""
        print(f"Error: {message}")

    def order_book_printer(self, symbol):
        """Función que se ejecutará en el hilo para imprimir el order book"""
        while self.running:

            # print(self.market_data_cache)

            if symbol in self.market_data_cache:
                data = self.market_data_cache[symbol]
                print("\n=== Order Book ===")
                print(f"Instrumento: {symbol}")
                print("Bids:")
                if 'BI' in data['marketData']:
                    for bid in data['marketData']['BI']:
                        print(f"Precio: {bid['price']}, Cantidad: {bid['size']}")
                print("Offers:")
                if 'OF' in data['marketData']:
                    for offer in data['marketData']['OF']:
                        print(f"Precio: {offer['price']}, Cantidad: {offer['size']}")
                print("================\n")
            time.sleep(10)

    def subscribe_market_data(self, symbol):
        """Suscribe a market data para un símbolo y comienza a imprimir el order book"""
        try:
            # Inicializar websocket si no está ya inicializado
            if not hasattr(self, '_ws_initialized'):
                pyRofex.init_websocket_connection(
                    market_data_handler=self.market_data_handler,
                    order_report_handler=self.order_report_handler,
                    error_handler=self.error_handler
                )
                self._ws_initialized = True

            # Suscribirse al market data
            entries = [
                pyRofex.MarketDataEntry.BIDS,
                pyRofex.MarketDataEntry.OFFERS,
                pyRofex.MarketDataEntry.LAST
            ]

            pyRofex.market_data_subscription(
                tickers=[symbol],
                entries=entries
            )

            print(f"Suscrito exitosamente a {symbol}")

            # Iniciar el hilo para imprimir el order book
            self.running = True
            printer_thread = threading.Thread(
                target=self.order_book_printer,
                args=(symbol,)
            )
            printer_thread.daemon = True
            printer_thread.start()

        except Exception as e:
            print(f"Error al suscribirse: {e}")
            self.running = False

    def stop_market_data(self):
        """Detiene la suscripción y el hilo de impresión"""
        self.running = False
        self.execution_running = False
        if hasattr(self, '_ws_initialized'):
            pyRofex.close_websocket_connection()
            delattr(self, '_ws_initialized')
        print("Suscripciones detenidas")

    # EXECUTION REPORTS
    def order_report_handler(self, message):
        """Callback para manejar los mensajes de execution reports"""
        if message['type'] == 'OR':
            print("\n=== Execution Report ===")
            print(f"Cliente Order ID: {message.get('clientOrderId')}")
            print(f"Orden Status: {message.get('orderReport', {}).get('status')}")
            print(f"Instrumento: {message.get('orderReport', {}).get('instrumentId', {}).get('symbol')}")
            print(f"Precio: {message.get('orderReport', {}).get('price')}")
            print(f"Cantidad: {message.get('orderReport', {}).get('quantity')}")
            print(f"Lado: {message.get('orderReport', {}).get('side')}")
            print(f"Tipo de Orden: {message.get('orderReport', {}).get('orderType')}")
            print(f"Timestamp: {message.get('timestamp')}")
            print("=====================\n")

    def subscribe_order_reports(self):
        """Suscribe a los execution reports"""
        try:
            # Inicializar websocket si no está ya inicializado
            if not hasattr(self, '_ws_initialized'):
                pyRofex.init_websocket_connection(
                    market_data_handler=self.market_data_handler,
                    order_report_handler=self.order_report_handler,
                    error_handler=self.error_handler
                )
                self._ws_initialized = True

            # Suscribirse a los order reports
            pyRofex.order_report_subscription()

            print("Suscrito exitosamente a Order Reports")
            self.execution_running = True

        except Exception as e:
            print(f"Error al suscribirse a order reports: {e}")
            self.execution_running = False

    def start_all_subscriptions(self, symbol):
        """Método de conveniencia para iniciar todas las suscripciones"""
        self.subscribe_market_data(symbol)
        self.subscribe_order_reports()




if __name__ == '__main__':
    client = PyRofexClient()
    # client.get_and_save_instruments()
    symbol = 'DLR/OCT24'
    # client.get_market_data(symbol)

    #
    # order = input("Enter order id: ")
    # client.query_order(order)
    #
    # client.cancel_order(order)
    #
    # client.place_market_order(symbol, pyRofex.Side.BUY, 1)
    # order = input("Enter order id: ")
    # client.query_order(order)


    client.check_positions()

    # Suscribirse a un instrumento (por ejemplo "DODic23")
    # client.subscribe_market_data("DLR/OCT24")
    # client.subscribe_order_reports()
    # client.start_all_subscriptions("DLR/OCT24")

    # time.sleep(10)
    #
    # client.place_limit_order(symbol, pyRofex.Side.SELL, 1, 1001)

    # # open instruments
    # with open("instruments.json", 'r') as file:
    #     instruments = json.load(file)
    #     print(instruments)
    #
    # for i in instruments['instruments']:
    #     symbol = i['instrumentId']['symbol']
    #     if 'AL30' in symbol:
    #         print(symbol)


    # import pickle
    # # open instruments
    # with open('instruments_test.pickle', 'rb') as handle:
    #     instruments = pickle.load(handle)
    #
    # for i in instruments['instruments']:
    #     symbol = i['instrumentId']['symbol']
    #     if 'PESOS' in symbol:
    #         print(symbol)

    # # Cancelar todas las ordenes
    # cancelled_orders = []
    # orders = pyRofex.get_all_orders_status()
    # for order in orders.get('orders', []):
    #     status = order.get('status', None)
    #     if status in ['NEW', 'PENDING_NEW', 'PARTIALLY_FILLED']:
    #         cancel_response = client.cancel_order(
    #             client_order_id=order['clOrdId'],
    #             proprietary=order.get('proprietary', 'ISV_PBCP')
    #         )
    #         cancelled_orders.append({
    #             'clientOrderId': order['clOrdId'],
    #             'symbol': order['instrumentId']['symbol'],
    #             'response': cancel_response
    #         })
    #
    # print(f"Canceladas {len(cancelled_orders)} órdenes:")
    # for order in cancelled_orders:
    #     print(f"Order ID: {order['clientOrderId']}, Símbolo: {order['symbol']}")



            # consulto la orden de cancelacion


