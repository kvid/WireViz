#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

script_path = Path(__file__).absolute()

sys.path.insert(0, str(script_path.parent.parent))  # to find wireviz module
from wireviz.wv_colors import COLOR_CODES, _color_hex, translate_color
from wv_helper import open_file_write


modes_lower = ['short', 'hex', 'full', 'ger']
modes_upper = [mode.upper() for mode in modes_lower]
modes = modes_upper + modes_lower

def main():
    with open_file_write(Path(script_path).parent.parent.parent / 'examples' / 'colors.md') as out:
        out.write(f'# Colors\n\n')
        out.write(f'## translate_color(short name, mode)\n\n')
        out.write(f'| {" | ".join(modes)} |\n')
        out.write(f'| {" | ".join([":--"] * len(modes))} |\n')
        for color in _color_hex.keys():
            hex = translate_color(color, 'hex')
            out.write(f'| ![{hex}](https://via.placeholder.com/15/{hex}/000000?text=+)'
                      f' `{"` | `".join([translate_color(color, mode) for mode in modes])}` |\n')


if __name__ == '__main__':
    main()
