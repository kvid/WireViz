#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from collections import defaultdict
from pathlib import Path

script_path = Path(__file__).absolute()

sys.path.insert(0, str(script_path.parent.parent))  # to find wireviz module
from wireviz.wv_colors import COLOR_CODES, _color_hex, translate_color
from wv_helper import open_file_write

colorkeys = _color_hex.keys()
key_error = defaultdict(int)


def get_color_codes(key, n):
    try:
        codes = COLOR_CODES[key][n]
        return [codes[i:i+2] for i in range(0, len(codes), 2)]
    except IndexError:
        return []


def color_image(code, size=15):
    try:
        hex = _color_hex[code]
        return f'![{hex}](https://via.placeholder.com/{size}/{hex[1:]}/000000?text=+)'
    except KeyError:
        key_error[code] += 1
        return color_image('WH', size).replace('+)', 'N+A)')


def doc_translate_color(out):
    modes_lower = ['short', 'hex', 'full', 'ger']
    modes_upper = [mode.upper() for mode in modes_lower]
    modes = modes_upper + modes_lower
    out.write(f'## translate_color(short name, mode)\n\n')
    out.write(f'| {" | ".join(modes)} |\n')
    out.write(f'| {" | ".join([":--"] * len(modes))} |\n')
    for color in colorkeys:
        out.write(f'| {color_image(color)} `{"` | `".join([translate_color(color, mode) for mode in modes])}` |\n')


def doc_color_codes(out):
    codekeys = COLOR_CODES.keys()
    out.write(f'## COLOR_CODES\n\n')
    out.write(f'| | {" | ".join(codekeys)} |\n')
    out.write(f'| --: | {" | ".join([":--"] * len(codekeys))} |\n')
    for r in range(max([len(colors) for colors in COLOR_CODES.values()])):
        columns = [' '.join([f'{color_image(c)} `{c}`' for c in get_color_codes(k, r)]) for k in codekeys]
        out.write(f'| {r} | {" | ".join(columns)} |\n')


def main():
    with open_file_write(Path(script_path).parent.parent.parent / 'examples' / 'colors.md') as out:
        out.write(f'# Colors\n\n')
        doc_translate_color(out)
        doc_color_codes(out)
    for key, count in key_error.items():
        print(f'{count} bad `{key}` values')


if __name__ == '__main__':
    main()
