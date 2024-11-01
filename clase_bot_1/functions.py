"""
Funciones de utilidad para el bot de cauciones
"""
import json

def get_data_instruments(symbols, json_instruments):
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
    with open(json_instruments, 'r', encoding='utf-8') as file:
        data = json.load(file)

    print(data)

    maturity = {}

    instruments = data['instruments']
    for instrument in instruments:
        symbol = instrument['symbol']
        if symbol in symbols:
            maturity[symbol] = instrument['maturity']


    return None