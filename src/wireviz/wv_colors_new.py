# -*- coding: utf-8 -*-

from collections import namedtuple
from dataclasses import dataclass, field
from enum import Enum
from typing import List

KnownColor = namedtuple("KnownColor", "html code_de full_en full_de")
ColorOutputMode = Enum("ColorOutputMode", "EN_LOWER EN_UPPER DE_LOWER DE_UPPER HTML_LOWER HTML_UPPER")

known_colors = {
    "BK": KnownColor("#000000", "sw", "black", "schwarz"),
    "WH": KnownColor("#ffffff", "ws", "white", "weiß"),
    "GY": KnownColor("#999999", "gr", "grey", "grau"),
    "PK": KnownColor("#ff66cc", "rs", "pink", "rosa"),
    "RD": KnownColor("#ff0000", "rt", "red", "rot"),
    "OG": KnownColor("#ff8000", "or", "orange", "orange"),
    "YE": KnownColor("#ffff00", "ge", "yellow", "gelb"),
    "OL": KnownColor("#708000", "ol", "olive green", "olivgrün"),
    "GN": KnownColor("#00ff00", "gn", "green", "grün"),
    "TQ": KnownColor("#00ffff", "tk", "turquoise", "türkis"),
    "LB": KnownColor("#a0dfff", "hb", "light blue", "hellblau"),
    "BU": KnownColor("#0066ff", "bl", "blue", "blau"),
    "VT": KnownColor("#8000ff", "vi", "violet", "violett"),
    "BN": KnownColor("#895956", "br", "brown", "braun"),
    "BG": KnownColor("#ceb673", "bg", "beige", "beige"),
    "IV": KnownColor("#f5f0d0", "eb", "ivory", "elfenbein"),
    "SL": KnownColor("#708090", "si", "slate", "schiefer"),
    "CU": KnownColor("#d6775e", "ku", "copper", "Kupfer"),
    "SN": KnownColor("#aaaaaa", "vz", "tin", "verzinkt"),
    "SR": KnownColor("#84878c", "ag", "silver", "Silber"),
    "GD": KnownColor("#ffcf80", "au", "gold", "Gold"),
}

color_output_mode = ColorOutputMode.EN_UPPER
padding_amount = 1

def convert_case(inp):
    if "_LOWER" in color_output_mode.name:
        return inp.lower()
    elif "_UPPER" in color_output_mode.name:
        return inp.upper()
    else:  # currently not used
        return inp

@dataclass
class SingleColor():
    _code_en: str
    _code_de: str
    _html: str

    @property
    def code_en(self):
        return convert_case(self._code_en)
        # repeat for _code_de, _html

    @property
    def code_de(self):
        return convert_case(self._code_de)
        # repeat for _code_de, _html

    @property
    def html(self):
        return convert_case(self._html)
        # repeat for _code_de, _html

    @property
    def known(self):
        return self.code_en.upper() in known_colors.keys()

    def __init__(self, inp):
        if isinstance(inp, int):
            hex_str = f"#{inp:06x}"
            self._html = hex_str
            self._code_en = hex_str  # do not perform reverse lookup
            self._code_de = hex_str
        elif inp.upper() in known_colors.keys():
            inp_upper = inp.upper()
            self._code_en = inp_upper
            self._code_de = known_colors[inp_upper].code_de
            self._html = known_colors[inp_upper].html
        else:  # assume valid HTML color
            self._html = inp
            self._code_en = inp
            self._code_de = inp

    @property
    def html_padded(self):
        return ":".join([self.html] * padding_amount)

    def __str__(self):
        if self.known and "EN_" in color_output_mode.name:
            return self.code_en
        elif self.known and "DE_" in color_output_mode.name:
            return self.code_de
        else:
            return self.html

