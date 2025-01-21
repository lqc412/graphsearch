import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import Point

"""
Replace these comments with documenation about the program.
It is important to note that failure to add your name will
result in an automatic zero. You have been warned.
@author [add your name]
"""

def add_to_graph(graph : nx.Graph, geodataframe : gpd.GeoDataFrame, color):
    """
    Update this documentation to explain what this code is doing
    """
    for _, row in geodataframe.iterrows():
        geometry = row.geometry
        if geometry.geom_type == "Point" and row.ROUTE_LIST != None:
            attributes = row.to_dict()
            attributes['color'] = color
            graph.add_node(tuple(geometry.coords[0]), **attributes)


def main():
    """
    Main body of your code below.
    """
    gdf = gpd.read_file("Transit_Stops_for_King_County_Metro___transitstop_point.geojson")
    G = nx.Graph()
    add_to_graph(G, gdf, "blue")

    # Uncomment to see the nodes with attributes
    # for node, attr in G.nodes(data=True):
    #    print(f"Node: {node}, Attributes: {attr}")

    fig, ax = plt.subplots(figsize=(10, 10))
    nodes = gpd.GeoDataFrame(
        {'geometry': [Point(x, y) for x, y in G.nodes]},
        crs="EPSG:4326"
    )
    nodes.plot(ax=ax, color="blue", markersize=5)
    ctx.add_basemap(ax, crs=nodes.crs.to_string(), zoom=11)
    plt.title("King County Transit Stops", fontsize=15)
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()

### Do NOT remove the following lines of code
if __name__ == "__main__":
    main()