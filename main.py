import sys; args = sys.argv[1:]
import re

def grfParse(lstArgs):
    # returns graph constructed from lstArgs
    graph = {}
    graphType = ''
    size = 0
    width = 0
    rwd = 0

    for arg in lstArgs:
        if arg[0] == 'G':
            spec = arg[1:]

            # graphType
            if spec[0] == 'N':
                graphType = 'N'
                spec = spec[1:]
            elif spec[0] == 'G':
                graphType = 'G'
                spec = spec[1:]
            else:
                graphType = 'G'
            
            # size
            size = ''
            while spec and spec[0] in [str(x) for x in range(10)]:
                size += spec[0]
                spec = spec[1:]
            
            size = int(size)
            if not size: exit()

            # width
            if spec and spec[0] == 'W':
                spec = spec[1:]
                width = ''
                while spec and spec[0] in [str(x) for x in range(10)]:
                    width += spec[0]
                    spec = spec[1:]
                width = int(width)
            else:
                width = 1
                for w in range(int(size**0.5), size+1):
                    if size//w <= w and (size/w)%1 == 0:
                        width = w; break
            
            # rwd
            if spec and spec[0] == 'R':
                spec = spec[1:]
                rwd = ''
                while spec and spec[0] in [str(x) for x in range(10)]:
                    rwd += spec[0]
                    spec = spec[1:]
                
            else:
                rwd = 12

            graph['type'] = graphType
            graph['size'] = size
            graph['width'] = width
            graph['rwd'] = rwd
            graph['vprops'] = {}
            graph['eprops'] = {}

            if width != 0 and graphType == 'G':
                # default edges
                graph['graph'] = {key:{idx for idx in [key-width, key-1, key+1, key+width] if 0<=idx<size and (key//width == idx//width or key%width == idx%width)} for key in range(size)}
            else:
                graph['graph'] = {key:set() for key in range(size)}

            graph['default'] = {key:{x for x in graph['graph'][key]} for key in graph['graph']}
            
        elif arg[0] == 'V':
            spec = arg[1:]

            ms, me = re.search('^([-,:]|\d)+', spec).span()
            
            vslcs = spec[ms:me]
            spec = spec[me:]

            vslcs = vslice(vslcs, graph['size'])

            g = graph['graph']
            d = graph['default']

            if 'RB' in spec:
                loc = spec.find('RB')
                spec = spec[:loc] + 'BR' + spec[loc+2:]

            if 'B' in spec:
                V = {key for key in d}
                W = {*vslcs}
                X = V - W

                S = set()
                for w in W:
                    for x in X:
                        if (w in g[x] or w in d[x]):
                            S.add((x, w))
                        if (x in g[w] or x in d[w]):
                            S.add((w, x))

                # toggle elements in S
                for edgeStart, edgeEnd in S:
                    if edgeEnd in g[edgeStart]:
                        # remove edge
                        g[edgeStart] -= {edgeEnd}
                    else:
                        # add edge
                        g[edgeStart].add(edgeEnd)
                
                loc = spec.find('B')
                spec = spec[:loc] + spec[loc+1:]

            reward = -1
            
            if spec and spec[0] == 'R':
                spec = spec[1:]
                
                z = spec.find('B')
                if z != -1:
                    spec = spec[:z] + spec[z+1:]
                    print(spec)
                reward = graph['rwd'] if not spec else int(spec)

                for v in {*vslcs}:
                    graph['vprops'][v] = {'rwd':reward}

        elif arg[0] == 'E':
            spec = arg[1:]

            if re.search('^[!+*~@]?([-,:]|\d)+[=~]([-,:]|\d)+[R\d+?T]*$', spec):
                # zip between vslcs1 and vslcs2
                mngment = '~'
                if spec[0] in '!+*~@':
                    mngment = spec[0]
                    spec = spec[1:]

                edgeType = '~'
                if '~' in spec:
                    vslcs = spec.split('~')
                else:
                    vslcs = spec.split('=')
                    edgeType = '='
                
                vslices = []
                for vslc in vslcs:
                    z = re.search('^([-,:]|\d)+', vslc).span()
                    v = vslc[z[0]:z[1]]
                    vslices.append(v)

                edgeStarts = vslice(vslices[0], graph['size'])
                edgeEnds = vslice(vslices[1], graph['size'])

                edges = [*zip(edgeStarts, edgeEnds)]
                
                if edgeType == '=':
                    # make bidirectional
                    additionalEdges = []
                    for eS, eE in edges:
                        additionalEdges.append((eE, eS))

                    edges += additionalEdges

                _seen = set()
                seen_add = _seen.add
                edges = [x for x in edges if not (x in _seen or seen_add(x))]

                g = graph['graph']
                d = graph['default']

                reward = -1
                if 'R' in spec:
                    loc = spec.find('R')
                    spec = spec[loc+1:]

                    z = spec.find('B')
                    if z != -1:
                        spec = spec[:z] + spec[z+1:]
                        print(spec)
                    reward = graph['rwd'] if not spec else int(spec)
                
                if mngment == '~':
                    # toggle
                    for edgeStart, edgeEnd in edges:
                        if edgeEnd in g[edgeStart]:
                            # remove edge
                            g[edgeStart] -= {edgeEnd}
                            if (edgeStart, edgeEnd) in graph['eprops']:
                                graph['eprops'][(edgeStart, edgeEnd)] = {}
                        else:
                            # add edge
                            g[edgeStart].add(edgeEnd)
                            if reward!=-1: graph['eprops'][(edgeStart, edgeEnd)] = {'rwd' : reward}

                elif mngment == '!':
                    # only remove extant edges
                    for edgeStart, edgeEnd in edges:
                        if edgeEnd in g[edgeStart]:
                            # remove edge
                            g[edgeStart] -= {edgeEnd}
                            if (edgeStart, edgeEnd) in graph['eprops']: graph['eprops'][(edgeStart, edgeEnd)] = {}

                elif mngment == '+':
                    # add new with properties, skip extant edges
                    for edgeStart, edgeEnd in edges:
                        if edgeEnd not in g[edgeStart]:
                            g[edgeStart].add(edgeEnd)

                            if reward!=-1: graph['eprops'][(edgeStart, edgeEnd)] = {'rwd' : reward}

                elif mngment == '*':
                    # add if missing, apply properties to new and previously extant
                    for edgeStart, edgeEnd in edges:
                        if edgeEnd not in g[edgeStart]:
                            g[edgeStart].add(edgeEnd)
                        
                        if reward!=-1: graph['eprops'][(edgeStart, edgeEnd)] = {'rwd' : reward}

                elif mngment == '@':
                        # apply props to extant edges
                        for edgeStart, edgeEnd in edges:
                            if edgeEnd in g[edgeStart]:
                                # add props
                                if reward!=-1: graph['eprops'][(edgeStart, edgeEnd)] = {'rwd' : reward}
                
            elif re.search('^[!+*~@]?([-,:]|\d)+[NSEW]+[=~][R\d+?T]*$', spec):
                reward = -1
                mngment = '~'
                if spec[0] in [*'!+*~@']:
                    mngment = spec[0]
                    spec = spec[1:]

                vslc = re.search('^([-,:]|\d)+', spec)
                sp = vslc.span()

                vslc = spec[sp[0]:sp[1]]
                vslc = vslice(vslc, graph['size'])

                spec = spec[sp[1]:]

                directions = []
                for x in spec:
                    if x in 'NSEW':
                        directions.append(x)

                spec = spec[len(directions):]
                    
                if spec[0] == '=':
                    edgeType = '='
                    spec = spec[1:]
                elif spec[0] == '~':
                    edgeType = '~'
                    spec = spec[1:]
                else:
                    edgeType = '~'

                for edgeStart in vslc:
                    edgeEnds = []

                    for di in directions:
                        if di == 'N':
                            c = edgeStart-graph['width']
                            if c >= 0 and c < graph['size']:
                                edgeEnds.append(c)
                        elif di == 'E':
                            c = edgeStart + 1
                            if c//graph['width'] == edgeStart//graph['width']:
                                edgeEnds.append(c)
                        elif di == 'S':
                            c = edgeStart+graph['width']
                            if c >= 0 and c < graph['size']:
                                edgeEnds.append(c)
                        elif di == 'W':
                            c = edgeStart - 1
                            if c//graph['width'] == edgeStart//graph['width']:
                                edgeEnds.append(c)

                    edges = [(edgeStart, eE) for eE in edgeEnds]


                    if edgeType == '=':
                        edges += [(y,x) for x,y in edges]

                    _seen = set()
                    seen_add = _seen.add
                    edges = [x for x in edges if not (x in _seen or seen_add(x))]

                    g = graph['graph']
                    d = graph['default']
                    
                    if 'R' in spec:
                        loc = spec.find('R')
                        spec = spec[loc+1:]

                        z = spec.find('B')
                        if z != -1:
                            spec = spec[:z] + spec[z+1:]
                            print(spec)
                        reward = graph['rwd'] if not spec else int(spec)
                    
                    if mngment == '~':
                        # toggle
                        for edgeStart, edgeEnd in edges:
                            if edgeEnd in g[edgeStart]:
                                # remove edge
                                g[edgeStart] -= {edgeEnd}
                                if (edgeStart, edgeEnd) in graph['eprops']:
                                    graph['eprops'][(edgeStart, edgeEnd)] = {}
                            else:
                                # add edge
                                g[edgeStart].add(edgeEnd)
                                if reward!=-1: graph['eprops'][(edgeStart, edgeEnd)] = {'rwd' : reward}

                    elif mngment == '!':
                        # only remove extant edges
                        for edgeStart, edgeEnd in edges:
                            if edgeEnd in g[edgeStart]:
                                # remove edge
                                g[edgeStart] -= {edgeEnd}
                                if (edgeStart, edgeEnd) in graph['eprops']: graph['eprops'][(edgeStart, edgeEnd)] = {}

                    elif mngment == '+':
                        # add new with properties, skip extant edges
                        for edgeStart, edgeEnd in edges:
                            if edgeEnd not in g[edgeStart]:
                                g[edgeStart].add(edgeEnd)

                                if reward!=-1: graph['eprops'][(edgeStart, edgeEnd)] = {'rwd' : reward}

                    elif mngment == '*':
                        # add if missing, apply properties to new and previously extant
                        for edgeStart, edgeEnd in edges:
                            if edgeEnd not in g[edgeStart]:
                                g[edgeStart].add(edgeEnd)
                            
                            if reward!=-1: graph['eprops'][(edgeStart, edgeEnd)] = {'rwd' : reward}

                    elif mngment == '@':
                            # apply props to extant edges
                            for edgeStart, edgeEnd in edges:
                                if edgeEnd in g[edgeStart]:
                                    # add props
                                    if reward!=-1: graph['eprops'][(edgeStart, edgeEnd)] = {'rwd' : reward}
                       
    return graph

def vslice(vslcs, graphSize):
    val = []
    vslcs = vslcs.split(',')
    sl = [*range(graphSize)]

    for vs in vslcs:
        numbs = vs.split(':')
        numbs = [int(x) if x!='' else '' for x in numbs]

        if len(numbs) == 1:
            val.append(numbs[0]) if numbs[0] >= 0 else val.append(graphSize + numbs[0])

        elif len(numbs) == 2:
            # options
            # :n
            # m:
            # m:n
            # :
            m, n = numbs
            if m == '' and n != '':
                s = sl[:n]
            elif m != '' and n == '':
                s = sl[m:]
            elif m != '' and n != '':
                s = sl[m:n]
            else:
                s = sl

            for x in s:
                val.append(x)

        elif len(numbs) == 3:
            # m::
            # m:n:
            # m::o
            # m:n:o
            # :n:
            # :n:o
            # ::o
            e = ''
            m, n, o = numbs

            if m != e and n == e and o == e:
                s = sl[m::]
            elif m != e and n != e and o == e:
                s = sl[m:n:]
            elif m != e and n == e and o != e:
                s = sl[m::o]
            elif m != e and n != e and o != e:
                s = sl[m:n:o]
            elif m == e and n != e and o == e:
                s = sl[:n:]
            elif m == e and n != e and o != e:
                s = sl[:n:o]
            elif m == e and n == e and o != e:
                s = sl[::o]
            else:
                continue

            for x in s:
                val.append(x)

    return val

def grfSize(graph):
    # returns the number of verticies the graph has
    return graph['size']

def grfGProps(graph):
    # returns the dictionary of properties for the graph, including 'width' and 'rwd'
    if graph['type'] == 'G':
        return {'rwd' : graph['rwd'], 'width' : graph['width']} 
    elif graph['type'] == 'N':
        return {'rwd' : graph['rwd']}

def grfVProps(graph, v):
    # returns the dictionary of properties of vertex v
    return {} if v not in graph['vprops'] else {'rwd':graph['vprops'][v]['rwd']}

def grfNbrs(graph, v):
    # returns a set or list of the neighbors (ie. ints) of vertex v
    return graph['graph'][v]

def grfEProps(graph, v1, v2):
    # returns the dictionary of properties of edge(v1, v2)
    if (v1, v2) not in graph['eprops']:
        return {} 
    else:
        return graph['eprops'][(v1, v2)]

def grfStrEdges(graph):
    # returns a string representation of the graph edges
    if 'width' not in graph or graph['width'] == 0: return ''
    if graph['type'] == 'N': return ''

    st = ''
    for idx in range(graph['size']):
        nbrs = graph['graph'][idx]
        if nbrs == ['']:
            st += '*'; continue
        if not nbrs:
            st += '.'; continue
        
        # print(f'{st=} {nbrs=}')
        
        dirs = set()
        for v2 in nbrs:
            d = directionFrom(graph, idx, v2)
            if d != '-': dirs.add(d)

        #print(idx, dirs)
        #print(nbrs)

        if dirs == {'N', 'W'}: st += 'J'
        elif dirs == {'N'}: st += 'N'
        elif dirs == {'N', 'W', 'E'}: st += '^'
        elif dirs == {'N', 'E'}: st += 'L'
        elif dirs == {'N', 'W', 'S'}: st += '<'
        elif dirs == {'W'}: st += 'W'
        elif dirs == {'N', 'W', 'E', 'S'}: st += '+'
        elif dirs == {'E'}: st += 'E'
        elif dirs == {'N', 'E', 'S'}: st += '>'
        elif dirs == {'S', 'W'}: st += '7'
        elif dirs == {'S', 'W', 'E'}: st += 'v'
        elif dirs == {'S'}: st += 'S'
        elif dirs == {'S', 'E'}: st += 'r'
        elif dirs == {'W', 'E'}: st += '-'
        elif dirs == {'N', 'S'}: st += '|'
        else: st += '.'
    

    j = jumps(graph)
    if j!='~': return st + '\n' + 'Jumps:' + j
    return st

def grfStrProps(graph):
    # returns a string representation of the graph edges and properties
    toRet = f"rwd:{graph['rwd']}"

    toPrint1 = ''
    for key in graph['vprops']:
        toPrint1+=f"{key}: rwd:{graph['vprops'][key]['rwd']}" + '\n'

    toPrint2 = ''
    for eS, eE in graph['eprops']:
        key = (eS, eE)
        toPrint2+=f"{(key)}: rwd:{graph['eprops'][key]['rwd']}" + '\n'

    if graph['type'] == 'G':
        toRet += f", width:{graph['width']}"

    if toPrint1:
        toRet += f'\n{toPrint1}'

    if toPrint2:
        toRet += f'\n{toPrint2}'

    return toRet

def directionFrom(graph, v1, v2):
    if v2 == v1 + 1 and v2//graph['width'] == v1//graph['width']: return 'E'
    if v2 == v1 - 1 and v2//graph['width'] == v1//graph['width']: return 'W'
    if v2 == v1 + graph['width']: return 'S'
    if v2 == v1 - graph['width']: return 'N'
    return '-'

def main():
    graph = grfParse(args)

    # stredges = grfStrEdges(graph)
    # print2d(graph, stredges)

    gw2(graph)

def jumps(graph):
    j = set()
    g = graph['graph']
    t = graph['type']
    d = graph['default']
    w = 0 if 'width' not in graph else graph['width']

    for vertex in g:
        nbrs = g[vertex]

        for nbr in nbrs:
            if nbr in d[vertex]: continue
            # must be a jump
            j.add((vertex, nbr))

    starts = ''
    ends = ''

    for s, e in j:
        starts += f'{s},'
        ends += f'{e},'
        
    starts = starts[:-1]
    ends = ends[:-1]

    v = starts + '~' + ends

    # if v != '~': print('Jumps:', v)

    return v

def print2d(graph, st):
    j = ''
    if 'Jumps' in st: 
        st = st.split('Jumps')
        j = st[-1]
        st = st[0]
    w = graph['width']
    if w == 0: print(st)
    else: print('\n'.join(st[rs:rs+w] for rs in range(0, graph['size'], w)))

    # if j: print(f'Jumps: {j}')

def gw2(graph):
    rewards = rewardLocations(graph)
    bestGraph = bfs(graph, rewards)

    t = graph['type']
    s = graph['size']
    w = -1 if 'width' not in graph else graph['width']
    r = graph['rwd']

    ISG = {
        'type' : t,
        'size' : s,
        'rwd' : r,
        'graph' : {},
        'default' : graph['default']
    }

    if w != -1:
        ISG['width'] = w

    jps = []
    for idx, obj in enumerate(bestGraph):
        if obj == '*':
            continue

        minLen, pathsToRwd = obj

        nbrs = []
        for path in pathsToRwd:
            nbr = path[-2]
            nbrs.append(nbr)
            path = path[::-1]

            for i,x in enumerate(path[1:]):
                if x not in graph['default'][path[i]]:
                    jps += [f'{path[i]}>{x}']

        ISG['graph'][idx] = nbrs

    #print(ISG['graph'])

    jps = [*{*jps}]

    idxs = [*range(graph['size'])]
    for n in idxs:
        if n not in ISG['graph']:
            ISG['graph'][n] = []

    rewards = [(x[0], x[2]) for x in rewards]
    for rwdIdx, dstToRwd in sorted(rewards):
        if dstToRwd == 0:
            ISG['graph'][rwdIdx] = ['']
    
    #print(ISG['graph'])
    st = grfStrEdges(ISG)

    print('Policy:')
    print2d(ISG, st)
    if jps: print(f'Jumps:{";".join(jps)}')
    
def rewardLocations(graph):
    rewards = []
    vprops = graph['vprops']; eprops = graph['eprops']

    for idx in vprops:
        rewards.append((idx, vprops[idx], 0))

    for edgeStart, edgeEnd in eprops:
        rewards.append((edgeStart, eprops[(edgeStart, edgeEnd)], 1))

    return rewards

def bfs(graph, rewards):
    bestGraph = [(graph['size'], [])] * graph['size']
    r = [x[0] for x in rewards if x[-1] == 1]

    for rwd, rwdAmt, t in rewards:
        if t == 0:
            bestGraph[rwd] = '*'

    #rewards = [(12, {'rwd': 74}, 1)]
    for bfsStart, rwdAmt, rwdDist in rewards:
        #print(bfsStart)
        seen = {(bfsStart, -1, 0)}
        queue = [(bfsStart, [bfsStart])]
        i = 0
        brk = False

        if rwdDist == 1:
            bestLen = 2
            bestPaths = []
            n = graph['graph'][bfsStart]
            for x in n:
                if (bfsStart, x) in graph['eprops']:
                    bestPaths.append([x, bfsStart])
                    #bestPaths.append([bfsStart, x])
            
            if bestPaths:
                if bestGraph[bfsStart] and bestGraph[bfsStart] != '*':
                    nL, nPaths = bestGraph[bfsStart]
                else:
                    nL = graph['size']
                    nPaths = []

                if nL == 2:
                    for bP in bestPaths:
                        if bP not in nPaths:
                            bestGraph[bfsStart][1].append(bP)
                else:
                    bestGraph[bfsStart] = (2, bestPaths)

        while not brk and i < len(queue):
            node = queue[i]; i += 1
            currentVertex, pathToNode = node
            
            nbrs = [x for x in graph['graph'] if currentVertex in graph['graph'][x]]
            nbrs = {*nbrs}

            #if bfsStart == 4: print(4, bestGraph[4]); print(12, bestGraph[12])

            for nbr in nbrs:
                if len(pathToNode) > 1 and (nbr, pathToNode[1], len(pathToNode)) in seen: continue

                # newnode is currentVertex
                # prev node nbr
                # test if currentVertex in graph[nbr]

                newPath = pathToNode + [nbr]
                if nbr not in r:
                    newLen = len(newPath) + rwdDist
                else:  
                    newLen = len(newPath) + rwdDist

                '''if newPath == [4, 12]:
                    print(bfsStart)
                    print(currentVertex)
                    print(pathToNode)
                    print(newPath)
                    print(nbr)
                    print(newLen)
                    print(rwdDist)'''

                if bestGraph[nbr] != '*':
                    if newLen < bestGraph[nbr][0]:
                        #print(newPath)
                        #dosmth = True
                        #if rwdDist == 1 and (newPath[-1], newPath[-2]) not in graph['eprops']: continue
                        bestGraph[nbr] = (newLen, [newPath])
                    elif newLen == bestGraph[nbr][0]:
                        #print(newPath)
                        #dosmth = True
                        #if rwdDist == 1 and (newPath[-1], newPath[-2]) not in graph['eprops']: continue
                        bestGraph[nbr] = (newLen, bestGraph[nbr][1]+[newPath])
                    else:
                        continue

                    seen.add((nbr, newPath[1], len(newPath))); queue.append((nbr, newPath))

    return bestGraph

if __name__ == '__main__': main()
# aaryan sumesh; period 2; class of 2025