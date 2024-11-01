from clase_primary.clase_pyrofex import PyRofexClient
import fx_sqlite
from fx_sqlite import main_sqlite, create_connection
import functions

from time import sleep

def run_bot():

    # descarga_instruments = False
    descarga_instruments = True

    client = PyRofexClient()  # Create a PyRofexClient

    if not descarga_instruments:
        client.get_and_save_instruments()  # Get instruments and save them in the DDBB.
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
        print("Hay algo pendiente")

        # get instruments de sql
        instruments = fx_sqlite.query_instruments(slq_conn)
        print(instruments)

        # obtengo el maturity en base a instruments_detailed.json
        maturity = functions.get_maturity(instruments, 'instruments_detailed.json')


        for p in pendiente:
            print(f"Procesando tarea pendiente: {p['id']}")



if __name__ == '__main__':
    run_bot()
