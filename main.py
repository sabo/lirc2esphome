import sys
from math import copysign
from yaml import dump, load


def same_sign(x, y):
    if copysign(1, x) == copysign(1, y):
        return True
    else:
        return False

def normalize_code(code):
    code_pairs = [(code[i], code[i+1])
                   for i in range(len(code) - 1)]
    canonicalized = False
    new_code = []
    skip = False
    for v, nv in code_pairs:
        if skip:
            skip = False
            continue
        if same_sign(v, nv):
            canonicalized = True
            new_code.append(v + nv)
            skip = True
        else:
            new_code.append(v)

    if canonicalized is False:
        return code
    else:
        return normalize_code(new_code)


def tokenize(filename):
    with open(filename, 'r') as f:
        lines = []
        for line in f.readlines():
            linechunks = []
            for chunk in line.split():
                if chunk.startswith('#'):
                    break
                else:
                    linechunks.append(chunk)
            if len(linechunks) > 0:
                lines.append((linechunks[0], linechunks[1:]))

    in_codes = False
    sections = {'meta': {},
                'codes': {}
                }
    for key, value in lines:
        if key == 'begin':
            in_codes = True if 'codes' in value else False
            continue
        elif key == 'end':
            in_codes = False if 'codes' in value else in_codes
            continue
        if in_codes:
            sections['codes'][key] = value[0]
        else:
            sections['meta'][key] = value
    return sections


def pair_to_tuple(raw):
    return [int(raw[0]), -1 * int(raw[1])]


def parse_remote_code(code=None, one=None, zero=None, bits=32):
    if not all((code, one, zero)):
        raise Exception("fuck you")
    name = code[0]
    bit_string = "{:b}".format(int(code[1], 16))
    if len(bit_string) > bits:
        # Pad it out with zeros on the left
        bit_string = ("0" * (bits - len(bit_string))) + bit_string
    translated_code = [one if b == '1' else zero for b in bit_string]
    # Flatten the code
    return (name, [y for x in translated_code for y in x])


def parse_lines(sections):
    # get total length
    bits = int(sections['meta']['bits'][0])
    # Get zero and one values
    zero = pair_to_tuple(sections['meta']['zero'])
    one = pair_to_tuple(sections['meta']['one'])

    # Get repeat
    repeat = pair_to_tuple(sections['meta']['repeat'])

    # Get header
    header = pair_to_tuple(sections['meta']['header'])

    # Get ptrail and gap
    ptrail = [int(sections['meta']['ptrail'][0])]
    gap = [int(sections['meta']['gap'][0])]

    # Name
    name = sections['meta']['name'][0]

    # Get binary versions of codes
    codes = {}
    for code in sections['codes'].items():
        key, data = parse_remote_code(code, one=one, zero=zero, bits=bits)
        # Build the full code
        full_code = header + data + ptrail + gap
        full_code = normalize_code(full_code)

        codes.update({name + ' ' + key: full_code})
    # Add the special repeat code
    codes['repeat_signal'] = repeat

    return codes

def esphomeificate(codes, transmitter_id=None, frequency=None):
    switches = []
    for name, code in codes.items():
        transmit_options = {'code': code}
        if transmitter_id:
            transmit_options['transmitter_id'] = transmitter_id
        if frequency:
            transmit_options['carrier_frequency'] = frequency

        switch = {'platform': 'template',
                  'name': name,
                  'turn_on_action': {
                      'remote_transmitter.transmit_raw': transmit_options
                  }
                 }
        switches.append(switch)
    return switches


def add_to_esp_file(filename, switches, out_name):
    with open(filename, 'r') as f:
        esp_file = load(f)
    if 'switch' in esp_file:
        esp_file['switch'].extend(switches)
    else:
        esp_file['switch'] = switches
    with open(out_name, 'w') as f:
        dump(esp_file, f, default_flow_style=None)

