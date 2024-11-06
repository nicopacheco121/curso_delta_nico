# models/database.py
import sqlite3
from sqlite3 import Error
from typing import List, Dict, Optional, Any


class Database:
    def __init__(self, db_name='cauciones_clases.db'):
        """
        Initialize the Database object
        :param db_name:
        """
        self.db_name = db_name
        self.conn = None

    def connect(self):
        """
        Connect to the database
        :return:
        """
        try:
            self.conn = sqlite3.connect(self.db_name)
            return self.conn
        except Error as e:
            print(f"Error connecting to database: {e}")
            return None

    def create_tables(self):
        """
        Crea las tablas si no existen
        :return:
        """
        if not self.conn:
            self.connect()

        try:
            cursor = self.conn.cursor()

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

            self.conn.commit()
            print("Tablas creadas exitosamente")
        except Error as e:
            print(f"Error creating tables: {e}")

    def add_todo(self, monto: float) -> bool:
        """
        Agrega una nueva tarea a la tabla todo.
        Args:
            monto (float): Monto de la operación
        Returns:
            bool: True si se agregó correctamente, False en caso contrario
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO todo (monto) VALUES (?)", (monto,))
            self.conn.commit()
            print("To-do agregado exitosamente")
            return True
        except Error as e:
            print(f"Error en la inserción: {e}")
            self.conn.rollback()
            return False

    def add_instruments(self, symbols: List[str]) -> bool:
        """
        Agrega instrumentos a la tabla instruments.
        Args:
            symbols (List[str]): Lista de símbolos a agregar
        Returns:
            bool: True si se agregaron correctamente, False en caso contrario
        """
        try:
            cursor = self.conn.cursor()
            for symbol in symbols:
                cursor.execute("INSERT OR IGNORE INTO instruments (symbol) VALUES (?)", (symbol,))
            self.conn.commit()
            print("Instrumentos agregados exitosamente")
            return True
        except Error as e:
            print(f"Error en la inserción: {e}")
            self.conn.rollback()
            return False

    def query_todo(self) -> List[Dict[str, Any]]:
        """
        Consulta todas las tareas pendientes.
        Returns:
            List[Dict]: Lista de diccionarios con las tareas
        """
        todo = []
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM todo")
            rows = cursor.fetchall()

            for row in rows:
                todo.append({
                    "id": row[0],
                    "monto": row[1],
                    "status": row[2]
                })
            return todo
        except Error as e:
            print(f"Error en la consulta: {e}")
            return []

    def query_instruments(self) -> List[str]:
        """
        Consulta todos los instrumentos.
        Returns:
            List[str]: Lista de símbolos
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT symbol FROM instruments")
            return [row[0] for row in cursor.fetchall()]
        except Error as e:
            print(f"Error en la consulta: {e}")
            return []

    def insert_order(self, client_id: str, id_todo: int, symbol: str) -> Optional[int]:
        """
        Inserta una nueva orden con datos iniciales.
        Args:
            client_id (str): ID del cliente
            id_todo (int): ID de la tarea relacionada
            symbol (str): Símbolo del instrumento
        Returns:
            Optional[int]: ID de la operación insertada
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO operaciones (clientId, id_todo, symbol)
                VALUES (?, ?, ?)
            ''', (client_id, id_todo, symbol))
            self.conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error al insertar orden inicial: {e}")
            return None

    def update_order(self, id_operacion: int, orden_response: Dict) -> bool:
        """
        Actualiza una orden existente con la respuesta del mercado.
        Args:
            id_operacion (int): ID de la operación a actualizar
            orden_response (Dict): Respuesta del mercado
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario
        """
        try:
            cursor = self.conn.cursor()
            order = orden_response['order']

            # Extraer datos
            price = order.get('price', 0)
            size = order.get('orderQty', 0)
            side = order.get('side', '')
            status = order.get('status', '')
            order_id = order.get('orderId', '')
            avg_price = order.get('avgPx', 0)
            filled = order.get('cumQty', 0)

            # Calcular valores
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

            self.conn.commit()
            return True
        except Error as e:
            print(f"Error al actualizar orden: {e}")
            return False

    def get_orders_by_todo(self, id_todo: int) -> List[Dict[str, Any]]:
        """
        Consulta todas las órdenes asociadas a un id_todo específico.
        Args:
            id_todo (int): ID de la tarea
        Returns:
            List[Dict]: Lista de órdenes
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT 
                    id_operacion, clientId, order_id, symbol,
                    price, size, side, pxq, avg_price,
                    filled, pxq_filled, status, tasa
                FROM operaciones 
                WHERE id_todo = ?
                ORDER BY id_operacion
            ''', (id_todo,))

            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Error as e:
            print(f"Error al consultar órdenes: {e}")
            return []

    def update_todo_status(self, id_todo: int) -> Optional[str]:
        """
        Actualiza el status de un todo basado en sus órdenes.
        Args:
            id_todo (int): ID de la tarea
        Returns:
            Optional[str]: Nuevo status o None si hubo error
        """
        try:
            cursor = self.conn.cursor()
            FINALIZADAS = ['FILLED', 'REJECTED', 'CANCELED']

            cursor.execute('''
                SELECT status
                FROM operaciones
                WHERE id_todo = ?
            ''', (id_todo,))

            ordenes_status = [row[0] for row in cursor.fetchall()]

            if not ordenes_status:
                print(f"No se encontraron órdenes para el todo {id_todo}")
                return None

            todas_finalizadas = all(status in FINALIZADAS for status in ordenes_status)
            todas_filled = all(status == 'FILLED' for status in ordenes_status)

            nuevo_status = None
            if todas_finalizadas:
                nuevo_status = 'FILLED' if todas_filled else 'REVISAR'

            if nuevo_status:
                cursor.execute('''
                    UPDATE todo
                    SET status = ?
                    WHERE id = ?
                ''', (nuevo_status, id_todo))
                self.conn.commit()
                return nuevo_status

            return None
        except Error as e:
            print(f"Error al actualizar status del todo: {e}")
            return None

    def close(self) -> None:
        """Cierra la conexión a la base de datos"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Permite usar la clase con with statement"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cierra la conexión al salir del with statement"""
        self.close()


# Ejemplo de uso de la clase Database
if __name__ == '__main__':
    # Usando context manager
    with Database() as db:
        # Crear tablas
        db.create_tables()

        # Agregar una tarea
        db.add_todo(10000000)

        # Agregar instrumentos
        symbols = ['DLR/NOV24', 'DLR/DIC24', 'DLR/ENE25']
        db.add_instruments(symbols)

        # Consultar tareas pendientes
        todos = db.query_todo()
        print("Tareas pendientes:", todos)

        # Consultar instrumentos
        instruments = db.query_instruments()
        print("Instrumentos:", instruments)

    # La conexión se cierra automáticamente al salir del with
