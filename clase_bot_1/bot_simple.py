from clase_primary.clase_pyrofex import PyRofexClient
import fx_sqlite
from fx_sqlite import main_sqlite, create_connection
import functions
import pyRofex

from time import sleep


def run_bot():

    # descarga_instruments = False
    descarga_instruments = True

    client = PyRofexClient()  # Create a PyRofexClient

    if not descarga_instruments:
        client.get_instruments_and_save()  # Get instruments and save them in the DDBB.
        descarga_instruments = True

    # SQLite
    main_sqlite()  # Creamos la tabla si no esta creada
    slq_conn = create_connection()

    # Consultamos a la DDBB si hay algo en la tabla todo
    todo = fx_sqlite.query_todo(slq_conn)
    print("To-do list:", todo)
    pendiente = [x for x in todo if x["status"] == 'pendiente']

    # Vemos si hay algo pendiente
    if pendiente:
        # print("Hay algo pendiente")

        instruments = fx_sqlite.query_instruments(slq_conn)  # get instruments de sql
        print(instruments)

        # obtengo la data de los symbols
        data_symbols = functions.get_data_instruments(instruments, 'instruments_detailed.json')
        data_symbols = {'DLR/ENE25': {'tick_price': 0.5, 'tick_size': 1.0, 'vencimiento': '2025-01-31'}, 'DLR/NOV24': {'tick_price': 0.5, 'tick_size': 1.0, 'vencimiento': '2024-11-29'}, 'DLR/DIC24': {'tick_price': 0.5, 'tick_size': 1.0, 'vencimiento': '2024-12-30'}}
        # print(data_symbols)

        # Obtengo puntas de precios
        ddbb_precios = {}
        # for i in data_symbols:
        #     symbol = i
        #     md = client.get_market_data(symbol)
        #     ddbb_precios[symbol] = md.get('marketData')

        ddbb_precios = {'DLR/ENE25': {'OF': [{'price': 1081.0, 'size': 90}], 'LA': None, 'BI': [{'price': 1080.5, 'size': 350}]}, 'DLR/NOV24': {'OF': [{'price': 1018.0, 'size': 5053}], 'LA': None, 'BI': [{'price': 1017.0, 'size': 7534}]}, 'DLR/DIC24': {'OF': [{'price': 1048.0, 'size': 295}], 'LA': None, 'BI': [{'price': 1047.5, 'size': 2059}]}}
        # print(ddbb_precios)

        # Calculo las ordenes a enviar
        for p in pendiente:
            monto_operar = p['monto']
            id_pendiente = p['id']

            ordenes = functions.calc_montos(ddbb_precios, monto_operar, data_symbols)
            # print(ordenes)

            for order_enviar in ordenes:
                print(f"Enviando orden: {order_enviar}")

                symbol = order_enviar
                price = ordenes[order_enviar]['price']
                size = ordenes[order_enviar]['size']

                if size < 1:  # si el size es menor a 1, no hago nada
                    continue

                orden = client.place_limit_order(ticker=symbol, price=price, size=size, side=pyRofex.Side.BUY)
                # print(orden)

                # Guardo en la DDBB
                insertar_orden = fx_sqlite.insertar_orden_inicial(slq_conn, client_id=orden['order']['clientId'], id_todo=id_pendiente, symbol=symbol)
                if not insertar_orden:
                    print("Error al actualizar la DDBB")

                sleep(1)

                # Consulto la orden
                client_order_id = orden['order']['clientId']
                orden = client.consultar_orden(client_order_id=client_order_id)
                print(orden)

                actualizar_ddbb = fx_sqlite.actualizar_orden(slq_conn, id_operacion=id_pendiente, orden_response=orden)
                if not actualizar_ddbb:
                    print("Error al actualizar la DDBB")

            sleep(1)

            while True:  # Consulto las ordenes hasta que esten todas finalizadas
                ordenes = fx_sqlite.consultar_ordenes_por_todo(slq_conn, id_todo=id_pendiente)
                print(ordenes)

                # verifico si todas las ordenes estan finalizadas
                nuevo_status = fx_sqlite.actualizar_status_todo(slq_conn, id_pendiente)
                if nuevo_status in ['FILLED', 'REVISAR']:
                    print(f"Todo {id_pendiente} finalizado con status: {nuevo_status}")
                    break

                # Si no estan finalizadas, consulto las ordenes y actualizo la DDBB
                for orden_sql in ordenes:
                    status = orden_sql['status']
                    if status in ['FILLED', 'REJECTED', 'CANCELED']:
                        continue
                    else:
                        client_id = orden_sql['clientId']
                        orden = client.consultar_orden(client_order_id=client_id)
                        print(orden)
                        actualizar_ddbb = fx_sqlite.actualizar_orden(slq_conn, id_operacion=orden_sql['id_operacion'], orden_response=orden)
                        if not actualizar_ddbb:
                            print("Error al actualizar la DDBB")

                print('Aun quedan ordenes, espero 10 segundos')
                sleep(10)

            print('Finalizado el pendiente con id:', id_pendiente)

    print('Todos los pendientes finalizados, duermo 10 minutos')
    sleep(600)


if __name__ == '__main__':
    run_bot()
