#!/usr/bin/python

import cbor2 as cbor

CACHE_VALUES = []
CACHE_CODES = {}

def V (obj):
    if isinstance(obj, (tuple, list, set)):
        code = type(obj)(map(V, obj))
    elif isinstance(obj, dict):
        code = { V(k): V(v) for k, v in obj.items()}
    elif obj is None or obj is False or obj is True:
        code = obj
    else:
        assert obj is None or isinstance(obj, (bool, int, float, str, bytes))
        try:
            code, counter = CACHE_CODES[obj]
        except KeyError:
            CACHE_VALUES.append(obj)
            code, counter = CACHE_CODES[obj] = len(CACHE_CODES), iter(range(0xFFFFFFFF))
        next(counter)
    return code

orig = ( 1, 2,
    # 'b', 'banana', 'c', 'laranja', 324234, 'banana',
    'lista', ('um', 'dois', 'tres', 'quatro', 'laranja', 'cinco'),
    'lista2', ('um', 'dois', 'tres', 'quatro', 'laranja', 'cinco'),
    (None, [0,1,2,3,4,5,6,7,8,9]),
    (False, [9,8,7,6,5,4,3,2,1,0]),
    (True, [1,1,1,2,2,2,3,3,3,0,0,0, (None, False, True)]),
    [0,1,2,3] * 10,
    [0,1,2,3,4,5,6] * 20,
    'quatro', 1, 0.2, -0.3
    )

encoded = V(orig)

# OTIMIZA
# CODIGOS, ORDENADOS PELA QUANTIDADE DE USOS
NOVOS = [old for _, old in sorted(((next(counter), code) for obj, (code, counter) in CACHE_CODES.items()), reverse=True)]
CACHE_VALUES = [ CACHE_VALUES[code] for code in NOVOS ]
# NOVOS = { old: i for i, old in enumerate(NOVOS) }
NOVOS = [ b for a, b in sorted((old, i) for i, old in enumerate(NOVOS)) ]

def OPTIMIZE (code):    
    if code is None or code is False or code is True:
        code2 = code
    elif isinstance(code, int):
        code2 = NOVOS[code]
    elif isinstance(code, (tuple, list, set)):
        code2 = type(code)(map(OPTIMIZE, code))
    else:
        code2 = { OPTIMIZE(k): OPTIMIZE(v) for k, v in code.items()}
    return code2

encoded = cbor.dumps((CACHE_VALUES, OPTIMIZE(encoded)))

# RESTAURA
def RESTAURA (code):
    if code is None or code is False or code is True:
        obj = code
    elif isinstance(code, int):
        obj = CACHE_VALUES[code]
    elif isinstance(code, (tuple, list, set)):
        obj = type(code)(map(RESTAURA, code))
    else:
        obj = { RESTAURA(k): RESTAURA(v) for k, v in code.items()}
    return obj

CACHE_VALUES, decoded = cbor.loads(encoded)
decoded = RESTAURA(decoded)

print('ORIGINAL:', orig)
print('ENCODED-CBOR:', len(encoded)/len(cbor.dumps(orig)))
print('DECODED:', decoded)
