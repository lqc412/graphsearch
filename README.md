# 🚌 Seattle Transit Route Finder – Graph Search on Real GIS Bus Data  
**Search Techniques: BFS, DFS, A\*, Heuristic Planning**

This project implements classical graph search algorithms to find optimal bus transit routes in Seattle using real-world GIS data from King County Metro. With full graph construction, visualization, and evaluation, it compares uninformed (BFS/DFS) and informed (A\*) search methods on practical transit tasks.

---

## 🔍 Features

- **Built on real GIS data** from King County Metro (GeoJSON format)
- Implements **Breadth-First Search**, **Depth-First Search**, and **A\*** pathfinding
- Uses **Euclidean distance** as a heuristic for A*
- Includes **automatic graph edge construction** from shared `ROUTE_LIST`
- Visualizes graph search paths with color-coded edge rendering using **NetworkX + GeoPandas**
- Compares algorithm outputs under different travel directions and edge constraints

---

## 🗺️ Example Visualizations

### 🧭 Route: *Colman Dock → Discovery Park*

| Algorithm | Map Overview | Zoomed Path |
|----------|---------------|--------------|
| **BFS**  | ![BFS](./1stResults/bfs_overview.png) | ![Zoom](./1stResults/bfs_zoom.png) |
| **DFS**  | ![DFS](./1stResults/dfs_overview.png) | ![Zoom](./1stResults/dfs_zoom.png) |
| **A\***  | ![A*](./1stResults/astar_overview.png) | ![Zoom](./1stResults/astar_zoom.png) |

---

## 📦 Tech Stack

- **Python**
- `networkx`, `geopandas`, `contextily`, `matplotlib`
- GIS dataset from: [King County Metro Open Data](https://gis-kingcounty.opendata.arcgis.com/)

---

## 📍 Usage

1. Install dependencies:

```bash
pip install networkx geopandas contextily numpy matplotlib shapely
```
2. Run the search:
```bash
python seattle.py
```
The program will prompt for starting and destination stops (e.g., `Alaskan Way & Columbia St`, `W Government Way & 36th Ave W`).

3. View generated visualizations and distances in the results/ folder.