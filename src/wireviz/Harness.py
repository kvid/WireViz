# -*- coding: utf-8 -*-

import re
from collections import Counter
from dataclasses import dataclass
from itertools import zip_longest
from pathlib import Path
from typing import Any, List, Union

from graphviz import Graph

from wireviz import APP_NAME, APP_URL, __version__, wv_colors
from wireviz.DataClasses import (
    Cable,
    Connector,
    MateComponent,
    MatePin,
    Metadata,
    Options,
    Side,
    Tweak,
)
from wireviz.svgembed import embed_svg_images_file
from wireviz.wv_bom import (
    HEADER_MPN,
    HEADER_PN,
    HEADER_SPN,
    bom_list,
    component_table_entry,
    generate_bom,
    get_additional_component_table,
    pn_info_string,
)
from wireviz.wv_colors import get_color_hex, translate_color
from wireviz.wv_gv_html import (
    apply_dot_tweaks,
    gv_connector_loops,
    gv_node_component,
    html_line_breaks,
    remove_links,
    set_dot_basics,
)
from wireviz.wv_helper import (
    flatten2d,
    is_arrow,
    open_file_read,
    open_file_write,
    tuplelist2tsv,
)
from wireviz.wv_html import generate_html_output


@dataclass
class Harness:
    metadata: Metadata
    options: Options
    tweak: Tweak

    def __post_init__(self):
        self.connectors = {}
        self.cables = {}
        self.mates = []
        self._bom = []  # Internal Cache for generated bom
        self.additional_bom_items = []

    def add_connector(self, name: str, *args, **kwargs) -> None:
        self.connectors[name] = Connector(name, *args, **kwargs)

    def add_cable(self, name: str, *args, **kwargs) -> None:
        self.cables[name] = Cable(name, *args, **kwargs)

    def add_mate_pin(self, from_name, from_pin, to_name, to_pin, arrow_type) -> None:
        self.mates.append(MatePin(from_name, from_pin, to_name, to_pin, arrow_type))
        self.connectors[from_name].activate_pin(from_pin, Side.RIGHT)
        self.connectors[to_name].activate_pin(to_pin, Side.LEFT)

    def add_mate_component(self, from_name, to_name, arrow_type) -> None:
        self.mates.append(MateComponent(from_name, to_name, arrow_type))

    def add_bom_item(self, item: dict) -> None:
        self.additional_bom_items.append(item)

    def connect(
        self,
        from_name: str,
        from_pin: (int, str),
        via_name: str,
        via_wire: (int, str),
        to_name: str,
        to_pin: (int, str),
    ) -> None:
        # check from and to connectors
        for (name, pin) in zip([from_name, to_name], [from_pin, to_pin]):
            if name is not None and name in self.connectors:
                connector = self.connectors[name]
                # check if provided name is ambiguous
                if pin in connector.pins and pin in connector.pinlabels:
                    if connector.pins.index(pin) != connector.pinlabels.index(pin):
                        raise Exception(
                            f"{name}:{pin} is defined both in pinlabels and pins, for different pins."
                        )
                    # TODO: Maybe issue a warning if present in both lists but referencing the same pin?
                if pin in connector.pinlabels:
                    if connector.pinlabels.count(pin) > 1:
                        raise Exception(f"{name}:{pin} is defined more than once.")
                    index = connector.pinlabels.index(pin)
                    pin = connector.pins[index]  # map pin name to pin number
                    if name == from_name:
                        from_pin = pin
                    if name == to_name:
                        to_pin = pin
                if not pin in connector.pins:
                    raise Exception(f"{name}:{pin} not found.")

        # check via cable
        if via_name in self.cables:
            cable = self.cables[via_name]
            # check if provided name is ambiguous
            if via_wire in cable.colors and via_wire in cable.wirelabels:
                if cable.colors.index(via_wire) != cable.wirelabels.index(via_wire):
                    raise Exception(
                        f"{via_name}:{via_wire} is defined both in colors and wirelabels, for different wires."
                    )
                # TODO: Maybe issue a warning if present in both lists but referencing the same wire?
            if via_wire in cable.colors:
                if cable.colors.count(via_wire) > 1:
                    raise Exception(
                        f"{via_name}:{via_wire} is used for more than one wire."
                    )
                # list index starts at 0, wire IDs start at 1
                via_wire = cable.colors.index(via_wire) + 1
            elif via_wire in cable.wirelabels:
                if cable.wirelabels.count(via_wire) > 1:
                    raise Exception(
                        f"{via_name}:{via_wire} is used for more than one wire."
                    )
                via_wire = (
                    cable.wirelabels.index(via_wire) + 1
                )  # list index starts at 0, wire IDs start at 1

        # perform the actual connection
        self.cables[via_name].connect(from_name, from_pin, via_wire, to_name, to_pin)
        if from_name in self.connectors:
            self.connectors[from_name].activate_pin(from_pin, Side.RIGHT)
        if to_name in self.connectors:
            self.connectors[to_name].activate_pin(to_pin, Side.LEFT)

    def create_graph(self) -> Graph:
        dot = Graph()
        set_dot_basics(dot, self.options)

        for connector in self.connectors.values():
            # generate connector node
            gv_html = gv_node_component(connector, self.options)
            dot.node(
                connector.name,
                label=f"<\n{gv_html}\n>",
                shape="box",
                style="filled",
            )
            # generate edges for connector loops
            if len(connector.loops) > 0:
                dot.attr("edge", color="#000000:#ffffff:#000000")
                loops = gv_connector_loops(connector)
                for head, tail in loops:
                    dot.edge(head, tail)

        # determine if there are double- or triple-colored wires in the harness;
        # if so, pad single-color wires to make all wires of equal thickness
        pad = any(
            len(colorstr) > 2
            for cable in self.cables.values()
            for colorstr in cable.colors
        )

        self.options._pad = pad

        for cable in self.cables.values():
            # generate cable node
            gv_html = gv_node_component(cable, self.options)
            # TODO: PN info for bundles (per wire)
            # shield
            #
            dot.node(
                cable.name,
                label=f"<\n{gv_html}\n>",
                shape="box",
                # style=style,
                # fillcolor=translate_color(bgcolor, "HEX"),
            )
            continue

            # TODO: connection edges

            html = []

            wirehtml = []
            # conductor table
            wirehtml.append('<table border="0" cellspacing="0" cellborder="0">')
            wirehtml.append("   <tr><td>&nbsp;</td></tr>")

            for i, (connection_color, wirelabel) in enumerate(
                zip_longest(cable.colors, cable.wirelabels), 1
            ):
                wirehtml.append("   <tr>")
                wirehtml.append(f"    <td><!-- {i}_in --></td>")
                wirehtml.append(f"    <td>")

                wireinfo = []
                if cable.show_wirenumbers:
                    wireinfo.append(str(i))
                colorstr = wv_colors.translate_color(
                    connection_color, self.options.color_mode
                )
                if colorstr:
                    wireinfo.append(colorstr)
                if cable.wirelabels:
                    wireinfo.append(wirelabel if wirelabel is not None else "")
                wirehtml.append(f'     {":".join(wireinfo)}')

                wirehtml.append(f"    </td>")
                wirehtml.append(f"    <td><!-- {i}_out --></td>")
                wirehtml.append("   </tr>")

                # fmt: off
                bgcolors = ['#000000'] + get_color_hex(connection_color, pad=pad) + ['#000000']
                wirehtml.append(f"   <tr>")
                wirehtml.append(f'    <td colspan="3" border="0" cellspacing="0" cellpadding="0" port="w{i}" height="{(2 * len(bgcolors))}">')
                wirehtml.append('     <table cellspacing="0" cellborder="0" border="0">')
                for j, bgcolor in enumerate(bgcolors[::-1]):  # Reverse to match the curved wires when more than 2 colors
                    wirehtml.append(f'      <tr><td colspan="3" cellpadding="0" height="2" bgcolor="{bgcolor if bgcolor != "" else wv_colors.default_color}" border="0"></td></tr>')
                wirehtml.append("     </table>")
                wirehtml.append("    </td>")
                wirehtml.append("   </tr>")
                # fmt: on

                # for bundles, individual wires can have part information
                if cable.category == "bundle":
                    # create a list of wire parameters
                    wireidentification = []
                    if isinstance(cable.pn, list):
                        wireidentification.append(
                            pn_info_string(
                                HEADER_PN, None, remove_links(cable.pn[i - 1])
                            )
                        )
                    manufacturer_info = pn_info_string(
                        HEADER_MPN,
                        cable.manufacturer[i - 1]
                        if isinstance(cable.manufacturer, list)
                        else None,
                        cable.mpn[i - 1] if isinstance(cable.mpn, list) else None,
                    )
                    supplier_info = pn_info_string(
                        HEADER_SPN,
                        cable.supplier[i - 1]
                        if isinstance(cable.supplier, list)
                        else None,
                        cable.spn[i - 1] if isinstance(cable.spn, list) else None,
                    )
                    if manufacturer_info:
                        wireidentification.append(html_line_breaks(manufacturer_info))
                    if supplier_info:
                        wireidentification.append(html_line_breaks(supplier_info))
                    # print parameters into a table row under the wire
                    if len(wireidentification) > 0:
                        # fmt: off
                        wirehtml.append('   <tr><td colspan="3">')
                        wirehtml.append('    <table border="0" cellspacing="0" cellborder="0"><tr>')
                        for attrib in wireidentification:
                            wirehtml.append(f"     <td>{attrib}</td>")
                        wirehtml.append("    </tr></table>")
                        wirehtml.append("   </td></tr>")
                        # fmt: on

            if cable.shield:
                wirehtml.append("   <tr><td>&nbsp;</td></tr>")  # spacer
                wirehtml.append("   <tr>")
                wirehtml.append("    <td><!-- s_in --></td>")
                wirehtml.append("    <td>Shield</td>")
                wirehtml.append("    <td><!-- s_out --></td>")
                wirehtml.append("   </tr>")
                if isinstance(cable.shield, str):
                    # shield is shown with specified color and black borders
                    shield_color_hex = wv_colors.get_color_hex(cable.shield)[0]
                    attributes = (
                        f'height="6" bgcolor="{shield_color_hex}" border="2" sides="tb"'
                    )
                else:
                    # shield is shown as a thin black wire
                    attributes = f'height="2" bgcolor="#000000" border="0"'
                # fmt: off
                wirehtml.append(f'   <tr><td colspan="3" cellpadding="0" {attributes} port="ws"></td></tr>')
                # fmt: on

            wirehtml.append("   <tr><td>&nbsp;</td></tr>")
            wirehtml.append("  </table>")

            html = [
                row.replace("<!-- wire table -->", "\n".join(wirehtml)) for row in html
            ]

            # connections
            for connection in cable.connections:
                if isinstance(connection.via_port, int):
                    # check if it's an actual wire and not a shield
                    dot.attr(
                        "edge",
                        color=":".join(
                            ["#000000"]
                            + wv_colors.get_color_hex(
                                cable.colors[connection.via_port - 1], pad=pad
                            )
                            + ["#000000"]
                        ),
                    )
                else:  # it's a shield connection
                    # shield is shown with specified color and black borders, or as a thin black wire otherwise
                    dot.attr(
                        "edge",
                        color=":".join(["#000000", shield_color_hex, "#000000"])
                        if isinstance(cable.shield, str)
                        else "#000000",
                    )
                if connection.from_pin is not None:  # connect to left
                    from_connector = self.connectors[connection.from_name]
                    from_pin_index = from_connector.pins.index(connection.from_pin)
                    from_port_str = (
                        f":p{from_pin_index+1}r"
                        if from_connector.style != "simple"
                        else ""
                    )
                    code_left_1 = f"{connection.from_name}{from_port_str}:e"
                    code_left_2 = f"{cable.name}:w{connection.via_port}:w"
                    dot.edge(code_left_1, code_left_2)
                    if from_connector.show_name:
                        from_info = [
                            str(connection.from_name),
                            str(connection.from_pin),
                        ]
                        if from_connector.pinlabels:
                            pinlabel = from_connector.pinlabels[from_pin_index]
                            if pinlabel != "":
                                from_info.append(pinlabel)
                        from_string = ":".join(from_info)
                    else:
                        from_string = ""
                    html = [
                        row.replace(f"<!-- {connection.via_port}_in -->", from_string)
                        for row in html
                    ]
                if connection.to_pin is not None:  # connect to right
                    to_connector = self.connectors[connection.to_name]
                    to_pin_index = to_connector.pins.index(connection.to_pin)
                    to_port_str = (
                        f":p{to_pin_index+1}l" if to_connector.style != "simple" else ""
                    )
                    code_right_1 = f"{cable.name}:w{connection.via_port}:e"
                    code_right_2 = f"{connection.to_name}{to_port_str}:w"
                    dot.edge(code_right_1, code_right_2)
                    if to_connector.show_name:
                        to_info = [str(connection.to_name), str(connection.to_pin)]
                        if to_connector.pinlabels:
                            pinlabel = to_connector.pinlabels[to_pin_index]
                            if pinlabel != "":
                                to_info.append(pinlabel)
                        to_string = ":".join(to_info)
                    else:
                        to_string = ""
                    html = [
                        row.replace(f"<!-- {connection.via_port}_out -->", to_string)
                        for row in html
                    ]

            style, bgcolor = (
                ("filled,dashed", self.options.bgcolor_bundle)
                if cable.category == "bundle"
                else ("filled", self.options.bgcolor_cable)
            )
            html = "\n".join(html)
            dot.node(
                cable.name,
                label=f"<\n{html}\n>",
                shape="box",
                style=style,
                fillcolor=translate_color(bgcolor, "HEX"),
            )

        apply_dot_tweaks(dot, self.tweak)

        for mate in self.mates:
            if mate.shape[0] == "<" and mate.shape[-1] == ">":
                dir = "both"
            elif mate.shape[0] == "<":
                dir = "back"
            elif mate.shape[-1] == ">":
                dir = "forward"
            else:
                dir = "none"

            if isinstance(mate, MatePin):
                color = "#000000"
            elif isinstance(mate, MateComponent):
                color = "#000000:#000000"
            else:
                raise Exception(f"{mate} is an unknown mate")

            from_connector = self.connectors[mate.from_name]
            if (
                isinstance(mate, MatePin)
                and self.connectors[mate.from_name].style != "simple"
            ):
                from_pin_index = from_connector.pins.index(mate.from_pin)
                from_port_str = f":p{from_pin_index+1}r"
            else:  # MateComponent or style == 'simple'
                from_port_str = ""
            if (
                isinstance(mate, MatePin)
                and self.connectors[mate.to_name].style != "simple"
            ):
                to_pin_index = to_connector.pins.index(mate.to_pin)
                to_port_str = (
                    f":p{to_pin_index+1}l"
                    if isinstance(mate, MatePin)
                    and self.connectors[mate.to_name].style != "simple"
                    else ""
                )
            else:  # MateComponent or style == 'simple'
                to_port_str = ""
            code_from = f"{mate.from_name}{from_port_str}:e"
            to_connector = self.connectors[mate.to_name]
            code_to = f"{mate.to_name}{to_port_str}:w"

            dot.attr("edge", color=color, style="dashed", dir=dir)
            dot.edge(code_from, code_to)

        return dot

    # cache for the GraphViz Graph object
    # do not access directly, use self.graph instead
    _graph = None

    @property
    def graph(self):
        if not self._graph:  # no cached graph exists, generate one
            self._graph = self.create_graph()
        return self._graph  # return cached graph

    @property
    def png(self):
        from io import BytesIO

        graph = self.graph
        data = BytesIO()
        data.write(graph.pipe(format="png"))
        data.seek(0)
        return data.read()

    @property
    def svg(self):
        graph = self.graph
        return embed_svg_images(graph.pipe(format="svg").decode("utf-8"), Path.cwd())

    def output(
        self,
        filename: (str, Path),
        view: bool = False,
        cleanup: bool = True,
        fmt: tuple = ("html", "png", "svg", "tsv"),
    ) -> None:
        # graphical output
        graph = self.graph
        svg_already_exists = Path(
            f"{filename}.svg"
        ).exists()  # if SVG already exists, do not delete later
        # graphical output
        for f in fmt:
            if f in ("png", "svg", "html"):
                if f == "html":  # if HTML format is specified,
                    f = "svg"  # generate SVG for embedding into HTML
                # SVG file will be renamed/deleted later
                _filename = f"{filename}.tmp" if f == "svg" else filename
                # TODO: prevent rendering SVG twice when both SVG and HTML are specified
                graph.format = f
                graph.render(filename=_filename, view=view, cleanup=cleanup)
        # embed images into SVG output
        if "svg" in fmt or "html" in fmt:
            embed_svg_images_file(f"{filename}.tmp.svg")
        # GraphViz output
        if "gv" in fmt:
            graph.save(filename=f"{filename}.gv")
        # BOM output
        bomlist = bom_list(self.bom())
        if "tsv" in fmt:
            open_file_write(f"{filename}.bom.tsv").write(tuplelist2tsv(bomlist))
        if "csv" in fmt:
            # TODO: implement CSV output (preferrably using CSV library)
            print("CSV output is not yet supported")
        # HTML output
        if "html" in fmt:
            generate_html_output(filename, bomlist, self.metadata, self.options)
        # PDF output
        if "pdf" in fmt:
            # TODO: implement PDF output
            print("PDF output is not yet supported")
        # delete SVG if not needed
        if "html" in fmt and not "svg" in fmt:
            # SVG file was just needed to generate HTML
            Path(f"{filename}.tmp.svg").unlink()
        elif "svg" in fmt:
            Path(f"{filename}.tmp.svg").replace(f"{filename}.svg")

    def bom(self):
        if not self._bom:
            self._bom = generate_bom(self)
        return self._bom
