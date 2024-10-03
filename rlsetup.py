import sys; args = sys.argv[1:]

STRDIGITs = {*'1234567890'}
DIRECTIONS = {*'NSEWnsew'}

def grfParse(args):
    # size is the first argument
    size = int(args[0])
    args = args[1:]

    # if the second element is a number, it specifies the width
    width = 0
    if args and all(ch in STRDIGITs for ch in args[0]):
        width = int(args[0])
        args = args[1:]

    else:
        for w in range(int(size**0.5), size+1):
            if (size//w <= w) and ((size/w)%1 == 0):
                width = w; break
            
    # default reward is 12
    impliedReward = 12

    # default graph - create the gridworld
    graph = {}
    graph['graph'] = {key:{idx for idx in [key-width, key-1, key+1, key+width] if 0<=idx<size and (key//width == idx//width or key%width == idx%width)} for key in range(size)}
    graph['default'] = {key:{idx for idx in [key-width, key-1, key+1, key+width] if 0<=idx<size and (key//width == idx//width or key%width == idx%width)} for key in range(size)}
    graph['size'] = size
    graph['rwd'] = impliedReward
    graph['width'] = width
    graph['cellrwds'] = {}

    directive = 'G1'    
        
    # The remaining directives may occur in any order and are processed in a left-to-right order:
    for arg in args:
        if arg[0] in {'R', 'r'}:
            arg = arg[1:]

            # R:#  Sets the implied reward to the number indicated
            if arg[0] == ':':
                arg = arg[1:]
                graph['rwd'] = int(arg)
            
            # R#   Sets the reward at the cell indicated by number equal to the implied reward
            elif ':' not in arg:
                cellIdx = int(arg)
                graph['cellrwds'][cellIdx] = graph['rwd']

            # R#:#  Sets the reward for the cell at the first # to be equal to the 2nd #
            else:
                cellIdx, cellReward = arg.split(':')
                graph['cellrwds'][int(cellIdx)] = int(cellReward)
        
        elif arg[0] in {'B', 'b'}:
            arg = arg[1:]

            # Toggles the links going in and out of the cell at the indicated position
            if all(direction not in arg for direction in DIRECTIONS):
                cellIdx = int(arg)

                for defaultNbr in graph['default'][cellIdx]:
                    if defaultNbr in graph['graph'][cellIdx]:
                        graph['graph'][cellIdx] -= {defaultNbr}

                    else:
                        graph['graph'][cellIdx].add(defaultNbr)

                    if cellIdx in graph['graph'][defaultNbr]:
                        graph['graph'][defaultNbr] -= {cellIdx}

                    else:
                        graph['graph'][defaultNbr].add(cellIdx)

            # B#[NSEW]+  Toggles the link (and its reciprocal) in the specified direction(s) from the cell at the indicated position.
            else:
                cellIdx = ''
                while arg[0] in STRDIGITs:
                    cellIdx += arg[0]; arg = arg[1:]
                cellIdx = int(cellIdx)

                specifiedDirections = {*arg}
                for d in specifiedDirections:
                    modifier = [[[-width, width][d in {'S', 's'}], -1][d in {'W', 'w'}], 1][d in {'E', 'e'}]
                    
                    endCell = cellIdx + modifier

                    if endCell%width != cellIdx%width and endCell//width != cellIdx//width:
                        endCell = -1
                    
                    if endCell < size and endCell > -1:
                        if endCell in graph['graph'][cellIdx]:
                            graph['graph'][cellIdx] -= {endCell}

                        else:
                            graph['graph'][cellIdx].add(endCell)

                        if cellIdx in graph['graph'][endCell]:
                            graph['graph'][endCell] -= {cellIdx}

                        else:
                            graph['graph'][endCell].add(cellIdx)

        else:
            directive = arg

    return graph, directive

def grfStrEdges(graph):
    grfStr = ''
    for key in graph['graph']:
        nbrs = graph['graph'][key]

        if nbrs == '*': grfStr += '*'; continue
        if not nbrs: grfStr += '.'; continue

        directions = set()
        for v2 in nbrs:
            d = directionFrom(graph, key, v2)
            if d != '-': directions.add(d)

        if not directions: grfStr += '.'; continue

        if directions == {*'UR'}: grfStr += 'V'
        elif directions == {*'URD'}: grfStr += 'W'
        elif directions == {*'RD'}: grfStr += 'S'
        elif directions == {*'RDL'}: grfStr += 'T'
        elif directions == {*'DL'}: grfStr += 'E'
        elif directions == {*'DLU'}: grfStr += 'F'
        elif directions == {*'LU'}: grfStr += 'M'
        elif directions == {*'LUR'}: grfStr += 'N'
        elif directions == {*'UD'}: grfStr += '|'
        elif directions == {*'LR'}: grfStr += '-'
        elif directions == {*'UDLR'}: grfStr += '+'
        else: grfStr += directions.pop()

    return grfStr

def directionFrom(graph, v1, v2):
    if v2 == v1 + 1 and v2//graph['width'] == v1//graph['width']: return 'R'
    if v2 == v1 - 1 and v2//graph['width'] == v1//graph['width']: return 'L'
    if v2 == v1 + graph['width']: return 'D'
    if v2 == v1 - graph['width']: return 'U'
    return '-'

def rlsetup(graph, directive):
    rlGraph = {}
    rlGraph['graph'] = {n:set() for n in range(graph['size'])}
    rlGraph['size'] = graph['size']
    rlGraph['width'] = graph['width']
    rewardLocations = [(idx, graph['cellrwds'][idx]) for idx in graph['cellrwds']]
    rlGraph = bfs(graph, rlGraph, rewardLocations, directive)
    grfStr = grfStrEdges(rlGraph)
    print(grfStr)

def bfs(graph, rlGraph, rewardLocations, directive):
    # bestGraph: (value, pathToVertex)
    bestGraph = [(-float('inf'), [])] * graph['size']
    for rewardIdx, rwd in rewardLocations:
        bestGraph[rewardIdx] = '*'

    # bfs from each reward location
    for rewardIdx, rwd in rewardLocations:
        # seen: (idx, first_step)
        seen = {(rewardIdx, -1)}
        queue = [(rewardIdx, [rewardIdx])]

        i = 0
        while i < len(queue):
            node = queue[i]; i += 1
            currentVertex, pathToVertex = node

            print(bestGraph[6])

            nbrs = {idx for idx in graph['graph'] if currentVertex in graph['graph'][idx]}

            for nbr in nbrs:
                if len(pathToVertex) > 1 and (nbr, pathToVertex[1]) in seen: continue

                pathToNbr = pathToVertex + [nbr]
                newLen = len(pathToNbr)

                if bestGraph[nbr] == '*': continue

                if directive == 'G1': value = rwd/(newLen-1)
                else: value, dst = rwd, newLen-1

                if value > bestGraph[nbr][0]:
                    if directive == 'G1': bestGraph[nbr] = (value, [pathToNbr])
                    else: bestGraph[nbr] = (value, dst, [pathToNbr])
                elif value == bestGraph[nbr][0]:
                    if directive == 'G1': bestGraph[nbr] = (value, bestGraph[nbr][1] + [pathToNbr])
                    else:
                        if bestGraph[nbr][1] > dst: bestGraph[nbr] = (value, dst, [pathToNbr])
                        elif bestGraph[nbr][1] == dst: bestGraph[nbr] = (value, dst, bestGraph[nbr][2] + [pathToNbr])
                        else: continue
                else:
                    continue

                seen.add((nbr, pathToNbr[-2])); queue.append((nbr, pathToNbr))

    print(bestGraph[25])

    for idx, obj in enumerate(bestGraph):
        if obj == '*': rlGraph['graph'][idx] = '*'; continue
        if len(obj) == 2:
            value, paths = obj
            paths = [path[-2] for path in paths]
            rlGraph['graph'][idx] = {*paths}
        else:
            value, dst, paths = obj
            paths = [path[-2] for path in paths]
            rlGraph['graph'][idx] = {*paths}

    return rlGraph

def main():
    grf, directive = grfParse(args)
    rlsetup(grf, directive)

if __name__ == '__main__': main()
# Aaryan Sumesh, Class of 2025, Period 2