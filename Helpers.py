from collections import defaultdict

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


@st.cache(allow_output_mutation=True)
def read_data(path):
    df = pd.read_csv(path).loc[lambda x: ~pd.isna(x.bedrooms)]
    st.session_state["base_data"] = df
    return df


def plot_choropleth(geo_df, geo_json, color_column):
    fig = px.choropleth_mapbox(
        geo_df,
        geojson=geo_json,
        color=color_column,
        locations="Map ID",
        featureidkey="properties.id_col",
        center={"lat": 40.7608, "lon": -110.8910},
        mapbox_style="carto-positron",
        zoom=5,
        labels={"price_per_sq_ft": "Price per Sq. Foot"},
    )
    return st.plotly_chart(fig)


def prediction_variables(df, zip_df):
    explanation_dict = {}

    for i in range(1, 4):
        explanation_dict[i - 1] = {}
        explanation_dict[i - 1]["expl"] = clean_string(
            df[f"EXPLANATION_{i}_FEATURE_NAME"].iloc[0]
        )
        explanation_dict[i - 1]["value"] = df[f"EXPLANATION_{i}_ACTUAL_VALUE"].iloc[0]
        explanation_dict[i - 1]["str"] = df[f"EXPLANATION_{i}_STRENGTH"].iloc[0]
        explanation_dict[i - 1]["qual_str"] = df[
            f"EXPLANATION_{i}_QUALITATIVE_STRENGTH"
        ].iloc[0]
        print(explanation_dict[i - 1]["expl"])
        if explanation_dict[i - 1]["expl"] == "Zip Geometry ":
            import pdb

            pdb.set_trace()
            geometry = str(df["zip_geometry"].iloc[0])
            explanation_dict[i - 1]["expl"] = zip_df.loc[
                geometry == zip_df["zip_geometry"].astype(str), "Map ID"
            ]
            explanation_dict[i - 1]["value"] = zip_df.loc[
                geometry == zip_df["zip_geometry"].astype(str), "price_per_sq_ft"
            ]
            print("Excecuted")
    return explanation_dict


def clean_columns(df, column_name):
    df = df.copy()

    df[column_name] = df[column_name].fillna(-1)
    df[column_name] = df[column_name].astype(int)
    df[column_name] = df[column_name].astype(str)
    df[column_name] = df[column_name].replace("-1", np.nan)

    return df[column_name]


def clean_string(explanation):
    string_array = explanation.split("_")
    temp_string = ""

    for count, i in enumerate(string_array):
        string_array[count] = i.capitalize()
        temp_string = temp_string + string_array[count] + " "

    clean_str = temp_string
    return clean_str


def filter_range(df, range, column_name):
    if range == "ANY":
        return df

    range_arr = range.split(" - ")
    low_range = int(range_arr[0])
    high_range = int(range_arr[1])
    range_check = (df[column_name] >= low_range) & (df[column_name] <= high_range)

    return df.loc[range_check]


def make_explanation_from_json(json, dict, zip):
    explanations_dict = {}
    for i in range(3):
        explanations_dict[i] = {}
        explanations_dict[i]["expl"] = clean_string(json[0][dict][i]["feature"])
        explanations_dict[i]["value"] = json[0][dict][i]["featureValue"]
        explanations_dict[i]["str"] = json[0][dict][i]["strength"]
        explanations_dict[i]["qual_str"] = json[0][dict][i]["qualitativeStrength"]

        if explanations_dict[i]["expl"] == "Zip Geometry ":
            geo = explanations_dict[i]["value"]
            explanations_dict[i]["expl"] = zip.loc[geo == zip["zip_geometry"], "Map ID"]
            explanations_dict[i]["value"] = zip.loc[
                geo == zip["zip_geometry"], "price_per_sq_ft"
            ]

    return explanations_dict


def get_explanatory_data(json_response):
    explanations = defaultdict(list)
    pred_explanations = json_response[0]["predictionExplanations"]

    for i in range(3):
        feature = pred_explanations[i]["feature"]
        value = pred_explanations[i]["featureValue"]
        strength = pred_explanations[i]["strength"]
        value = (
            value
            if feature != "zip_geometry"
            else "High Cost Zipcode"
            if strength >= 0
            else "Low Cost Zipcode"
        )
        feature = clean_string(feature)

        explanations["feature"].append(feature)
        explanations["value"].append(value)
        explanations["strength"].append(strength)
        explanations["qual_strength"].append(
            pred_explanations[i]["qualitativeStrength"]
        )
    return explanations


def write_explanations(container, container_title, exp_dict):
    container_title.write("> ### Prediction Explanations")

    with container:
        st.write(
            "#### Showing the 3 features with the largest impact on your prediction:"
        )
        exp1, exp2, exp3 = st.columns(3, gap="medium")

        with exp1:
            feat1 = st.expander(
                f"1. {exp_dict['feature'][0]} {exp_dict['qual_strength'][0]}"
            )
            feat1.write(f"{exp_dict['feature'][0]}: {exp_dict['value'][0]}")
            feat1.write(f"Strength: {exp_dict['strength'][0]}")

            if exp_dict["strength"][0] >= 0:
                feat1.write(f"{exp_dict['feature'][0]} positively impacts prediction")
            else:
                feat1.write(f"{exp_dict['feature'][0]} negatively impacts prediction")

        with exp2:
            feat2 = st.expander(
                f"2. {exp_dict['feature'][1]} {exp_dict['qual_strength'][1]}"
            )
            feat2.write(f"{exp_dict['feature'][1]}: {exp_dict['value'][1]}")
            feat2.write(f"Strength: {exp_dict['strength'][1]}")

            if exp_dict["strength"][1] >= 0:
                feat2.write(f"{exp_dict['feature'][1]} positively impacts prediction")
            else:
                feat2.write(f"{exp_dict['feature'][1]} negatively impacts prediction")

        with exp3:
            feat3 = st.expander(
                f"3. {exp_dict['feature'][2]} {exp_dict['qual_strength'][2]}"
            )
            feat3.write(f"{exp_dict['feature'][2]}: {exp_dict['value'][2]}")
            feat3.write(f"Strength: {exp_dict['strength'][2]}")

            if exp_dict["strength"][2] >= 0:
                feat3.write(f"{exp_dict['feature'][2]} positively impacts prediction")
            else:
                feat3.write(f"{exp_dict['feature'][2]} negatively impacts prediction")
        return


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
        symbol="is_New",
    )
