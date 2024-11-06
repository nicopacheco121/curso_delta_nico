import sqlite3
from sqlite3 import Error


def create_connection():
    try:
        conn = sqlite3.connect('cauciones.db')
        return conn
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None


def create_tables(conn):
    try:
        cursor = conn.cursor()

        # Tabla to-do
        cursor.execute('''
          CREATE TABLE IF NOT EXISTS todo (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              monto REAL NOT NULL,
              status TEXT DEFAULT 'pendiente'
          )
      ''')

        # Tabla operaciones
        cursor.execute('''
          CREATE TABLE IF NOT EXISTS operaciones (
              id_operacion INTEGER PRIMARY KEY AUTOINCREMENT,
              id_todo INTEGER,
              clientId TEXT NOT NULL,
              order_id TEXT,
              symbol TEXT NOT NULL,
              price REAL,
              size INTEGER,
              side TEXT,
              pxq REAL,
              avg_price REAL,
              filled INTEGER,
              pxq_filled REAL,
              status TEXT,
              tasa REAL,
              FOREIGN KEY (id_todo) REFERENCES todo(id)
          )
      ''')

        # Tabla resumen
        cursor.execute('''
          CREATE TABLE IF NOT EXISTS resumen (
              id_todo INTEGER PRIMARY KEY,
              pxq REAL,
              tasa REAL,
              FOREIGN KEY (id_todo) REFERENCES todo(id)
          )
      ''')

        # Tabla instruments
        cursor.execute('''
          CREATE TABLE IF NOT EXISTS instruments (
              symbol TEXT PRIMARY KEY
          )
      ''')

        conn.commit()
        print("Tablas creadas exitosamente")

    except Error as e:
        print(f"Error al crear las tablas: {e}")


def main_sqlite():
    conn = create_connection()
    if conn is not None:
        create_tables(conn)
        conn.close()
    else:
        print("Error! No se pudo crear la conexión a la base de datos.")


# FX Para el bot
def query_table(conn, table='todo'):
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()

        return rows

    except Error as e:
        print(f"Error en la consulta: {e}")


def query_todo(conn):
    todo = []
    try:
        rows = query_table(conn, table='todo')

        # Convertimos a diccionario agregando monto y status
        for row in rows:
            todo.append({
                "id": row[0],
                "monto": row[1],
                "status": row[2]
            })

        return todo

    except Error as e:
        print(f"Error en la consulta: {e}")


def query_instruments(conn):

    try:
        rows = query_table(conn, table='instruments')
        instruments = [row[0] for row in rows]

        return instruments

    except Error as e:
        print(f"Error en la consulta: {e}")


# FX para tareas en la base de datos
def add_todo(conn, monto):
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO todo (monto) VALUES (?)", (monto,))
        conn.commit()
        print("To-do agregado exitosamente")

    except Error as e:
        print(f"Error en la inserción: {e}")
        conn.rollback()


def add_instruments(conn, symbols):
    try:
        cursor = conn.cursor()
        for symbol in symbols:
            # insert instruments if not exists
            cursor.execute("INSERT OR IGNORE INTO instruments (symbol) VALUES (?)", (symbol,))

        conn.commit()
        print("Instrumentos agregados exitosamente")

    except Error as e:
        print(f"Error en la inserción: {e}")
        conn.rollback()


def insertar_orden_inicial(conn, client_id, id_todo, symbol):
    """
    Inserta una nueva orden con los datos iniciales básicos
    """
    try:
        cursor = conn.cursor()
        cursor.execute('''
          INSERT INTO operaciones (clientId, id_todo, symbol)
          VALUES (?, ?, ?)
      ''', (client_id, id_todo, symbol))

        conn.commit()
        return cursor.lastrowid  # Retorna el id_operacion generado
    except Error as e:
        print(f"Error al insertar orden inicial: {e}")
        return None


