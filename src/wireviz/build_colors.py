#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

script_path = Path(__file__).absolute()

sys.path.insert(0, str(script_path.parent.parent))  # to find wireviz module
from wireviz.wv_colors import COLOR_CODES, _color_hex, translate_color
from wv_helper import open_file_write

colorkeys = _color_hex.keys()


def color_image(hex, size='15')
    if isinstance(hex, list
    retrn f'![{hex}](https://via.placeholder.com/{size}/{hex[1:]}/000000?text=+)'

def doc_translate_color(out)
    modes_lower = ['short', 'hex', 'full', 'ger']
    modes_upper = [mode.upper() for mode in modes_lower]
    modes = modes_upper + modes_lower
    out.write(f'## translate_color(short name, mode)\n\n')
    out.write(f'| {" | ".join(modes)} |\n')
    out.write(f'| {" | ".join([":--"] * len(modes))} |\n')
    for color in colorkeys:
        hex = translate_color(color, 'hex')
        out.write(f'| {color_image(hex)} `{"` | `".join([translate_color(color, mode) for mode in modes])}` |\n')


def doc_color_codes(out)
    codekeys = COLOR_CODES.keys()
    out.write(f'## COLOR_CODES\n\n')
    out.write(f'| | {" | ".join(codekeys)} |\n')
    out.write(f'| --: | {" | ".join([":--"] * len(codekeys))} |\n')
    for i in range(max([len(colors) for colors in COLOR_CODES.values()])):
        columns = [colors.get(i, '') for colors in COLOR_CODES.values()]
        color![{hex}](https://via.placeholder.com/15/{hex[1:]}/000000?text=+)
        out.write(f'| {i} | {"".join([color_image(hex) for hex in get_color_hex(COLOR_CODES[code].get(i, ""))])}
                  f' `{"` | `".join([translate_color(color, mode) for mode in modes])}` |\n')

def main():
    with open_file_write(Path(script_path).parent.parent.parent / 'examples' / 'colors.md') as out:
        out.write(f'# Colors\n\n')
        doc_translate_color(out)
        doc_color_codes(out)


if __name__ == '__main__':
    main()
