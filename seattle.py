import networkx as nx
import geopandas as gpd
import math
import contextily as ctx
import matplotlib.pyplot as plt
from shapely.geometry import Point
from collections import deque
import heapq
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import geopandas as gpd
from shapely.geometry import Point
from collections import deque

"""
1) Reads the "Transit_Stops_for_King_County_Metro___transitstop_point.geojson" file,
   building a NetworkX graph where each node is a transit stop identified by (longitude, latitude).
2) Connects stops that share a route (based on 'ROUTE_LIST') and assigns the Euclidean distance
   as the edge weight.
3) Prompts the user for a start and end stop (in "Street1 & Street2" or single-name format).
4) Performs three searches (BFS, DFS, and A*) to find a path between these stops,
   stopping as soon as the goal is found.
5) Visualizes each search in two PNG images (an overview and, if a path is found, a zoomed-in view),
   coloring visited nodes/edges in orange and any final path in red. Start/end nodes are highlighted
   in distinct colors and larger markers.
@author Quancheng Li
"""

def parse_street_input(user_input: str):
    user_input = user_input.strip()
    if "&" in user_input:
        parts = [p.strip() for p in user_input.split("&")]
        if len(parts) >= 2:
            return parts[0], parts[1]
        else:
            print("Warning: input has '&' but not enough parts.")
            return user_input, None
    else:
        return user_input, None


def find_node_by_streets(G: nx.Graph, s1: str, s2: str=None):
    s1_lower = s1.lower().strip()
    s2_lower = s2.lower().strip() if s2 else None

    for node, data in G.nodes(data=True):
        if not data.get("ROUTE_LIST", None):
            continue
        on_st = str(data.get("ON_STREET_NAME", "")).lower().strip()
        cross_st = str(data.get("CF_CROSS_STREETNAME", "")).lower().strip()

        if s2_lower is None:
            if on_st == s1_lower or cross_st == s1_lower:
                return node
        else:
            cond1 = (on_st == s1_lower and cross_st == s2_lower)
            cond2 = (on_st == s2_lower and cross_st == s1_lower)
            if cond1 or cond2:
                return node
    return None


