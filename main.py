import sys
import yaml

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
                lines.append({linechunks[0]: linechunks[1:]})

    in_codes = False
    sections = {'meta': {},
                'codes': {}
                }
    for line in lines:
        if 'codes' in line:
            in_codes = True if 'begin' in line else False
            continue
        if in_codes:
            sections['codes'][line[0]] = line[1]
        else:
            sections['meta'][line[0]] = line[1:]
    return sections


def parse_remote_code(code=None, one=None, zero=None):
    if not all(code, one, zero):
        raise Exception("fuck you")
    name = code[0]
    bit_string = "{:b}".format(int(code[1]))
    return {name: [one if b == '1' else zero for b in bit_string]}


def parse_lines(sections):
    # Get zero and one values
    zero_raw = sections['meta']['zero']
    one_raw = sections['meta']['one']
    zero = (int(zero_raw[0]), -1 * int(zero_raw[1]))
    one = (int(one_raw[0]), -1 * int(one_raw[1]))

    # Get header
    header_raw = sections['meta']['header']
    header = (int(header_raw[0], -1 * int(header_raw[1])))

    # 

