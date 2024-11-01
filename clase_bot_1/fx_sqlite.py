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
              symbol TEXT NOT NULL,
              price REAL,
              size INTEGER,
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

if __name__ == '__main__':
    # CREAMOS LA DDBB
    main_sqlite()

    # Created/Modified files during execution:
    print("Created files:")
    print("trading.db")

    # INSERTAMOS UN TO-DO
    conn = create_connection()
    # add_todo(conn, 10000)

    # INSERTAMOS SYMOLS A INSTRUMENTS
    symbols = ['DLR/NOV24', 'DLR/DIC24', 'DLR/ENE25']
    add_instruments(conn, symbols)

