#!/usr/bin/python

import cbor2 as cbor

#
class CData:

    def __init__ (self, x=None):
        self.CODES = {}
        self.VALS = []
        if x is not None:
            x = self.ENC(x)
        self.x = x

    def append (self, v):
        self.x.append(self.ENC(v))

    def add (self, v):
        self.x.add(self.ENC(v))

    # CACHE A VALUE, AND ENCODE IT AS CODE
    def ENC (self, obj):
        if isinstance(obj, (tuple, list, set)):
            code = type(obj)(map(self.ENC, obj))
        elif isinstance(obj, dict):
            code = { self.ENC(k): self.ENC(v) for k, v in obj.items()}
        elif (obj is None
           or obj is False
           or obj is True):
            code = obj
        else:
            assert obj is None or isinstance(obj, (bool, int, float, str, bytes))
            try:
                code, counter = self.CODES[obj]
            except KeyError:
                self.VALS.append(obj)
                code, counter = self.CODES[obj] = len(self.CODES), iter(range(0xFFFFFFFF))
            next(counter)
        return code

    # STORE
    def encode (self):

        assert len(self.CODES) == len(self.VALS)

        # OPTIMIZE
        def OPTIMIZE (self, code):
            if code is None or code is False or code is True:
                code2 = code
            elif isinstance(code, int):
                code2 = NOVOS[code]
            elif isinstance(code, (tuple, list, set)):
                code2 = type(code)(map(OPTIMIZE, code))
            else:
                code2 = { OPTIMIZE(k): OPTIMIZE(v) for k, v in code.items()}
            return code2
        
        # OTIMIZA
        # CODIGOS, ORDENADOS PELA QUANTIDADE DE USOS
        NOVOS = [old for _, old in sorted(((next(counter), code) for obj, (code, counter) in self.CODES.items()), reverse=True)]
        self.VALS = [ self.VALS[code] for code in NOVOS ]
      # NOVOS = { old: i for i, old in enumerate(NOVOS) }
        NOVOS = [ b for a, b in sorted((old, i) for i, old in enumerate(NOVOS)) ]
        encoded = cbor.dumps((self.VALS, self.OPTIMIZE(self.x)))
        self.CODES.clear()
        self.VALS.clear()
        self.x = None
        return encoded

# LOAD
def CDATA_LOAD (encoded):

    # DECODE A CODE, TO ITS VALUE
    def DEC (code):
        if code is None or code is False or code is True:
            obj = code
        elif isinstance(code, int):
            obj = VALS[code]
        elif isinstance(code, (tuple, list, set)):
            obj = type(code)(map(DEC, code))
        else:
            obj = { DEC(k): DEC(v) for k, v in code.items() }
        return obj

    VALS, x = cbor.loads(encoded)
    
    return DEC(x)


######

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

encoded = CData(orig).encode()

decoded = CDATA_LOAD(encoded)

print('ORIGINAL:', orig)
print('ENCODED-CBOR:', len(encoded)/len(cbor.dumps(orig)))
print('DECODED:', decoded)
