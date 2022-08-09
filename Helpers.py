import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


def read_data(path):
    df = (pd.read_csv(path)
    .loc[lambda x: ~pd.isna(x.bedrooms)]
    )
    st.session_state["base_data"] = df
    return df

def prediction_variables(df, zip_df):
    explanation_dict = {}
    for i in range(1,4):
        explanation_dict[i-1] = {}
        explanation_dict[i-1]['expl'] = clean_string(df[f'EXPLANATION_{i}_FEATURE_NAME'].iloc[0])
        explanation_dict[i-1]['value'] = df[f'EXPLANATION_{i}_ACTUAL_VALUE'].iloc[0]
        explanation_dict[i-1]['str'] = df[f'EXPLANATION_{i}_STRENGTH'].iloc[0]
        explanation_dict[i-1]['qual_str'] = df[f'EXPLANATION_{i}_QUALITATIVE_STRENGTH'].iloc[0]

        #if explanation_dict[i-1]['expl']=='Zip Geometry':
             #explanation_dict[i-1]['expl'] = zip_df[f'EXPLANATION_{i}_ACTUAL_VALUE'].iloc[0]
             #explanation_dict[i-1]['value'] = zip_df[f'EXPLANATION_{i}_ACTUAL_VALUE'].iloc[0]

    return explanation_dict

def clean_columns(df, column_name):
    df=df.copy()
    
    df[column_name] = df[column_name].fillna(-1)
    df[column_name] = df[column_name].astype(int)
    df[column_name] = df[column_name].astype(str)
    df[column_name] = df[column_name].replace('-1', np.nan)
        
    return df[column_name]    

def clean_string(explanation):
    string_array = explanation.split('_')
    temp_string = ''

    for count, i in enumerate(string_array):
        string_array[count] = i.capitalize()
        temp_string = temp_string + string_array[count] + ' '

    clean_str = temp_string
    return clean_str

def filter_range(df, range, column_name):
    if range == 'ANY':
        return df
   
    range_arr = range.split(' - ')
    low_range = int(range_arr[0])
    high_range = int(range_arr[1])
    range_check = (df[column_name]>=low_range) & (df[column_name]<=high_range) 

    return df.loc[range_check]

def make_explanation_from_json(json, dict):
    explanations_dict = {}
    for i in range(3):
        explanations_dict[i] = {}
        explanations_dict[i]['expl'] = clean_string(json[0][dict][i]['feature'])
        explanations_dict[i]['value'] = json[0][dict][i]['featureValue']
        explanations_dict[i]['str'] = json[0][dict][i]['strength']
        explanations_dict[i]['qual_str'] = json[0][dict][i]['qualitativeStrength']

    return explanations_dict



def make_plot(df, xaxis_choice):
      fig = px.scatter(
        df,
        x=xaxis_choice,
        y="price_PREDICTION",
        labels={
        "price_PREDICTION": "Predicted Price",
        "sq_ft": "Square Footage",
        "price": "Actual Price",
        "acres": "Acres",
        "bathrooms": "Bathrooms",
        "bedrooms": "Bedrooms",
        "is_New": "Predicted Home",
    },
        color="is_New",
        symbol='is_New',
    )
    

  

