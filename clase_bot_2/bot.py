from database import Database
from clase_primary.clase_pyrofex import PyRofexClient
import pyRofex
import time
import json
import random
# bot.py
class TradingBot(PyRofexClient):
    def __init__(self, config_file="keys.json", descargar_instruments=False):
        """Bot de trading que hereda funcionalidades de PyRofexClient"""
        # Llamamos al constructor de la clase padre
        super().__init__(config_file)

        # Inicializamos atributos propios del bot
        self.db = Database()
        self.active_orders = {}
        self.is_running = False
        self.file_instruments = "instruments_detailed.json"
        self.symbols = []
        self.data_symbols = {}
        self.ddbb_precios = {}
        self.multiplicador = 1000

        self.orders_id = []

        # Instruments
        if descargar_instruments:
            self.get_instruments_and_save()

    def initialize(self):
        """Inicializa el bot"""
        self.db.connect()
        self.db.create_tables()
        print("Bot initialized successfully")

    def process_pending_orders(self):
        """Procesa órdenes pendientes"""
        pending = self.db.query_todo()
        for p in pending:
            if p["status"] == "pendiente":

                # self.symbols = self.db.query_instruments()  # get instruments de sql

                # self.get_data_instruments()  # obtengo la data de los symbols
                # self.build_ddbb_precios()  # Obtengo puntas de precios

                self.data_symbols = {'DLR/ENE25': {'tick_price': 0.5, 'tick_size': 1.0, 'vencimiento': '2025-01-31'},
                                'DLR/NOV24': {'tick_price': 0.5, 'tick_size': 1.0, 'vencimiento': '2024-11-29'},
                                'DLR/DIC24': {'tick_price': 0.5, 'tick_size': 1.0, 'vencimiento': '2024-12-30'}}
                self.ddbb_precios = {'DLR/ENE25': {'OF': [{'price': 1081.0, 'size': 90}], 'LA': None,
                                              'BI': [{'price': 1080.5, 'size': 350}]},
                                'DLR/NOV24': {'OF': [{'price': 1018.0, 'size': 5053}], 'LA': None,
                                              'BI': [{'price': 1017.0, 'size': 7534}]},
                                'DLR/DIC24': {'OF': [{'price': 1048.0, 'size': 295}], 'LA': None,
                                              'BI': [{'price': 1047.5, 'size': 2059}]}}

                orders = self.calc_montos(p['monto'])  # Calculo las ordenes a enviar

                self.execute_order_strategy(orders, p['id'])

                self.finish_pendiente(p['id'])

                print('Finalizado el pendiente con id:', p['id'])

    def execute_order_strategy(self, ordenes, id_todo):
        """Ejecuta la estrategia de trading para un pendiente"""
        try:

            for order_enviar in ordenes:

                symbol = order_enviar
                price = ordenes[order_enviar]['price']
                size = ordenes[order_enviar]['size']

                if size < 1:  # si el size es menor a 1, no hago nada
                    continue

                # orden = self.place_limit_order(ticker=symbol, price=price, size=size, side=pyRofex.Side.BUY)
                # print(orden)

                client_id = str(random.randint(100000, 999999))

                # Guardo en la DDBB
                insertar_orden = self.db.insert_order(
                    # client_id=orden['order']['clientId'],
                    client_id=client_id,
                    id_todo=id_todo, symbol=symbol)
                if not insertar_orden:
                    print("Error al actualizar la DDBB")

        except Exception as e:
            print(f"Error executing order: {e}")

    def finish_pendiente(self, id_todo):
        """Finaliza un pendiente"""
        while True:  # Consulto las ordenes hasta que esten todas finalizadas
            ordenes = self.db.get_orders_by_todo(id_todo)
            print(ordenes)

            # verifico si todas las ordenes estan finalizadas
            nuevo_status = self.db.update_todo_status(id_todo)
            if nuevo_status in ['FILLED', 'REVISAR']:
                print(f"Todo {id_todo} finalizado con status: {nuevo_status}")
                break

            # Si no estan finalizadas, consulto las ordenes y actualizo la DDBB
            for orden_sql in ordenes:
                status = orden_sql['status']
                if status in ['FILLED', 'REJECTED', 'CANCELED']:
                    continue
                else:
                    client_id = orden_sql['clientId']
                    # orden = self.consultar_orden(client_order_id=client_id)
                    # print(orden)

                    # Orden modelo para la base de datos
                    orden = {
                        "status": "OK",
                        "order": {
                            "orderId": "1130835",
                            # "clOrdId": "user1145712381052053",
                            "clOrdId": client_id,
                            "proprietary":"PBCP",
                            "execId":"160229133429-fix1-493",
                            "accountId":{ "id":"10" },
                            "instrumentId":{ "marketId":"ROFX", "symbol":"DLR/DIC23" },
                            "price":183,
                            "orderQty":10,
                            "ordType":"LIMIT",
                            "side":"BUY",
                            "timeInForce":"DAY",
                            "transactTime":"20160304-17:37:35",
                            "avgPx":0,
                            "lastPx":0,
                            "lastQty":0,
                            "cumQty":0,
                            "leavesQty":10,
                            "status":"FILLED",
                            "text":"Aceptada" } }

                    actualizar_ddbb = self.db.update_order(id_operacion=orden_sql['id_operacion'], orden_response=orden)
                    if not actualizar_ddbb:
                        print("Error al actualizar la DDBB")

            print('Aun quedan ordenes, espero 10 segundos')
            time.sleep(10)

    def run(self):
        """Ejecuta el bot en un loop continuo"""
        self.is_running = True
        self.initialize()

        while self.is_running:
            try:
                self.process_pending_orders()
                print("Terminado el proceso de pendientes, duermo 10 minutos")
                time.sleep(600)  # 10 minutos
            except Exception as e:
                print(f"Error in bot execution: {e}")
                time.sleep(60)  # 1 minuto en caso de error

    def stop(self):
        """Detiene el bot"""
        self.is_running = False
        print("Bot stopped")

    def get_data_instruments(self):
        """
        Obtiene la data necesaria de los instrumentos en base a instruments_detailed.json
        Data:
        Matuity
        minPriceIncrement
        tickSize
        orderTypes
        instrumentPricePrecision
        """

        # abro el json
        with open(self.file_instruments, 'r', encoding='utf-8') as file:
            data = json.load(file)

        instruments = data['instruments']
        for instrument in instruments:
            symbol = instrument['securityDescription']

            for s in self.symbols:
                if s == symbol:
                    self.data_symbols[symbol] = {}
                    self.data_symbols[symbol]['tick_price'] = instrument['minPriceIncrement']
                    self.data_symbols[symbol]['tick_size'] = instrument['tickSize']

                    maturityDate = instrument['maturityDate']

                    # example "20250131", this to datetime
                    year = maturityDate[0:4]
                    month = maturityDate[4:6]
                    day = maturityDate[6:8]
                    self.data_symbols[symbol]['vencimiento'] = f"{year}-{month}-{day}"

                    break

    def build_ddbb_precios(self):
        """Construye el diccionario de precios de la base de datos"""
        for symbol in self.symbols:
            md = self.get_market_data(symbol)
            self.ddbb_precios[symbol] = md.get('marketData')

    def calc_montos(self, monto_operar):
        """
        En base al monto a operar, calcula cuanto size ira para cada instrumento.

        Toma solo el OF, si no tiene OF, toma el BI, si no tiene nada, lo descarta

        El monto sera un ponderado en base al size que tiene cada punta

        :param ddbb_precios:
        :param monto_operar:
        :return:
        """

        ordenes = {}
        monto_sobrante = 0

        size_total = 0
        for i in self.ddbb_precios:
            if self.ddbb_precios[i]['OF']:
                size = self.ddbb_precios[i]['OF'][0]['size']
                size_total += size

            elif self.ddbb_precios[i]['BI']:
                size = self.ddbb_precios[i]['BI'][0]['size']
                size_total += size

        for i in self.ddbb_precios:
            tick_size = float(self.data_symbols[i]['tick_size'])

            if self.ddbb_precios[i]['OF'] or self.ddbb_precios[i]['BI']:
                size_i = self.ddbb_precios[i]['OF'][0]['size'] if self.ddbb_precios[i]['OF'] else self.ddbb_precios[i]['BI'][0]['size']
                price_i = self.ddbb_precios[i]['OF'][0]['price'] if self.ddbb_precios[i]['OF'] else self.ddbb_precios[i]['BI'][0][
                    'price']

                monto_ars = (size_i / size_total) * (monto_operar) + monto_sobrante

                contratos = monto_ars / (price_i * self.multiplicador)
                # round to the lower tick size
                contratos_adj = int(contratos // tick_size) * tick_size

                pxq = price_i * contratos_adj * self.multiplicador
                monto_sobrante = monto_ars - pxq

                ordenes[i] = {'monto': pxq, 'size': contratos_adj, 'price': price_i}

        print('Monto sobrante:', round(monto_sobrante))

        return ordenes


# main.py
if __name__ == "__main__":
    # Ejemplo de uso del bot
    bot = TradingBot(config_file="keys.json")

    try:
        # Iniciamos el bot
        bot.run()
    except KeyboardInterrupt:
        # Manejo de interrupción por teclado
        print("\nDetecting keyboard interrupt...")
        bot.stop()
    except Exception as e:
        # Manejo de otros errores
        print(f"Unexpected error: {e}")
        bot.stop()
