from collections import defaultdict

import geopandas as gpd
import json
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image


@st.cache(allow_output_mutation=True)
def read_data(path):
    try:
        return st.session_state["base_data"]
    except KeyError:
        df = pd.read_csv(path).loc[lambda x: ~pd.isna(x.bedrooms)]
        st.session_state["base_data"] = df
        return df

def build_map_data():
    try: 
        return st.session_state["ppsqft_data"], st.session_state["geo"]
    except KeyError:
        base_data = read_data("./Data/HousingAllFeatures/HousingAllFeatures.csv")

        color_choices = ["price", "sq_ft", "acres"]
        # Geometry is at zipcode level, should make whatever we want to plot also be at zipcode level
        df_zip_agg = (
            base_data.groupby("zip_geometry")[color_choices]
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
        st.session_state["ppsqft_data"] = average_price_per_geometry
        st.session_state["geo"] = geo_json
        return average_price_per_geometry, geo_json


def plot_choropleth(geo_df, geo_json, color_column):
    fig = px.choropleth_mapbox(
        geo_df,
        geojson=geo_json,
        color=color_column,
        locations="Map ID",
        featureidkey="properties.id_col",
        center={"lat": 40.1608, "lon": -110.8910},
        mapbox_style="carto-positron",
        zoom=4.7,
        labels={"price_per_sq_ft": "Price per Sq. Foot"},
    )

    fig.update_layout(
        font=dict(size=16, color="Black"),
        title={
            "text": "Displaying Data for Featured Zipcodes",
            "x": 0.4,
            "xanchor": "center",
            "yanchor": "top",
        },
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
        explanation_dict[i - 1]["str"] = (
            df[f"EXPLANATION_{i}_STRENGTH"].iloc[0]
        ).round(3)
        explanation_dict[i - 1]["qual_str"] = df[
            f"EXPLANATION_{i}_QUALITATIVE_STRENGTH"
        ].iloc[0]
        if explanation_dict[i - 1]["expl"] == "Zip Geometry ":

            geometry = str(df["zip_geometry"].iloc[0])

            map_id = list(
                zip_df.loc[geometry == zip_df["zip_geometry"].astype(str), "Map ID"]
            )[0]
            explanation_dict[i - 1]["expl"] = f"Map ID #{map_id} "
            pp_sqft = list(
                zip_df.loc[
                    geometry == zip_df["zip_geometry"].astype(str), "price_per_sq_ft"
                ]
            )[0]
            explanation_dict[i - 1]["value"] = f"Price/Sq. Ft - ${pp_sqft}"

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


def get_explanatory_data(json_response, zip):
    explanations = defaultdict(list)
    pred_explanations = json_response[0]["predictionExplanations"]

    for i in range(3):
        feature = pred_explanations[i]["feature"]
        value = pred_explanations[i]["featureValue"]
        strength = round(pred_explanations[i]["strength"], 3)

        if feature == "zip_geometry":
            geo = value
            map_id = list(zip.loc[geo == zip["zip_geometry"].astype(str), "Map ID"])[0]

            feature = f"Map ID #{map_id} "

            price_sqft = list(
                zip.loc[geo == zip["zip_geometry"].astype(str), "price_per_sq_ft"]
            )[0]

            value = f"Price/Sq. Ft - ${price_sqft}"

        else:
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


def write_view_explanation(real_price, est_price, img, listing, dict):
    col1, col2 = st.columns(2, gap="medium")

    with col1:
        st.write("> #### Real Price: " + "${:,.2f}".format(real_price))
        st.image(img, caption=f"Listing ID: {listing}")

    with col2:
        st.write("> #### Predicted Price: " + "${:,.2f}".format(est_price))
        st.write("##### Factors influencing house price:")

        # Explanation 1
        feat1 = st.expander(f'1. {dict[0]["expl"]} {dict[0]["qual_str"]}')
        feat1.write(f'{dict[0]["expl"]}: {dict[0]["value"]}')
        feat1.write(f'Strength: {dict[0]["str"]}')
        if dict[0]["str"] >= 0:
            feat1.write(f'{dict[0]["expl"]} positively impacts prediction')
        else:
            feat1.write(f'{dict[0]["expl"]} negatively impacts prediction')

        # Explanation 2
        feat2 = st.expander(f'2. {dict[1]["expl"]} {dict[1]["qual_str"]}')
        feat2.write(f'{dict[1]["expl"]}: {dict[1]["value"]}')
        feat2.write(f'Strength: {dict[1]["str"]}')
        if dict[1]["str"] >= 0:
            feat2.write(f'{dict[1]["expl"]} positively impacts prediction')
        else:
            feat2.write(f'{dict[1]["expl"]} negatively impacts prediction')

        # Explanation 3
        feat3 = st.expander(f'3. {dict[2]["expl"]} {dict[2]["qual_str"]}')
        feat3.write(f'{dict[2]["expl"]}: {dict[2]["value"]}')
        feat3.write(f'Strength: {dict[2]["str"]}')
        if dict[2]["str"] >= 0:
            feat3.write(f'{dict[2]["expl"]} positively impacts prediction')
        else:
            feat3.write(f'{dict[2]["expl"]} negatively impacts prediction')

    return


def title_and_logo():
    logo = Image.open("./Data/DR_logo.png")
    st.set_page_config(page_title="Utah Housing Market", page_icon=logo)
    return


def hide_streamlit_menu():
    hide_menu = """
        <style>
        #MainMenu {visibility: hidden; }
        footer {visibility: hidden;}
        </style>
        """
    st.markdown(hide_menu, unsafe_allow_html=True)
    return
