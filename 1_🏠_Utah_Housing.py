import geopandas as gpd
import json
import numpy as np
import os
import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image

import DR_Predict
import Helpers

# Webpage title & icon 
Helpers.title_and_logo()

# Hide streamlit menu & watermark
Helpers.hide_streamlit_menu()

# Title
st.title("*Utah* Real Estate Market")

# Full DF
df = Helpers.read_data("./Data/HousingAllFeatures/HousingAllFeatures.csv")

# Cutting columns for display
showcase_df = df.drop(
    ["cooling", "flooring", "roof_type", "zip_geometry", "exterior_image"], axis=1
)

# "About" dropdown
with st.expander("About:"):
    st.write(
        "This webpage uses a machine learning model made on DataRobot's ML platform to predict house prices in the state of Utah."
    )
    st.write(
        "The model was trained on a demo dataset containing thousands of house listings from Utah and their respective features."
    )
    st.write(
        "The house viewing page allows you to view a single listing in more detail, along with the real and predicted values for the house and explanations for the house price."
    )
    st.write(
        "The price prediction page allows you to send a new listing to the DataRobot app, and ping the ML model to predict the price of the house with the feautures you have set. This includes explanations behind what is driving the model to estimate the house's value."
    )

color_choices = ["price", "sq_ft", "acres"]

# Geometry is at zipcode level, should make whatever we want to plot also be at zipcode level
df_zip_agg = (
    df.groupby("zip_geometry")[color_choices]
    .mean()
    .reset_index()
    .assign(
        price=lambda x: x.price.astype(int),
        sq_ft=lambda x: x.sq_ft.astype(int),
        acres=lambda x: x.acres.round(2),
        price_per_sq_ft=lambda x: (x.price / x.sq_ft).round(2),
    )
)

# Zip geometry is read as a string, need to transform it into an actual geometry column type (gpd)
# https://stackoverflow.com/questions/56433138/converting-a-column-of-polygons-from-string-to-geopandas-geometry
df_zip_agg["zip_geometry"] = gpd.GeoSeries.from_wkt(df_zip_agg["zip_geometry"])
average_price_per_geometry = gpd.GeoDataFrame(
    df_zip_agg, geometry="zip_geometry"
).assign(id_col=lambda x: x.index)

# Polygon doesn't look like plotly format
# We can fix with a small trick (this was a guess on my part). Another choice was an in depth for loop
json_string = average_price_per_geometry.loc[
    ~pd.isna(average_price_per_geometry.zip_geometry), ["id_col", "zip_geometry"]
].to_json()
geo_json = json.loads(json_string)
average_price_per_geometry = average_price_per_geometry.rename(
    columns={"id_col": "Map ID"}
)

if "ppsqft_data" not in st.session_state:
    st.session_state["ppsqft_data"] = average_price_per_geometry

Helpers.plot_choropleth(average_price_per_geometry, geo_json, "price_per_sq_ft")
