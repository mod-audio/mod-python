def hardware_connections(pedalboard):
    m = {
        'audio_inputs': 0,
        'audio_outputs': 0,
        'midi_inputs': 0,
        'midi_outputs': 0,
        'rotary_addressings': 0,
        'footswitch_addressings': 0,
        'pedal_addressings': 0,
        }
    for connection in pedalboard['connections']:
        if connection[0] == 'system':
            if connection[1].startswith('midi'):
                m['midi_inputs'] += 1
            else:
                m['audio_inputs'] += 1
        if connection[2] == 'system':
            if connection[3].startswith('midi'):
                m['midi_outputs'] += 1
            else:
                m['audio_outputs'] += 1
    for instance in pedalboard['instances']:
        addressing = instance.get('addressing', {})
        for symbol, address in addressing.items():
            actuator = address.get('actuator', [-1, -1, -1, -1])
            # TODO hardcoded hardware IDs here
            if actuator[0] == 0 and actuator[2] == 1:
                # hwtype quadra acttype footswitch
                typ = 'footswitch'
            elif actuator[0] == 0 and actuator[2] == 2:
                # hwtype quadra acttype rotary
                typ = 'rotary'
            elif actuator[0] == 1:
                # hwtype expression pedal
                typ = 'pedal'
            else:
                continue
            m['%s_addressings' % typ] += 1

    return m