def euclidean_distance(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

def add_to_graph(G: nx.Graph, gdf: gpd.GeoDataFrame):
    """
    Adds transit stops from the given GeoDataFrame to the graph as nodes.

    1) Iterates over each row in the GeoDataFrame.
    2) Checks if the geometry is a Point and 'ROUTE_LIST' is non-empty.
       (We only care about transit stops that have at least one route.)
    3) Extracts the Point's longitude (lon) and latitude (lat),
       then uses (lon, lat) as the node identifier in the graph.
    4) Converts the entire row into a dictionary (row.to_dict()) and stores these
       attributes in the node, including a 'pos' attribute for convenience.
    5) As a result, each qualifying transit stop is represented as a node,
       with relevant data (like 'ON_STREET_NAME', 'CF_CROSS_STREETNAME') attached.
    """
    for _, row in gdf.iterrows():
        geom = row.geometry
        if geom.geom_type == "Point" and row.ROUTE_LIST:
            lon, lat = geom.coords[0]
            attrs = row.to_dict()
            attrs['pos'] = (lon, lat)
            G.add_node((lon, lat), **attrs)

def create_edges_by_route(G: nx.Graph):
    route_dict = {}
    for node, data in G.nodes(data=True):
        routes_str = data.get("ROUTE_LIST", "")
        routes = routes_str.split()
        for r in routes:
            route_dict.setdefault(r, []).append(node)

    for r, node_list in route_dict.items():
        node_list = list(set(node_list))
        node_list.sort(key=lambda n: (n[1], n[0]))
        for i in range(len(node_list)-1):
            n1 = node_list[i]
            n2 = node_list[i+1]
            if not G.has_edge(n1, n2):
                dist = euclidean_distance(n1, n2)
                G.add_edge(n1, n2, weight=dist, route=r)

def bfs_expansion(G: nx.Graph, start, goal):
    queue = deque([start])
    visited_nodes = set([start])
    parent = {}
    visited_edges = set()

    while queue:
        current = queue.popleft()
        if current == goal:
            return backtrace_path(parent, start, goal), visited_edges, visited_nodes

        for nbr in G.neighbors(current):
            if nbr not in visited_nodes:
                visited_nodes.add(nbr)
                parent[nbr] = current
                visited_edges.add(tuple(sorted((current, nbr))))
                queue.append(nbr)

    return None, visited_edges, visited_nodes


def dfs_expansion(G: nx.Graph, start, goal):
    stack = [start]
    visited_nodes = set([start])
    parent = {}
    visited_edges = set()

    while stack:
        current = stack.pop()
        if current == goal:
            return backtrace_path(parent, start, goal), visited_edges, visited_nodes

        for nbr in G.neighbors(current):
            if nbr not in visited_nodes:
                visited_nodes.add(nbr)
                parent[nbr] = current
                visited_edges.add(tuple(sorted((current, nbr))))
                stack.append(nbr)

    return None, visited_edges, visited_nodes


def astar_expansion(G: nx.Graph, start, goal):
    if start == goal:
        return [start], set(), {start}

    visited_edges = set()
    visited_nodes = set([start])
    gCost = {start: 0.0}
    openSet = []
    heapq.heappush(openSet, (0.0, start))
    inOpen = {start}

    def heuristic(u, v):
        return euclidean_distance(u, v)

    parent = {}

    while openSet:
        fCurr, current = heapq.heappop(openSet)
        inOpen.discard(current)
        if current == goal:
            return backtrace_path(parent, start, goal), visited_edges, visited_nodes

        visited_nodes.add(current)
        for nbr in G.neighbors(current):
            visited_nodes.add(nbr)
            edgeW = G[current][nbr].get("weight", 1.0)
            new_g = gCost[current] + edgeW
            if nbr not in gCost or new_g < gCost[nbr]:
                gCost[nbr] = new_g
                parent[nbr] = current
                visited_edges.add(tuple(sorted((current, nbr))))
                fScore = new_g + heuristic(nbr, goal)
                if nbr not in inOpen:
                    heapq.heappush(openSet, (fScore, nbr))
                    inOpen.add(nbr)

    return None, visited_edges, visited_nodes


def backtrace_path(parent, start, goal):
    path = [goal]
    while path[-1] != start:
        path.append(parent[path[-1]])
    path.reverse()
    return path


def total_distance(G: nx.Graph, path):
    if not path or len(path) < 2:
        return 0.0
    dist = 0.0
    for i in range(len(path)-1):
        if G.has_edge(path[i], path[i+1]):
            dist += G[path[i]][path[i+1]].get("weight", 0.0)
    return dist

def visualize_search(G: nx.Graph,
                     path,
                     visited_edges=None,
                     visited_nodes=None,
                     start_node=None,
                     goal_node=None,
                     out_file="search_result.png",
                     title="Search Result",
                     xlim=None,
                     ylim=None,
                     zoom=11):
    """
    - visited_nodes => orange
    - visited_edges => orange
    - path => red edges
    - start_node => green (size=80)
    - goal_node  => yellow (size=80)
    - unvisited => blue/gray
    If no path => no red edges. Still show start/goal in bigger size.
    """
    visited_nodes = visited_nodes or set()

    node_coords = []
    node_colors = []
    node_sizes  = []

    for nd in G.nodes():
        node_coords.append(Point(nd[0], nd[1]))

        # default
        color = "blue"
        size  = 3

        # if visited => orange
        if nd in visited_nodes:
            color = "orange"

        # if it's start_node => override => green
        if start_node and nd == start_node:
            color = "green"
            size  = 80

        # if it's goal_node => override => yellow
        if goal_node and nd == goal_node:
            color = "yellow"
            size  = 80

        node_colors.append(color)
        node_sizes.append(size)

    gdf_nodes = gpd.GeoDataFrame({'geometry': node_coords,
                                  'color': node_colors,
                                  'size': node_sizes},
                                 crs="EPSG:4326")

    fig, ax = plt.subplots(figsize=(10, 10))
    gdf_nodes.plot(ax=ax,
                   color=gdf_nodes['color'],
                   markersize=gdf_nodes['size'],
                   alpha=0.8)

    path_edges = set()
    if path and len(path) > 1:
        for i in range(len(path)-1):
            e = tuple(sorted((path[i], path[i+1])))
            path_edges.add(e)

    for (u, v) in G.edges():
        e_sorted = tuple(sorted((u, v)))
        x1, y1 = u
        x2, y2 = v
        color = "lightgray"
        lw = 0.5

        if visited_edges and e_sorted in visited_edges:
            color = "orange"
            lw = 0.8

        if e_sorted in path_edges:
            color = "red"
            lw = 2.0

        ax.plot([x1, x2], [y1, y2], color=color, linewidth=lw, alpha=0.9)

    if xlim:
        ax.set_xlim(xlim)
    if ylim:
        ax.set_ylim(ylim)

    ctx.add_basemap(ax, crs=gdf_nodes.crs.to_string(), zoom=zoom)

    legend_patches = [
        mpatches.Patch(color='blue',   label='Unvisited Nodes'),
        mpatches.Patch(color='orange', label='Visited Nodes'),
        mpatches.Patch(color='green',  label='Start Node'),
        mpatches.Patch(color='yellow', label='Goal Node'),
        mlines.Line2D([], [], color='lightgray', label='Unvisited Edges', linewidth=1),
        mlines.Line2D([], [], color='orange',    label='Visited Edges',   linewidth=1),
        mlines.Line2D([], [], color='red',       label='Final Path',      linewidth=2),
    ]
    ax.legend(handles=legend_patches, loc='upper right')

    plt.title(title, fontsize=13)
    plt.savefig(out_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved visualization to {out_file}")


def get_path_bounding_box(path, margin=0.01):
    if not path:
        return None, None
    xs = [p[0] for p in path]
    ys = [p[1] for p in path]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    minx -= margin
    maxx += margin
    miny -= margin
    maxy += margin
    return (minx, maxx), (miny, maxy)


def main():
    # 1) Load data
    gdf = gpd.read_file("Transit_Stops_for_King_County_Metro___transitstop_point.geojson")
    print(f"Total features: {len(gdf)}")

    # 2) Build graph
    G = nx.Graph()
    add_to_graph(G, gdf)
    create_edges_by_route(G)
    print(f"Graph built with {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")

    # 3) user input
    start_input = input("Enter start station or 'Street1 & Street2': ")
    goal_input  = input("Enter goal station or 'Street1 & Street2': ")

    s1a, s1b = parse_street_input(start_input)
    g1a, g1b = parse_street_input(goal_input)

    start_node = find_node_by_streets(G, s1a, s1b)
    goal_node  = find_node_by_streets(G, g1a, g1b)
    if not start_node or not goal_node:
        print("Could not find start or goal node in the graph.")
        return
    print("Start node:", start_node)
    print("Goal node:", goal_node)

    # BFS
    bfs_path, bfs_edges, bfs_nodes = bfs_expansion(G, start_node, goal_node)
    bfs_dist = total_distance(G, bfs_path)
    if bfs_path:
        bfs_title = f"BFS Overview (dist={bfs_dist:.2f})"
    else:
        bfs_title = "BFS Overview (no route found)"

    visualize_search(G,
                     path=bfs_path,
                     visited_edges=bfs_edges,
                     visited_nodes=bfs_nodes,
                     start_node=start_node,
                     goal_node=goal_node,
                     out_file="bfs_overview.png",
                     title=bfs_title,
                     zoom=11)
    # Zoom in
    if bfs_path:
        (xminmax, yminmax) = get_path_bounding_box(bfs_path, margin=0.005)
        xlim_bfs = (xminmax[0], xminmax[1])
        ylim_bfs = (yminmax[0], yminmax[1])
        visualize_search(G,
                         path=bfs_path,
                         visited_edges=bfs_edges,
                         visited_nodes=bfs_nodes,
                         start_node=start_node,
                         goal_node=goal_node,
                         out_file="bfs_zoom.png",
                         title=bfs_title.replace("Overview", "Zoom"),
                         zoom=15,
                         xlim=xlim_bfs,
                         ylim=ylim_bfs)

    # DFS
    dfs_path, dfs_edges, dfs_nodes = dfs_expansion(G, start_node, goal_node)
    dfs_dist = total_distance(G, dfs_path)
    if dfs_path:
        dfs_title = f"DFS Overview (dist={dfs_dist:.2f})"
    else:
        dfs_title = "DFS Overview (no route found)"

    visualize_search(G,
                     path=dfs_path,
                     visited_edges=dfs_edges,
                     visited_nodes=dfs_nodes,
                     start_node=start_node,
                     goal_node=goal_node,
                     out_file="dfs_overview.png",
                     title=dfs_title,
                     zoom=11)
    # Zoom in
    if dfs_path:
        (xminmax, yminmax) = get_path_bounding_box(dfs_path, margin=0.005)
        xlim_dfs = (xminmax[0], xminmax[1])
        ylim_dfs = (yminmax[0], yminmax[1])
        visualize_search(G,
                         path=dfs_path,
                         visited_edges=dfs_edges,
                         visited_nodes=dfs_nodes,
                         start_node=start_node,
                         goal_node=goal_node,
                         out_file="dfs_zoom.png",
                         title=dfs_title.replace("Overview", "Zoom"),
                         zoom=15,
                         xlim=xlim_dfs,
                         ylim=ylim_dfs)

    # A*
    a_star_path, a_star_edges, a_star_nodes = astar_expansion(G, start_node, goal_node)
    a_star_dist = total_distance(G, a_star_path)
    if a_star_path:
        a_star_title = f"A* Overview (dist={a_star_dist:.2f})"
    else:
        a_star_title = "A* Overview (no route found)"

    visualize_search(G,
                     path=a_star_path,
                     visited_edges=a_star_edges,
                     visited_nodes=a_star_nodes,
                     start_node=start_node,
                     goal_node=goal_node,
                     out_file="astar_overview.png",
                     title=a_star_title,
                     zoom=11)
    # Zoom in
    if a_star_path:
        (xminmax, yminmax) = get_path_bounding_box(a_star_path, margin=0.005)
        xlim_astar = (xminmax[0], xminmax[1])
        ylim_astar = (yminmax[0], yminmax[1])
        visualize_search(G,
                         path=a_star_path,
                         visited_edges=a_star_edges,
                         visited_nodes=a_star_nodes,
                         start_node=start_node,
                         goal_node=goal_node,
                         out_file="astar_zoom.png",
                         title=a_star_title.replace("Overview", "Zoom"),
                         zoom=15,
                         xlim=xlim_astar,
                         ylim=ylim_astar)

### Do NOT remove the following lines of code
if __name__ == "__main__":
    main()
