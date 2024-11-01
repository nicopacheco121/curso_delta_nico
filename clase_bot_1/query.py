import sqlite3


def ejemplos_queries():
    conn = sqlite3.connect('trading.db')
    cursor = conn.cursor()

    # 1. Obtener todas las operaciones de un todo específico con su monto
    query1 = """
  SELECT t.id, t.monto, o.symbol, o.price, o.size
  FROM todo t
  JOIN operaciones o ON t.id = o.id_todo
  WHERE t.id = 1
  """

    # 2. Obtener el resumen junto con el monto original del todo
    query2 = """
  SELECT t.id, t.monto, r.pxq, r.tasa
  FROM todo t
  JOIN resumen r ON t.id = r.id_todo
  """

    # 3. Obtener operaciones con información del instrumento
    query3 = """
  SELECT o.symbol, o.price, o.size, i.dias
  FROM operaciones o
  JOIN instruments i ON o.symbol = i.symbol
  """

    # 4. Reporte completo: todo con sus operaciones y resumen
    query4 = """
  SELECT 
      t.id,
      t.monto,
      o.symbol,
      o.price,
      o.size,
      r.pxq as resumen_pxq,
      r.tasa as resumen_tasa
  FROM todo t
  LEFT JOIN operaciones o ON t.id = o.id_todo
  LEFT JOIN resumen r ON t.id = r.id_todo
  """

    # Ejemplo de inserción de datos relacionados
    def insertar_operacion_completa(monto, symbol, price, size):
        try:
            # Primero insertamos en todo
            cursor.execute("INSERT INTO todo (monto) VALUES (?)", (monto,))
            id_todo = cursor.lastrowid

            # Luego en operaciones
            pxq = price * size
            cursor.execute("""
              INSERT INTO operaciones 
              (id_todo, symbol, price, size, pxq) 
              VALUES (?, ?, ?, ?, ?)
          """, (id_todo, symbol, price, size, pxq))

            # Y finalmente en resumen
            cursor.execute("""
              INSERT INTO resumen 
              (id_todo, pxq, tasa) 
              VALUES (?, ?, ?)
          """, (id_todo, pxq, 0.1))  # tasa ejemplo

            conn.commit()
            print("Operación insertada exitosamente")

        except sqlite3.Error as e:
            print(f"Error en la inserción: {e}")
            conn.rollback()

    # Ejemplo de uso:
    # insertar_operacion_completa(1000, "AAPL", 150.5, 10)

    conn.close()