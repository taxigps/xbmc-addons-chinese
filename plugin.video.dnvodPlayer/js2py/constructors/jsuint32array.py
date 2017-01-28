# this is based on jsarray.py

from ..base import *
try:
    import numpy
except:
    pass

@Js
def Uint32Array():
    TypedArray = (PyJsInt8Array,PyJsUint8Array,PyJsUint8ClampedArray,PyJsInt16Array,PyJsUint16Array,PyJsInt32Array,PyJsUint32Array,PyJsFloat32Array,PyJsFloat64Array)
    a = arguments[0]
    if isinstance(a, PyJsNumber): # length
        length = a.to_uint32()
        if length!=a.value:
            raise MakeError('RangeError', 'Invalid array length')
        temp = Js(numpy.full(length, 0, dtype=numpy.uint32))
        temp.put('length', a)
        return temp
    elif isinstance(a, PyJsString): # object (string)
        temp = Js(numpy.array(list(a.value), dtype=numpy.uint32))
        temp.put('length', Js(len(list(a.value))))
        return temp
    elif isinstance(a, PyJsArray): # object (array)
        array = a.to_list()
        array = [(int(item.value) if item.value != None else 0) for item in array]
        temp = Js(numpy.array(array, dtype=numpy.uint32))
        temp.put('length', Js(len(array)))
        return temp
    elif isinstance(a,TypedArray) or isinstance(a,PyJsArrayBuffer): # TypedArray / buffer
        if len(arguments) > 1:
            offset = int(arguments[1].value)
        else:
            offset = 0
        if len(arguments) == 3:
            length = int(arguments[2].value)
        else:
            length = a.get('length').to_uint32()
        temp = Js(numpy.frombuffer(a.array, dtype=numpy.uint32, count=length, offset=offset))
        temp.put('length', Js(length))
        return temp

    elif isinstance(a,PyObjectWrapper): # object (Python object)
        if len(arguments) > 1:
            offset = int(arguments[1].value)
        else:
            offset = 0
        if len(arguments) == 3:
            length = int(arguments[2].value)
        else:
            length = len(a.obj)
        temp = Js(numpy.frombuffer(a.obj, dtype=numpy.uint32, count=length, offset=offset))
        temp.put('length', Js(length))
        return temp
    temp = Js(numpy.full(0, 0, dtype=numpy.uint32))
    temp.put('length', Js(0))
    return temp

Uint32Array.create = Uint32Array
Uint32Array.own['length']['value'] = Js(3)

Uint32Array.define_own_property('prototype', {'value': Uint32ArrayPrototype,
                                         'enumerable': False,
                                         'writable': False,
                                         'configurable': False})

Uint32ArrayPrototype.define_own_property('constructor', {'value': Uint32Array,
                                                    'enumerable': False,
                                                    'writable': True,
                                                    'configurable': True})

Uint32ArrayPrototype.define_own_property('BYTES_PER_ELEMENT', {'value': Js(4),
                                                    'enumerable': False,
                                                    'writable': False,
                                                    'configurable': False})
