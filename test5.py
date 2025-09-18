import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
import leafmap.foliumap as leafmap

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

# Set CRS for each GeoDataFrame (assuming WGS84)
facility.crs = "EPSG:4326"
buildings.crs = "EPSG:4326"
gardens.crs = "EPSG:4326"

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
        "Google Satellite": "SATELLITE",
        "Google Hybrid": "HYBRID",
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
# Step 6: Function to create the map
# --------------------------
def create_map(basemap):
    m = leafmap.Map(locate_control=True, draw_control=True)
    
    # Set the initial view based on the facility layer bounds
    bounds = facility.total_bounds  # [minx, miny, maxx, maxy]
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
    m.add_basemap(basemap)

    # Add Facility Layer
    facility_layer = folium.FeatureGroup(name="Facilities").add_to(m)
    for _, f_row in facility.iterrows():
        folium.GeoJson(
            f_row['geometry'],
            style_function=lambda x: {
                "color": "black",
                "weight": 2,
                "fillOpacity": 0
            },
            tooltip=f"<b>Facility:</b> {f_row['Name']}"
        ).add_to(facility_layer)

    # Add Buildings Layer
    buildings_layer = folium.FeatureGroup(name="Buildings").add_to(m)
    for _, b_row in buildings.iterrows():
        folium.GeoJson(
            b_row['geometry'],
            style_function=lambda x: {
                "color": "blue",
                "weight": 1,
                "fillOpacity": 0.6
            },
            tooltip=f"<b>Building:</b> {b_row['Name']}"
        ).add_to(buildings_layer)

    # Define crop colors
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

    # Create a Gardens layer
    gardens_layer = folium.FeatureGroup(name="Gardens").add_to(m)

    # Add gardens layer with filtering and color coding
    for _, g_row in gardens.iterrows():
        plot_history = filtered_history[filtered_history["plot_name"] == g_row["plot_name"]]

        # Default values for tooltip
        crop = "No crop data"
        year = "N/A"
        season = "N/A"
        rotation = "N/A"
        color = default_color

        if not plot_history.empty:
            for _, h_row in plot_history.iterrows():
                crop = h_row["crop_type"]
                year = h_row["year"]
                season = h_row["season"]
                rotation = h_row["rotation_order"]
                color = crop_colors.get(crop, default_color)
                break  # Use the first matching record

        # Create the GeoJson with custom styles and tooltip
        geojson = folium.GeoJson(
            g_row["geometry"],
            style_function=lambda x, col=color: {
                "fillColor": col,
                "color": "darkgreen",
                "weight": 1,
                "fillOpacity": 0.7,
            },
            tooltip=(
                f"<b>Plot:</b> {g_row['plot_name']}<br>"
                f"<b>Crop:</b> {crop}<br>"
                f"<b>Year:</b> {year}<br>"
                f"<b>Season:</b> {season}<br>"
                f"<b>Rotation:</b> {rotation}"
            )
        )
        geojson.add_to(gardens_layer)

    return m

# --------------------------
# Step 7: Create and display the map
# --------------------------
m = create_map(basemap_options[selected_basemap])
with col2:
    m.to_streamlit(height=700)
