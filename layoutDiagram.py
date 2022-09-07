'''
 read in a wokwi diagram.json file and output a new one with cells placed in a 'better' order to reduce overlapping
 Uses networkx and dot to find the placements.
 Ranking is not working correctly so adjusts the inputs and outputs manually after graph layout

TODO: Reduce the dependancies to eliminate pygraphviz as it is a troublesome install on windows
TODO: Allow parts to be fixed in position, lower the weights of those edges
TODO: incorporate spacing info, will be much more helpful for wires

Info on wokwi layout and part sizes
top left positions are in SVG pixels 
96 pixels = 1 inch
mm to pixels conversion 96/25.4

small parts  data 
part        Size mm
wokwi-gnd              5.40 x  9.66
wokwi-vcc              5.08 x  7.55
wokwi-gate-buffer     25.40 x 10.00
wokwi-gate-not        25.40 x 10.00
wokwi-gate-and-2      25.40 x 10.00
wokwi-gate-nand-2     25.40 x 10.00
wokwi-gate-or-2       25.40 x 10.00
wokwi-gate-xor-2      25.40 x 10.00
wokwi-mux-2           25.40 x 12.70
wokwi-flip-flop-d     25.40 x 10.00
wokwi-flip-flop-sr    25.40 x 10.00
wokwi-flip-flop-dsr   25.40 x 16.00
wokwi-clock-generator 17.78 x 10.00

Installation

sudo apt-get update
sudo apt-get install graphviz graphviz-dev
pip3 install pygraphviz
pip3 install networkx
pip3 install coloredlogs

Window install of pygraphviz is not easy

https://pygraphviz.github.io/documentation/stable/install.html

python -m pip install --global-option=build_ext `
              --global-option="-IC:\Program Files\Graphviz\include" `
              --global-option="-LC:\Program Files\Graphviz\lib" `
              pygraphviz

Make sure C:\Program Files\Graphviz\bin or directory where graphviz is installed is added to path variable
restart to ensure new path variable is used 

 Copyright (c) burkew, 2022
 wokwi-tools is licensed under the GNU General Public License v3.0
 Copyright and license notices must be preserved. Contributors provide an express grant of patent rights.

'''

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import json
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import coloredlogs, logging

# for viewing
import matplotlib.pyplot as plt 


def create_graph(design):
    # create graph
    G = nx.DiGraph()

    # add nodes
    minNodes = []
    maxNodes = []
    for part in design["parts"]:
        myrank = None
        if "input" in part["id"] and "analyzer" not in part["id"]:
            minNodes.append(part["id"])
        elif "output" in part["id"] and "analyzer" not in part["id"]:
            maxNodes.append(part["id"])

        G.add_node(part["id"],rank='same')
    
    # So far have had no luck with ranking on nodes
    # following code and if elif above do nothing on windows 
    # tbd if a newer graphviz lib will be better or if results will be different another platform
    S = G.subgraph(minNodes)
    nx.set_node_attributes(S,'min','rank')
    # s.attr(rank='min')
        # for n in minNodes:
        #     s.node(n)

    S = G.subgraph(maxNodes)
    nx.set_node_attributes(S,'max','rank')
    # s.attr(rank='max')
        # for n in maxNodes:
        #     s.node(n)
    
    for connection in design["connections"]:
        if 'analyzer' in connection[0] or 'analyzer' in connection[1]: 
            log.debug("Connections between inputs ")
            log.debug(connection[0], connection[1])
            continue
        G.add_edge(connection[0].split(":")[0], connection[1].split(":")[0], weight=1)

    # add edges to the inputs and outputs to make them ordered
    
    #G = nx.DiGraph()
    #for part in design["parts"]:
    #    G.add_node(part["id"],rank='same')

    def orderNodes(nodelist):
        prev = None
        for n in sorted(nodelist):
            if prev:
                G.add_edge(prev, n,weight=10)
            prev = n
    orderNodes(minNodes)
    orderNodes(maxNodes)
    return G

