# this is based on jsarray.py

from ..base import *
try:
    import numpy
except:
    pass

@Js
def Int16Array():
    TypedArray = (PyJsInt8Array,PyJsUint8Array,PyJsUint8ClampedArray,PyJsInt16Array,PyJsUint16Array,PyJsInt32Array,PyJsUint32Array,PyJsFloat32Array,PyJsFloat64Array)
    a = arguments[0]
    if isinstance(a, PyJsNumber): # length
        length = a.to_uint32()
        if length!=a.value:
            raise MakeError('RangeError', 'Invalid array length')
        temp = Js(numpy.full(length, 0, dtype=numpy.int16))
        temp.put('length', a)
        return temp
    elif isinstance(a, PyJsString): # object (string)
        temp = Js(numpy.array(list(a.value), dtype=numpy.int16))
        temp.put('length', Js(len(list(a.value))))
        return temp
    elif isinstance(a, PyJsArray): # object (array)
        array = a.to_list()
        array = [(int(item.value) if item.value != None else 0) for item in array]
        temp = Js(numpy.array(array, dtype=numpy.int16))
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
        temp = Js(numpy.frombuffer(a.array, dtype=numpy.int16, count=length, offset=offset))
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
        temp = Js(numpy.frombuffer(a.obj, dtype=numpy.int16, count=length, offset=offset))
        temp.put('length', Js(length))
        return temp
    temp = Js(numpy.full(0, 0, dtype=numpy.int16))
    temp.put('length', Js(0))
    return temp

Int16Array.create = Int16Array
Int16Array.own['length']['value'] = Js(3)

Int16Array.define_own_property('prototype', {'value': Int16ArrayPrototype,
                                         'enumerable': False,
                                         'writable': False,
                                         'configurable': False})

Int16ArrayPrototype.define_own_property('constructor', {'value': Int16Array,
                                                    'enumerable': False,
                                                    'writable': True,
                                                    'configurable': True})

Int16ArrayPrototype.define_own_property('BYTES_PER_ELEMENT', {'value': Js(2),
                                                    'enumerable': False,
                                                    'writable': False,
                                                    'configurable': False})
