from cgitb import small

import streamlit as st 
import pandas as pd
import numpy as np
import plotly.express as px
 

from PIL import Image

import DR_Predict
import Helpers


predictions = pd.read_csv('./Data/Prediction_Explanations.csv')
small_df = pd.read_csv('./Data/clean_small_data.csv')

try:
    df = st.session_state['base_data']
except KeyError:
    df = Helpers.read_data('./Data/HousingAllFeatures/HousingAllFeatures.csv')

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

    house_img = str(list(view_df['exterior_image'])[0])
    img_jpg = Image.open('./Data/HousingAllFeatures/' + house_img)
    viewing_expl_df = predictions[predictions['listing_id']==listing_select]
    real = int(viewing_expl_df['price'])
    estimate = int(viewing_expl_df['price_PREDICTION']) 

    col1, col2 = st.columns(2, gap = "medium")
    explain1 = viewing_expl_df['EXPLANATION_1_FEATURE_NAME'].iloc[0]
    explain2 = viewing_expl_df['EXPLANATION_2_FEATURE_NAME'].iloc[0]
    explain3 = viewing_expl_df['EXPLANATION_3_FEATURE_NAME'].iloc[0]
    value1 = viewing_expl_df['EXPLANATION_1_ACTUAL_VALUE'].iloc[0]
    value2 = viewing_expl_df['EXPLANATION_2_ACTUAL_VALUE'].iloc[0]
    value3 = viewing_expl_df['EXPLANATION_3_ACTUAL_VALUE'].iloc[0]
    strength1 = viewing_expl_df['EXPLANATION_1_STRENGTH'].iloc[0]
    strength2 = viewing_expl_df['EXPLANATION_2_STRENGTH'].iloc[0]
    strength3 = viewing_expl_df['EXPLANATION_3_STRENGTH'].iloc[0]
    qual_strgth1 = viewing_expl_df['EXPLANATION_1_QUALITATIVE_STRENGTH'].iloc[0]
    qual_strgth2 = viewing_expl_df['EXPLANATION_2_QUALITATIVE_STRENGTH'].iloc[0]
    qual_strgth3 = viewing_expl_df['EXPLANATION_3_QUALITATIVE_STRENGTH'].iloc[0]

    if explain1 == 'zip_geometry':
        if strength1 >= 0:
            value1 = 'Good location'
        else:
            value1 = 'Bad location'
    else:
        explain1 = explain1
    
    if explain2 == 'zip_geometry':
        if strength2 >= 0:
            value2 = 'Good location'
        else:
            value2 = 'Bad location'
    else:
        explain2 = explain2

    if explain3 == 'zip_geometry':
        if strength3 >= 0:
            value3 = 'Good location'
        else:
            value3 = 'Bad location'
    else:
        explain3 = explain3

    with col1:
        st.write('> #### Real Price: ' + "${:,.2f}".format(real))
        st.image(img_jpg, caption= f'Listing ID: {listing_select}')
    
    with col2:
        st.write('> #### Predicted Price: ' + "${:,.2f}".format(estimate))
        st.write('##### Factors influencing house price:')

        feat1 = st.expander('1. ' + explain1 + '  ' + qual_strgth1)
        feat1.write(explain1 + ': ' + value1)
        feat1.write('Strength: ' + str(strength1))
        if strength1 >= 0:
            feat1.write(explain1+' positively impacts prediction')
        else:
            feat1.write(explain1+' negatively impacts prediction')

        feat2 = st.expander('2. ' + explain2 + '  ' + qual_strgth2)
        feat2.write(explain2 + ': ' + value2)
        feat2.write('Strength: ' + str(strength2))
        if strength2 >= 0:
            feat2.write(explain2+' positively impacts prediction')
        else:
            feat2.write(explain2+' negatively impacts prediction')

        feat3 = st.expander('3. ' + explain3 + '  ' + qual_strgth3)
        feat3.write(explain3 + ': ' + str(value3))
        feat3.write('Strength: ' + str(strength3))
        if strength3 >= 0:
            feat3.write(explain3+' positively impacts prediction')
        else:
            feat3.write(explain3+' negatively impacts prediction')

    st.write('> #### House Features')

    #cleaning view df
    view_df = view_df.drop(['zip_geometry', 'exterior_image'], axis=1)
    view_df = view_df.rename(columns={'listing_id': 'Listing ID', 'price': 'Price', 'acres': 'Acres', 'bathrooms': 'Bath', 'bedrooms': 'Bed', 'car_garage': 'Car Garage', 'patios': 'Patios', 'sq_ft': 'Sq. Footage', 'cooling': 'Cooling', 'elementary': 'Elementary School', 'flooring': 'Floors', 'roof_type': 'Roofing', 'year_built': 'Build Year', 'amenities': 'Amenities', 'sold_date': 'Sold Date'})
    view_df['Patios'] = view_df['Patios'].fillna(-1)
    view_df['Patios'] = view_df['Patios'].astype(int)
    view_df['Patios'] = view_df['Patios'].astype(str)
    view_df['Patios'] = view_df['Patios'].replace('-1', np.nan)
    view_df['Car Garage'] = view_df['Car Garage'].fillna(-1)
    view_df['Car Garage'] = view_df['Car Garage'].astype(int)
    view_df['Car Garage'] = view_df['Car Garage'].astype(str)
    view_df['Car Garage'] = view_df['Car Garage'].replace('-1', np.nan)
    view_df['Sq. Footage'] = view_df['Sq. Footage'].fillna(-1)
    view_df['Sq. Footage'] = view_df['Sq. Footage'].astype(int)
    view_df['Sq. Footage'] = view_df['Sq. Footage'].astype(str)
    view_df['Sq. Footage'] = view_df['Sq. Footage'].replace('-1', np.nan)
    view_df['Bed'] = view_df['Bed'].fillna(-1)
    view_df['Bed'] = view_df['Bed'].astype(int)
    view_df['Bed'] = view_df['Bed'].astype(str)
    view_df['Bed'] = view_df['Bed'].replace('-1', np.nan)
    
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
    price_filt = st.selectbox('Filter by price', ['40000 - 100000', '100000 - 250000', '250000 - 500000', '500000 - 750000', '750000 - 1000000', '1000000 - 1500000', '1500000 - 2000000'], index=3 )
    sqft_filt = st.selectbox('Filter by square footage', ['500 - 1000', '1000 - 1500', '1500 - 2000', '2000 - 3000', '3000 - 4000', '4000 - 5000', '5000 - 6500'], index=3)

