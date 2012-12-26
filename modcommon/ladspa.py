# -*- coding: utf-8 -*-

import ctypes
from math import exp, log, sqrt
from hashlib import sha1

LADSPA_PORT_INPUT   = 0x1
LADSPA_PORT_OUTPUT  = 0x2
LADSPA_PORT_CONTROL = 0x4
LADSPA_PORT_AUDIO   = 0x8

LADSPA_HINT_BOUNDED_BELOW   = 0x1
LADSPA_HINT_BOUNDED_ABOVE   = 0x2
LADSPA_HINT_TOGGLED         = 0x4
LADSPA_HINT_SAMPLE_RATE     = 0x8
LADSPA_HINT_LOGARITHMIC     = 0x10
LADSPA_HINT_INTEGER         = 0x20
LADSPA_HINT_DEFAULT_MASK    = 0x3C0
LADSPA_HINT_DEFAULT_NONE    = 0x0
LADSPA_HINT_DEFAULT_MINIMUM = 0x40
LADSPA_HINT_DEFAULT_LOW     = 0x80
LADSPA_HINT_DEFAULT_MIDDLE  = 0xC0
LADSPA_HINT_DEFAULT_HIGH    = 0x100
LADSPA_HINT_DEFAULT_MAXIMUM = 0x140
LADSPA_HINT_DEFAULT_0       = 0x200
LADSPA_HINT_DEFAULT_1       = 0x240
LADSPA_HINT_DEFAULT_100     = 0x280
LADSPA_HINT_DEFAULT_440     = 0x2C0


class LadspaDescriptor(ctypes.Structure):
    _fields_ = [("UniqueID", ctypes.c_ulong),
                ("Label", ctypes.c_char_p),
                ("Properties", ctypes.c_int),
                ("Name", ctypes.c_char_p),
                ("Maker", ctypes.c_char_p),
                ("Copyright", ctypes.c_char_p),
                ("PortCount", ctypes.c_ulong),
                ("PortDescriptors", ctypes.c_void_p),
                ("PortNames", ctypes.c_void_p),
                ("PortRangeHints", ctypes.c_void_p),
                # The rest is not useful and has been trimmed
                ]

class LadspaPortRangeHint(ctypes.Structure):
    _fields_ = [("Descriptor", ctypes.c_int),
                ("LowerBound", ctypes.c_float),
                ("UpperBound", ctypes.c_float),
                ]


class Plugin(object):

    def __init__(self, path):
        self.path = path
        self.lib = ctypes.cdll.LoadLibrary(path)
        self.lib.ladspa_descriptor.restype = ctypes.POINTER(LadspaDescriptor)

        for key, value in self.descriptor.items():
            try:
                getattr(self, key)
            except AttributeError:
                setattr(self, key, value)

    def open(self):
        return open(self.path)


    @property
    def descriptor(self):
        d = self.lib.ladspa_descriptor(None).contents

        port_names = ctypes.cast(d.PortNames, ctypes.POINTER(ctypes.c_char_p * d.PortCount))
        port_descs = ctypes.cast(d.PortDescriptors, ctypes.POINTER(ctypes.c_int * d.PortCount))
        port_hints = ctypes.cast(d.PortRangeHints, ctypes.POINTER(LadspaPortRangeHint * d.PortCount))

        ports = {
            'audio': {
                'input': [],
                'output': [],
                },
            'control': {
                'input': [],
                'output': [],
                },
            }

        # Audio input ports are always an even number, while output
        # are odd numbers, and they are sequencially mapped.
        # Control input and output ports are sequencially mapped
        # independently, using all natural numbers
        port_index = { 'audio': { 'input': 0, 'output': 1 },
                       'control': { 'input': 0, 'output': 0 },
                       }

        for i in range(d.PortCount):
            port = {'name': port_names.contents[i] }

            desc = port_descs.contents[i]
            hint = port_hints.contents[i]

            if desc & LADSPA_PORT_INPUT:
                direction = 'input'
            elif desc & LADSPA_PORT_OUTPUT:
                direction = 'output'
            else:
                raise Exception("Porta inválida") # Plugin inválido

            if desc & LADSPA_PORT_CONTROL:
                port_type = 'control'
                id_increment = 1
            elif desc & LADSPA_PORT_AUDIO:
                port_type = 'audio'
                id_increment = 2
            else:
                raise Exception("Porta inválida") # Plugin inválido

            port['id'] = port_index[port_type][direction]
            port_index[port_type][direction] += id_increment

            desc = hint.Descriptor
            
            if desc & LADSPA_HINT_BOUNDED_BELOW:
                port['minimum'] = hint.LowerBound
            else:
                port['minimum'] = None

            if desc & LADSPA_HINT_BOUNDED_ABOVE:
                port['maximum'] = hint.UpperBound
            else:
                port['maximum'] = None

            default = desc & LADSPA_HINT_DEFAULT_MASK
            logarithm = desc & LADSPA_HINT_LOGARITHMIC

            if default == LADSPA_HINT_DEFAULT_NONE:
                port['default'] = None
            elif default == LADSPA_HINT_DEFAULT_MINIMUM:
                port['default'] = port['minimum']
            elif default == LADSPA_HINT_DEFAULT_LOW:
                if logarithm:
                    port['default'] = exp(log(hint.LowerBound) * 0.75 +
                                          log(hint.UpperBound) * 0.25)
                else:
                    port['default'] = hint.LowerBound * 0.75 + hint.UpperBound * 0.25
            elif default == LADSPA_HINT_DEFAULT_MIDDLE:
                if logarithm:
                    port['default'] = sqrt(hint.LowerBound * hint.UpperBound)
                else:
                    port['default'] = 0.5 * (hint.LowerBound + hint.UpperBound)
            elif default == LADSPA_HINT_DEFAULT_HIGH:
                if logarithm:
                    port['default'] = exp(log(hint.LowerBound) * 0.25 +
                                          log(hint.UpperBound) * 0.75)
                else:
                    port['default'] = hint.LowerBound * 0.25 + hint.UpperBound * 0.75
            elif default == LADSPA_HINT_DEFAULT_MAXIMUM:
                port['default'] = hint.UpperBound

            elif default == LADSPA_HINT_DEFAULT_0:
                port['default'] = 0
            elif default == LADSPA_HINT_DEFAULT_1:
                port['default'] = 1
            elif default == LADSPA_HINT_DEFAULT_100:
                port['default'] = 100
            elif default == LADSPA_HINT_DEFAULT_440:
                port['default'] = 440
            else:
                port['default'] = None

            port['logarithm'] = bool(logarithm)

            ports[port_type][direction].append(port)

        return {'label': d.Label,
                'properties': d.Properties,
                'name': d.Name,
                'author': d.Maker,
                'copyright': d.Copyright,
                'ports': ports,
                }

