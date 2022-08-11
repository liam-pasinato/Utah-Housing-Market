from cgitb import small

import numpy as np
import pandas as pd
from PIL import Image
import plotly.express as px
import streamlit as st 

import DR_Predict
import Helpers

# Webpage title & icon
Helpers.title_and_logo()

# Hide streamlit menu & watermark
Helpers.hide_streamlit_menu()

predictions = pd.read_csv('./Data/Prediction_Explanations.csv')
small_df = pd.read_csv('./Data/clean_small_data.csv')

try:
    df = st.session_state['base_data']
except KeyError:
    df = Helpers.read_data('./Data/HousingAllFeatures/HousingAllFeatures.csv')

price_per_sqft_df = st.session_state['ppsqft_data']

st.write('# House Viewings')

#House viewing form
with st.form(key='View_form'):
    listings = sorted(predictions['listing_id'].astype(int).unique())
    listing_select = st.selectbox('Enter the listing ID for the house you would like to view', listings, help = 'Use the table below to find the correct listing ID')
    st.write('Price prediction form will be autofilled with values from selected listing')
    view_button = st.form_submit_button(label = 'View House')

if view_button:
    view_df = df.loc[df['listing_id']==int(listing_select)]
    st.session_state['viewing_data'] = view_df

    house_img_check = list(view_df['exterior_image'])[0]
    house_img = str(list(view_df['exterior_image'])[0])

    if not pd.isna(house_img_check):
        house_img = str(house_img_check)
        img_jpg = Image.open('./Data/HousingAllFeatures/' + house_img)
    
    else:
        img_jpg = Image.open('./Data/no_img_available.jpeg')

    viewing_expl_df = predictions[predictions['listing_id']==listing_select]
    real = int(viewing_expl_df['price'])
    estimate = int(viewing_expl_df['price_PREDICTION']) 

    explanation_dict=Helpers.prediction_variables(viewing_expl_df, price_per_sqft_df)
    
    Helpers.write_view_explanation(real, estimate, img_jpg, listing_select, explanation_dict)
   
    st.write('> #### House Features')

    #cleaning view df
    view_df = view_df.drop(['zip_geometry', 'exterior_image'], axis=1)
    view_df = view_df.rename(columns={'listing_id': 'Listing ID', 'price': 'Price', 'acres': 'Acres', 'bathrooms': 'Bath', 'bedrooms': 'Bed', 'car_garage': 'Car Garage', 'patios': 'Patios', 'sq_ft': 'Sq. Footage', 'cooling': 'Cooling', 'elementary': 'Elementary School', 'flooring': 'Floors', 'roof_type': 'Roofing', 'year_built': 'Build Year', 'amenities': 'Amenities', 'sold_date': 'Sold Date'})
    columns = ['Patios', 'Car Garage', 'Sq. Footage', 'Bed']

    for i in columns:
        view_df[i] = Helpers.clean_columns(view_df, i)
    
    st.write(view_df)

st.write('> #### Available Viewings')

#Multiselect boxes for filtering
filt1, filt2, filt3 = st.columns(3, gap='medium')

with filt1:
    bed_filt = st.multiselect('Filter by bedrooms', sorted(small_df['bedrooms'].astype(int).unique()))
    bath_filt = st.multiselect('Filter by bathrooms', sorted(small_df['bathrooms'].astype(int).unique()))

with filt2:
    garage_filt = st.multiselect('Filter by garage size', [0,1,2,3,4,5,6])
    patio_filt = st.multiselect('Filter by patios', [0,1,2])
    
with filt3:
    price_filt = st.selectbox('Filter by price', ['ANY', '40000 - 100000', '100000 - 250000', '250000 - 500000', '500000 - 750000', '750000 - 1000000', '1000000 - 1500000', '1500000 - 2000000'], index=0 )
    sqft_filt = st.selectbox('Filter by square footage', ['ANY', '500 - 1000', '1000 - 1500', '1500 - 2000', '2000 - 3000', '3000 - 4000', '4000 - 5000', '5000 - 6500'], index=0)

#Removing unnecessary cols and renaming cols
df_filt = small_df.drop(['zip_geometry','exterior_image'], axis=1)
df_filt = df_filt.rename(columns={'listing_id': 'Listing ID', 'price': 'Price', 'acres': 'Acres', 'bathrooms': 'Bath', 'bedrooms': 'Bed', 'car_garage': 'Car Garage', 'patios': 'Patios', 'sq_ft': 'Sq. Footage', 'cooling': 'Cooling', 'elementary': 'Elementary School', 'flooring': 'Floors', 'roof_type': 'Roofing', 'year_built': 'Build Year', 'amenities': 'Amenities', 'sold_date': 'Sold Date'})

#Filtering by multiselect & select boxes
filter_dict = {
    0: {'filt': bed_filt, 'column': 'Bed'},
    1: {'filt': bath_filt, 'column': 'Bath'},
    2: {'filt': garage_filt, 'column': 'Car Garage'},
    3: {'filt': patio_filt, 'column': 'Patios'},
}

for i in filter_dict:
    col = filter_dict[i]['column']
    filt = filter_dict[i]['filt']
    if filt:    
        df_filt = df_filt[df_filt[col].isin(filt)]

df_filt = Helpers.filter_range(df_filt, price_filt, 'Price')
df_filt = Helpers.filter_range(df_filt, sqft_filt, 'Sq. Footage')

#Converting float to int
cols = ['Car Garage', 'Patios']
for i in cols:
        df_filt[i] = Helpers.clean_columns(df_filt, i)

st.write(df_filt)


