import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium

# --------------------------
# Step 0: Streamlit page config
# --------------------------
st.set_page_config(layout="wide")

# --------------------------
# Step 1: Load GIS layers
# --------------------------
facility = gpd.read_file("Layout_facility_boundary.geojson")
buildings = gpd.read_file("buildings.geojson")
gardens = gpd.read_file("Planting_area.geojson")
history = pd.read_csv("planting_records.csv")

# --------------------------
# Step 2: Rename columns
# --------------------------
gardens = gardens.rename(columns={"Name": "plot_name", "rotat orde": "rotation_order"})
history = history.rename(columns={"Name": "plot_name", "rotation_o": "rotation_order"})

# --------------------------
# Step 3: Normalize strings
# --------------------------
gardens["plot_name"] = gardens["plot_name"].str.strip().str.lower()
history["plot_name"] = history["plot_name"].str.strip().str.lower()
history["season"] = history["season"].str.strip().str.lower()

# --------------------------
# Step 4: Create two columns: filters left, map right
# --------------------------
col1, col2 = st.columns([1, 3])

with col1:
    years_options = ["All"] + sorted(history["year"].unique())
    selected_year = st.selectbox("Select Year", years_options)

    seasons_options = ["All"] + sorted(history["season"].unique())
    selected_season = st.selectbox("Select Season", seasons_options)

    rotation_options = ["All"] + sorted(history["rotation_order"].unique())
    selected_rotation = st.selectbox("Select Rotation Order", rotation_options)

    # Basemap selection
    basemap_options = {
        "OpenStreetMap": "OpenStreetMap",
        "CartoDB Dark": "CartoDB dark_matter",
        "Google Satellite": "Google Satellite",
        "Google Hybrid": "Google Hybrid"
    }
    selected_basemap = st.selectbox("Select Basemap", list(basemap_options.keys()))

# --------------------------
# Step 5: Filter history
# --------------------------
filtered_history = history.copy()
if selected_year != "All":
    filtered_history = filtered_history[filtered_history["year"] == selected_year]
if selected_season != "All":
    filtered_history = filtered_history[filtered_history["season"] == selected_season]
if selected_rotation != "All":
    filtered_history = filtered_history[
        filtered_history["rotation_order"] == selected_rotation
    ]

# --------------------------
# Step 6: Map center
# --------------------------
center = [
    facility.geometry.centroid.y.mean(),
    facility.geometry.centroid.x.mean(),
]

# Create map
m = folium.Map(location=center, zoom_start=17)

# Add selected basemap
if selected_basemap == "OpenStreetMap":
    folium.TileLayer("OpenStreetMap", attr="© OpenStreetMap contributors").add_to(m)
elif selected_basemap == "CartoDB Dark":
    folium.TileLayer("CartoDB dark_matter", attr="© CartoDB").add_to(m)
elif selected_basemap == "Google Satellite":
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        name="Google Satellite",
        attr="© Google Maps"
    ).add_to(m)
elif selected_basemap == "Google Hybrid":
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        name="Google Hybrid",
        attr="© Google Maps"
    ).add_to(m)

# --------------------------
# Step 7: Create FeatureGroups
# --------------------------
facility_layer = folium.FeatureGroup(name="Facility Boundary", show=True)
buildings_layer = folium.FeatureGroup(name="Buildings", show=True)
gardens_layer = folium.FeatureGroup(name="Gardens", show=True)

# --------------------------
# Step 8: Draw Facility Boundary
# --------------------------
folium.GeoJson(
    facility,
    style_function=lambda x: {"color": "black", "weight": 2, "fillOpacity": 0},
    tooltip="<b>Facility Boundary</b>",
).add_to(facility_layer)

# --------------------------
# Step 9: Draw Buildings
# --------------------------
for _, row in buildings.iterrows():
    color = (
        "lightblue"
        if row["Name"] == "Assembly"
        else "lightgreen"
        if row["Name"] == "Painting"
        else "red"
    )
    folium.GeoJson(
        row["geometry"],
        style_function=lambda x, col=color: {
            "fillColor": col,
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.6,
        },
        tooltip=f"<b>{row['Name']}</b>",
    ).add_to(buildings_layer)

# --------------------------
# Step 10: Draw Gardens with filtered popups
# --------------------------
crop_colors = {
    "Maize": "yellow",
    "Soy Bean": "orange",
    "Navy Bean": "lightblue",
    "Alphapha": "green",
    "Wheat": "brown",
    "Groundnuts": "darkorange",
    "Cow peas": "pink",
}
default_color = "grey"

for _, g_row in gardens.iterrows():
    plot_history = filtered_history[filtered_history["plot_name"] == g_row["plot_name"]]

    if not plot_history.empty:
        for _, h_row in plot_history.iterrows():
            crop = h_row["crop_type"]
            year = h_row["year"]
            season = h_row["season"]
            rotation = h_row["rotation_order"]
            color = crop_colors.get(crop, default_color)
            folium.GeoJson(
                g_row["geometry"],
                style_function=lambda x, col=color: {
                    "fillColor": col,
                    "color": "darkgreen",
                    "weight": 1,
                    "fillOpacity": 0.7,
                },
                tooltip=f"<b>Plot:</b> {g_row['plot_name']}<br>"
                f"<b>Crop:</b> {crop}<br>"
                f"<b>Year:</b> {year}<br>"
                f"<b>Season:</b> {season}<br>"
                f"<b>Rotation:</b> {rotation}",
            ).add_to(gardens_layer)
    else:
        folium.GeoJson(
            g_row["geometry"],
            style_function=lambda x: {
                "fillColor": default_color,
                "color": "darkgreen",
                "weight": 1,
                "fillOpacity": 0.5,
            },
            tooltip=f"Plot: {g_row['plot_name']}<br>No crop record for selection",
        ).add_to(gardens_layer)

# --------------------------
# Step 11: Add FeatureGroups to map
# --------------------------
facility_layer.add_to(m)
buildings_layer.add_to(m)
gardens_layer.add_to(m)

# --------------------------
# Step 12: Add Layer Control
# --------------------------
folium.LayerControl(position='topleft', collapsed=True).add_to(m)

# --------------------------
# Step 13: Display map
# --------------------------
with col2:
    st_folium(m, width=1400, height=800)