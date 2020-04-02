""" Sord number generator"""

def sord_generator(fuel_type, id):
    if id in range(0, 10):
        sord = f'SORD{fuel_type}-000{id}'
    elif id in range(10, 100):
        sord = f'SORD{fuel_type}-00{id}'
    elif id in range(100, 1000):
        sord = f'SORD{fuel_type}-0{id}'
    else:
        sord = f'SORD{fuel_type}-{id}'
    return sord

