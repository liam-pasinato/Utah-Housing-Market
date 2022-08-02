import streamlit as st 
import pandas as pd
import numpy as np
import plotly.express as px  
import os

from PIL import Image

import DR_Predict
import Helpers
#from DR_Predict import DEPLOYMENT_ID

#Title
st.title("*Utah* Real Estate Market")

#Full DF
df = Helpers.read_data("./Data/HousingAllFeatures/HousingAllFeatures.csv")
#df = (pd.read_csv("./Data/HousingAllFeatures/HousingAllFeatures.csv")
    #.loc[lambda x: ~pd.isna(x.bedrooms)]
#)


#Cutting columns for display
showcase_df = df.drop(['cooling','flooring','roof_type','zip_geometry','exterior_image'], axis=1)


st.write('> ## *Utah* Housing Data')
st.write('##### Use the toolbar to filter through home listings')

#Selectbox
bdrms = sorted(showcase_df['bedrooms'].astype(int).unique())
bdrm_selection = st.selectbox("Bedrooms", bdrms, index=4)

#Display selectBox & the data
st.write('*Showing data for ' + str(bdrm_selection) + ' bedroom houses*')
df_bdrm = showcase_df[showcase_df['bedrooms']==bdrm_selection]
st.write(df_bdrm)



