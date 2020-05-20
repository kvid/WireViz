# WireViz

## Problem

There is no easy way to document wires in projects.

## Solution

Create a GraphViz-based markup language and parser to quickly and easily document cables, wires and pinouts.

## Requirements

* Must be text based for easy version control
* Must be easy to use, yet flexible and extendable

## Features

* Auto-generate standard wire color schemes and allow custom ones
  * DIN 47100 (WT/BN/GN/YE/GY/PK/BU/RD/BK/VT/...)
  * IEC ???   (BN/RD/OR/YE/GN/BU/VT/GY/WT/BK/...)
* Allow more than one connector per side
* Include image with pinout of connector, if known

## Example

WireViz input file:

    // define connectors

    X1 [type="D-Sub DE-9",
        subtype="female",
        num_pins=9,
        pin_labels="DCD|RX|TX|DTR|GND|DSR|RTS|CTS|RI",
        position=L
       ]

    X2 [type="Molex KK 254 6-pin",
        subtype="female",
        num_pins=6,
        pin_labels="GND|RX|TX|NC|OUT|IN",
        position=R
       ]

    // define wire

    W1 [type="3x 0,25 mm² shielded",
        length="0.2m",
        num_wires=3,
        colors="din47100",
        shield=true
       ]

    // define connections

    X1:5 -> W1:1 -> X2:1  // GND
    X1:2 -> W1:2 -> X2:3  // TX-RX
    X1:3 -> W1:3 -> X2:2  // RX-TX
    X1:5 -> W1:S          // shield
    X2:5 -> X2:6          // loop

Output file:

![Sample output diagram](idea/example1.png)

GraphViz code generated by parser:

    digraph G {
        graph [rankdir = LR, ranksep=2, fontname = "arial"];
        edge [arrowhead=none, fontname = "arial"];
        node [shape=record, style=rounded, fontname = "arial"];

        X1[label="X1 | D-Sub DE-9 | female | {{DCD|RX|TX|DTR|GND|DSR|RTS|CTS|RI} | {<p1>1|<p2>2|<p3>3|<p4>4|<p5>5|<p6>6|<p7>7|<p8>8|<p9>9}} "];
        X2[label="X2 | Molex KK 254 6-pin | female | {{<p1>1|<p2>2|<p3>3|<p4>4|<p5>5|<p6>6} | {GND|RX|TX|NC|OUT|IN}}"];

        W1[label="W1 | 3x 0,25 mm² shielded | 0.2 m | {{<w1i>1|<w2i>2|<w3i>3|<wsi>}|{WT|BN|GN|Shield}|{<w1o>1|<w2o>2|<w3o>3|<wsi>}}}"];

        X1:p5 -> W1:w1i; W1:w1o -> X2:p1;
        X1:p2 -> W1:w2i; W1:w2o -> X2:p3;
        X1:p3 -> W1:w3i; W1:w3o -> X2:p2;
        X1:p5 -> W1:wsi;
        X2:p5:w -> X2:p6:w
    }
