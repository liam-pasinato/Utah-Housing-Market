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

average_price_per_geometry, geo_json = Helpers.build_map_data()

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

Helpers.plot_choropleth(average_price_per_geometry, geo_json, "price_per_sq_ft")