def actualizar_orden(conn, id_operacion, orden_response):
    """
    Actualiza una orden existente con la respuesta del mercado
    """
    try:
        cursor = conn.cursor()

        # Extraer datos de la respuesta
        order = orden_response['order']
        price = order.get('price', 0)
        size = order.get('orderQty', 0)
        side = order.get('side', '')
        status = order.get('status', '')
        order_id = order.get('orderId', '')
        avg_price = order.get('avgPx', 0)
        filled = order.get('cumQty', 0)

        # Calcular pxq y pxq_filled
        pxq = price * size if price and size else 0
        pxq_filled = avg_price * filled if avg_price and filled else 0

        cursor.execute('''
          UPDATE operaciones 
          SET order_id = ?,
              price = ?,
              size = ?,
              side = ?,
              pxq = ?,
              avg_price = ?,
              filled = ?,
              pxq_filled = ?,
              status = ?
          WHERE id_operacion = ?
      ''', (order_id, price, size, side, pxq, avg_price, filled,
            pxq_filled, status, id_operacion))

        conn.commit()
        return True
    except Error as e:
        print(f"Error al actualizar orden: {e}")
        return False


def consultar_ordenes_por_todo(conn, id_todo):
    """
    Consulta todas las órdenes asociadas a un id_todo específico
    Retorna una lista de diccionarios con la información de cada orden
    """
    try:
        cursor = conn.cursor()

        cursor.execute('''
          SELECT 
              id_operacion,
              clientId,
              order_id,
              symbol,
              price,
              size,
              side,
              pxq,
              avg_price,
              filled,
              pxq_filled,
              status,
              tasa
          FROM operaciones 
          WHERE id_todo = ?
          ORDER BY id_operacion
      ''', (id_todo,))

        # Obtener los nombres de las columnas
        columnas = [description[0] for description in cursor.description]

        # Convertir los resultados a una lista de diccionarios
        ordenes = []
        for row in cursor.fetchall():
            orden = dict(zip(columnas, row))
            ordenes.append(orden)

        return ordenes

    except Error as e:
        print(f"Error al consultar órdenes: {e}")
        return []


def actualizar_status_todo(conn, id_todo):
    """
    Actualiza el status de un todo basado en el estado de sus órdenes
    Returns:
        str: El nuevo status del todo ('FILLED', 'REVISAR', o None si hubo error)
    """
    try:
        cursor = conn.cursor()
        FINALIZADAS = ['FILLED', 'REJECTED', 'CANCELED']

        # Obtener todas las órdenes del todo
        cursor.execute('''
          SELECT status
          FROM operaciones
          WHERE id_todo = ?
      ''', (id_todo,))

        ordenes_status = [row[0] for row in cursor.fetchall()]

        if not ordenes_status:
            print(f"No se encontraron órdenes para el todo {id_todo}")
            return None

        # Verificar si todas están finalizadas
        todas_finalizadas = all(status in FINALIZADAS for status in ordenes_status)
        todas_filled = all(status == 'FILLED' for status in ordenes_status)

        # Determinar el nuevo status
        nuevo_status = None
        if todas_finalizadas:
            if todas_filled:
                nuevo_status = 'FILLED'
            else:
                nuevo_status = 'REVISAR'

        # Actualizar el status en la tabla todo
        if nuevo_status:
            cursor.execute('''
              UPDATE todo
              SET status = ?
              WHERE id = ?
          ''', (nuevo_status, id_todo))

            conn.commit()
            print(f"Todo {id_todo} actualizado a status: {nuevo_status}")
            return nuevo_status

    except Error as e:
        print(f"Error al actualizar status del todo: {e}")
        return None


# Función auxiliar para verificar el status actual
def obtener_status_todo(conn, id_todo):
    """
    Obtiene el status actual de un todo
    """
    try:
        cursor = conn.cursor()
        cursor.execute('''
          SELECT status
          FROM todo
          WHERE id = ?
      ''', (id_todo,))

        resultado = cursor.fetchone()
        return resultado[0] if resultado else None

    except Error as e:
        print(f"Error al obtener status del todo: {e}")
        return None


if __name__ == '__main__':
    # CREAMOS LA DDBB
    main_sqlite()

    # Created/Modified files during execution:
    print("Created files:")
    print("trading.db")

    # INSERTAMOS UN TO-DO
    conn = create_connection()
    add_todo(conn, 10000)

    # INSERTAMOS SYMOLS A INSTRUMENTS
    symbols = ['DLR/NOV24', 'DLR/DIC24', 'DLR/ENE25']
    add_instruments(conn, symbols)

