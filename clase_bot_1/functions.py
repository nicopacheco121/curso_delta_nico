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

    data_symbols = {}

    instruments = data['instruments']
    for instrument in instruments:
        symbol = instrument['securityDescription']

        for s in symbols:
            if s == symbol:
                data_symbols[symbol] = {}
                # data_symbols[symbol]['vencimiento'] = instrument['maturityDate']
                data_symbols[symbol]['tick_price'] = instrument['minPriceIncrement']
                data_symbols[symbol]['tick_size'] = instrument['tickSize']

                maturityDate = instrument['maturityDate']

                # example "20250131", this to datetime
                year = maturityDate[0:4]
                month = maturityDate[4:6]
                day = maturityDate[6:8]
                data_symbols[symbol]['vencimiento'] = f"{year}-{month}-{day}"


                break


    return data_symbols


def calc_montos(ddbb_precios, monto_operar, data_symbols, multiplicador=1000):
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
    for i in ddbb_precios:
        if ddbb_precios[i]['OF']:
            size = ddbb_precios[i]['OF'][0]['size']
            size_total += size

        elif ddbb_precios[i]['BI']:
            size = ddbb_precios[i]['BI'][0]['size']
            size_total += size

    for i in ddbb_precios:
        tick_size = float(data_symbols[i]['tick_size'])

        if ddbb_precios[i]['OF'] or ddbb_precios[i]['BI']:
            size_i = ddbb_precios[i]['OF'][0]['size'] if ddbb_precios[i]['OF'] else ddbb_precios[i]['BI'][0]['size']
            price_i = ddbb_precios[i]['OF'][0]['price'] if ddbb_precios[i]['OF'] else ddbb_precios[i]['BI'][0]['price']

            monto_ars = (size_i / size_total) * (monto_operar) + monto_sobrante

            contratos = monto_ars / (price_i * multiplicador)
            # round to the lower tick size
            contratos_adj = int(contratos // tick_size) * tick_size

            pxq = price_i * contratos_adj * multiplicador
            monto_sobrante = monto_ars - pxq

            ordenes[i] = {'monto': pxq, 'size': contratos_adj, 'price': price_i}

    print('Monto sobrante:', round(monto_sobrante))

    return ordenes