#Removing unnecessary cols and renaming cols
df_filt = small_df.drop(['zip_geometry','exterior_image'], axis=1)
df_filt = df_filt.rename(columns={'listing_id': 'Listing ID', 'price': 'Price', 'acres': 'Acres', 'bathrooms': 'Bath', 'bedrooms': 'Bed', 'car_garage': 'Car Garage', 'patios': 'Patios', 'sq_ft': 'Sq. Footage', 'cooling': 'Cooling', 'elementary': 'Elementary School', 'flooring': 'Floors', 'roof_type': 'Roofing', 'year_built': 'Build Year', 'amenities': 'Amenities', 'sold_date': 'Sold Date'})

#Filtering by multiselect & select boxes
##df_filt = df_filt[df_filt['Bed'].isin(bed_filt)]
##df_filt = df_filt[df_filt['Bath'].isin(bath_filt)]
##df_filt = df_filt[df_filt['Car Garage'].isin(garage_filt)]
##df_filt = df_filt[df_filt['Patios'].isin(patio_filt)]

#Converting float to int
df_filt['Car Garage'] = df_filt['Car Garage'].fillna(-1)
df_filt['Car Garage'] = df_filt['Car Garage'].astype(int)
df_filt['Car Garage'] = df_filt['Car Garage'].astype(str)
df_filt['Car Garage'] = df_filt['Car Garage'].replace('-1', np.nan)
df_filt['Patios'] = df_filt['Patios'].fillna(-1)
df_filt['Patios'] = df_filt['Patios'].astype(int)
df_filt['Patios'] = df_filt['Patios'].astype(str)
df_filt['Patios'] = df_filt['Patios'].replace('-1', np.nan)

st.write(df_filt)