@dataclass
class MultiColor():
    colors: List[SingleColor] = field(default_factory=list)

    def __init__(self, inp):
        self.colors = []
        if isinstance(inp, List):  # input is already a list
            for item in inp:
                if isinstance(item, SingleColor):
                    self.colors.append(item)
                else:  # string
                    self.colors.append(SingleColor(item))
        elif isinstance(inp, SingleColor):  # single color
            self.colors = [inp]
        else:  # split input into list
            if ":" in str(inp):
                self.colors = [SingleColor(item) for item in inp.split(":")]
            else:
                if isinstance(inp, int):
                    self.colors = [SingleColor(inp)]
                elif len(inp) % 2 == 0:
                    items = [inp[i:i+2] for i in range(0, len(inp), 2)]
                    known = [item.upper() in known_colors.keys() for item in items]
                    if all(known):
                        self.colors = [SingleColor(item) for item in items]
                    else:  # assume it's a HTML color name
                        self.colors = [SingleColor(inp)]
                else:  # assume it's a HTML color name
                    self.colors = [SingleColor(inp)]


    def __len__(self):
        return len(self.colors)

    def __str__(self):
        if "EN_" in color_output_mode.name or "DE_" in color_output_mode.name:
            joiner = "" if self.all_known else ":"
        elif "HTML_" in color_output_mode.name:
            joiner = ":"
        else:
            joiner = "???"
        return joiner.join([str(color) for color in self.colors])

    @property
    def all_known(self):
        return all([color.known for color in self.colors])

    @property
    def html(self):
        return ":".join([color.html for color in self.colors])

    @property
    def html_padded(self):
        if len(self) == 0:
            out = []
        elif len(self) == 1:
            out = [self.colors[0] for i in range(3)]
        elif len(self) == 2:
            out = [self.colors[0], self.colors[1], self.colors[0]]
        elif len(self) == 3:
            out = self.colors
        else:
            raise Exception(f"Padding not supported for len {len(selfq)}")
        return ":".join([str(color) for color in out])

COLOR_CODES = {
    # fmt: off
    "DIN": [
        "WH", "BN", "GN", "YE", "GY", "PK", "BU", "RD", "BK", "VT", "GYPK", "RDBU",
        "WHGN", "BNGN", "WHYE", "YEBN", "WHGY", "GYBN", "WHPK", "PKBN", "WHBU", "BNBU",
        "WHRD", "BNRD", "WHBK", "BNBK", "GYGN", "YEGY", "PKGN", "YEPK", "GNBU", "YEBU",
        "GNRD", "YERD", "GNBK", "YEBK", "GYBU", "PKBU", "GYRD", "PKRD", "GYBK", "PKBK",
        "BUBK", "RDBK", "WHBNBK", "YEGNBK", "GYPKBK", "RDBUBK", "WHGNBK", "BNGNBK",
        "WHYEBK", "YEBNBK", "WHGYBK", "GYBNBK", "WHPKBK", "PKBNBK", "WHBUBK",
        "BNBUBK", "WHRDBK", "BNRDBK",
    ],
    # fmt: on
    "IEC": ["BN", "RD", "OG", "YE", "GN", "BU", "VT", "GY", "WH", "BK"],
    "BW": ["BK", "WH"],
    # 25-pair color code - see also https://en.wikipedia.org/wiki/25-pair_color_code
    # 5 major colors (WH,RD,BK,YE,VT) combined with 5 minor colors (BU,OG,GN,BN,SL).
    # Each POTS pair tip (+) had major/minor color, and ring (-) had minor/major color.
    # fmt: off
    "TEL": [  # 25x2: Ring and then tip of each pair
        "BUWH", "WHBU", "OGWH", "WHOG", "GNWH", "WHGN", "BNWH", "WHBN", "SLWH", "WHSL",
        "BURD", "RDBU", "OGRD", "RDOG", "GNRD", "RDGN", "BNRD", "RDBN", "SLRD", "RDSL",
        "BUBK", "BKBU", "OGBK", "BKOG", "GNBK", "BKGN", "BNBK", "BKBN", "SLBK", "BKSL",
        "BUYE", "YEBU", "OGYE", "YEOG", "GNYE", "YEGN", "BNYE", "YEBN", "SLYE", "YESL",
        "BUVT", "VTBU", "OGVT", "VTOG", "GNVT", "VTGN", "BNVT", "VTBN", "SLVT", "VTSL",
    ],
    "TELALT": [  # 25x2: Tip and then ring of each pair
        "WHBU", "BU", "WHOG", "OG", "WHGN", "GN", "WHBN", "BN", "WHSL", "SL",
        "RDBU", "BURD", "RDOG", "OGRD", "RDGN", "GNRD", "RDBN", "BNRD", "RDSL", "SLRD",
        "BKBU", "BUBK", "BKOG", "OGBK", "BKGN", "GNBK", "BKBN", "BNBK", "BKSL", "SLBK",
        "YEBU", "BUYE", "YEOG", "OGYE", "YEGN", "GNYE", "YEBN", "BNYE", "YESL", "SLYE",
        "VTBU", "BUVT", "VTOG", "OGVT", "VTGN", "GNVT", "VTBN", "BNVT", "VTSL", "SLVT",
    ],
    # fmt: on
    "T568A": ["WHGN", "GN", "WHOG", "BU", "WHBU", "OG", "WHBN", "BN"],
    "T568B": ["WHOG", "OG", "WHGN", "BU", "WHBU", "GN", "WHBN", "BN"],
}