def update_design(design, pos):
    # adjust graph so that inputs are left most 
    def dist(x, y):
        d = 0
        if x > y:
            d = x - y
        else:
            d = y - x
        return d

    vertSpacing = 50
    maxX = 0
    minX = 0

    if True:
        for key in sorted(pos):
            # pick up the maxX while we are looping 
            if pos[key][0] > maxX:
                maxX = pos[key][0]
            if 'input' in key and 'analyzer' not in key:
                vert = pos[key][1]
                log.debug("Placing key ", key, "at ", vert)
                # check if we will stomp on any other y spacing
                for key2 in sorted(pos):
                    if key2 == key:
                        continue
                    if 'input' in key2:
                        vert2 = pos[key2][1]
                        if dist(vert, vert2) < vertSpacing:
                            # keep our spacing and bump the next guy
                            pos[key2] = (pos[key2][0],vert+vertSpacing)
                            
                            log.debug("moving key2 ", key2, "from ", vert2, " to ", vert+vertSpacing)
                pos[key] = (minX, vert)


        for key in sorted(pos):
            if 'output' in key and 'analyzer' not in key:
                vert = pos[key][1]
                log.debug("Placing key ", key, "at ", vert)
                # check if we will stomp on any other y spacing
                for key2 in sorted(pos):
                    if key2 == key:
                        continue
                    if 'output' in key2:
                        vert2 = pos[key2][1]
                        if dist(vert, vert2) < vertSpacing:
                            # keep our spacing and bump the next guy
                            pos[key2] = (pos[key2][0],vert+vertSpacing)
                            
                            log.debug("moving key2 ", key2, "from ", vert2, " to ", vert + vertSpacing)
                pos[key] = (maxX, vert)

    # update the parts positions 
    for part in design['parts']: 
        if part['id'] in pos:
            newpos = pos[part['id']]
            part['top'] = newpos[1]
            part['left'] = newpos[0]

def write_design(filename, design):
    with open(ofname, 'w', encoding='utf-8') as f:
        json.dump(design, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    SHOWPLOT = True

    parser = ArgumentParser(description='%(prog)s is a lookup table generator tool for wokwi',
                            formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument('-v', '--verbose',
                        action='count',
                        help='log level (-v: INFO, -vv: DEBUG)',
                        default=0)

    parser.add_argument('-f', '--file',
                        dest='in_file',
                        help='path to input wokwi file',
                        default=None)

    parser.add_argument('-o', '--outfile',
                        dest='out_file',
                        help='path to generated wokwi file',
                        default=None)

    args = parser.parse_args()

    # Create and configure logger object
    log = logging.getLogger(__name__)
    #coloredlogs.install(level='DEBUG', fmt='%(asctime)s [%(levelname)8s] %(message)s')

    if args.verbose > 0:
        log_level='INFO'
        if args.verbose > 1:
            log_level='DEBUG'
    else:
        log_level='WARNING'

    coloredlogs.install(level=log_level, fmt='[%(levelname)8s] %(message)s')

    # default design
    fname = "./examples/7segexample.json"
    ofname = "./examples/7segexample_layout.json"

    if args.in_file:
        fname = args.in_file
    
    if args.out_file:
        ofname = args.out_file

    try: 
        f = open(fname)
        design = json.load(f)
    except FileNotFoundError:
        log.error(f"Input file '{fname}' cannot be found. Use flag '-h' to get usage.")
        exit(1)

    graph = create_graph(design)
    pos = graphviz_layout(graph, prog='dot', args='-Grankdir="LR"')

    update_design(design, pos)

    write_design(ofname, design)

    if SHOWPLOT:
        labels = {v["id"]: v["id"] for v in design["parts"]}
        nx.draw(graph, with_labels=True, pos=pos, labels=labels)
        plt.show()
    # debug stop to prevent vscode from quiting early as it will just close the graphic 
    pause = 0
    payse = 1
    a = input()