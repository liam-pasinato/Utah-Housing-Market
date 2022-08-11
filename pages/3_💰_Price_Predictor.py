import os

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

# Import DFs
try:
    df = st.session_state["base_data"]
except KeyError:
    df = Helpers.read_data("./Data/HousingAllFeatures/HousingAllFeatures.csv")

predictions = pd.read_csv("./Data/Prediction_Explanations.csv")
price_per_sqft_df = st.session_state['ppsqft_data']

st.write("# House Price Predictor")

# Prediction form
schools = df["elementary"].unique()

# Autofill prediction form
try:
    viewing_data = st.session_state["viewing_data"]
    sqft_def = int(viewing_data["sq_ft"].iloc[0])
    car_def = viewing_data["car_garage"].iloc[0]
    bdrm_def = viewing_data["bedrooms"].iloc[0]
    patio_def = viewing_data["patios"].iloc[0]
    bath_def = viewing_data["bathrooms"].iloc[0]
    elementary_def = viewing_data["elementary"].iloc[0]

    car_def = 0 if pd.isna(car_def) else int(car_def)
    bdrm_def = 0 if pd.isna(bdrm_def) else int(bdrm_def)
    patio_def = 0 if pd.isna(patio_def) else int(patio_def)
    bath_def = 0 if pd.isna(bath_def) else int(bath_def)


except KeyError:
    sqft_def = 6000
    car_def = 1
    bdrm_def = 3
    patio_def = 1
    bath_def = 2
    elementary_def = 4

with st.form(key="MLform"):
    st.write(
        '##### Specify values and press "Get Price Prediction" to recieve a price estimation for a house with specified features:'
    )
    col1, col2, col3 = st.columns(3, gap="medium")

    # Input boxes in columns
    with col1:
        sq_ft = st.number_input(
            "Square Footage", min_value=300, max_value=33000, value=sqft_def, step=500
        )
        num_car = st.number_input(
            "Car Garage", min_value=0, max_value=30, value=car_def, step=1
        )
        st.write("###### Predictions from *DataRobot*")

    with col2:
        num_bdrm = st.number_input(
            "Bedrooms", min_value=1, max_value=12, value=bdrm_def, step=1
        )
        num_patio = st.number_input(
            "Patios", min_value=0, max_value=5, value=patio_def, step=1
        )

    with col3:
        num_bath = st.number_input(
            "Bathrooms", min_value=1, max_value=18, value=bath_def, step=1
        )
        elementary = st.selectbox("Elementary School", schools, index=4)

        submit_button = st.form_submit_button(label="Get Price Prediction")

# Containers for prediction pop-upa
loading = st.empty()
price_est = st.container().empty()
predict_expl_title = st.container().empty()
predict_expl = st.container().empty()

st.write("> ## House Price Plot")

# SelectBox for x-axis
xAxis = st.selectbox(
    "Select X-Axis:", ("sq_ft", "price", "acres", "bathrooms", "bedrooms"), index=0
)

fig1 = st.container().empty()


# On clicl 'get prediction'
if submit_button:
    try:
        predict_df = st.session_state["viewing_data"]

    except KeyError:
        rand = np.random.choice(df["listing_id"])
        predict_df = df.loc[df["listing_id"] == rand]

    # Builing prediction features DF
    predict_df = predict_df.copy()
    predict_df["sq_ft"] = sq_ft
    predict_df["bedrooms"] = num_bdrm
    predict_df["bathrooms"] = num_bath
    predict_df["car_garage"] = num_car
    predict_df["patios"] = num_patio
    predict_df["elementary"] = elementary

    df_predict_json = predict_df.to_json(orient="records")

    with loading:
        with st.spinner("Getting prediction, hang on..."):
            res = DR_Predict.make_prediction(df_predict_json, input_type="json")

    # Getting predictions & explanations from DR
    res_price = res[0]["prediction"]
    est_price = "${:,.2f}".format(res_price)
    price_est.write("## Estimated Price: " + est_price)

    explanatory_dict = Helpers.get_explanatory_data(res, price_per_sqft_df)
    st.session_state["explanations"] = explanatory_dict
    Helpers.write_explanations(predict_expl, predict_expl_title, explanatory_dict)

    # Adding prediction to DF
    predict_df["price_PREDICTION"] = res_price
    plot_df = predictions.append(predict_df)
    plot_df["is_New"] = False
    plot_df.loc[plot_df.index == plot_df.index[-1], "is_New"] = True

    st.session_state["update_graph_df"] = plot_df

    # Updated plot
    with fig1:
        fig = px.scatter(
            plot_df,
            x=xAxis,
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
        vs_title = Helpers.clean_string(xAxis)

        fig.update_layout(
            font=dict(size=16, color="Black"),
            title={
                "text": f"Predicted Price vs {vs_title}",
                "x": 0.4,
                "xanchor": "center",
                "yanchor": "top",
            },
        )

        st.plotly_chart(fig)
else:

    if st.session_state.get("explanations"):
        Helpers.write_explanations(
            predict_expl, predict_expl_title, st.session_state.get("explanations")
        )
    # Scatter plot
    with fig1:
        plotting_df = st.session_state.get(
            "update_graph_df", predictions.assign(is_New=False)
        )
        fig = px.scatter(
                plotting_df,
            x=xAxis,
            y="price_PREDICTION",
            labels={
                "price_PREDICTION": "Predicted Price",
                "sq_ft": "Square Footage",
                "price": "Actual Price",
                "acres": "Acres",
                "bathrooms": "Bathrooms",
                "bedrooms": "Bedrooms",
                "is_New": "Predicted Home"
            },
            color="is_New",
            symbol="is_New",
        )
        vs_title = Helpers.clean_string(xAxis)

        fig.update_layout(
            font=dict(size=16, color="Black"),
                title={
                    "text": f"Predicted Price vs {vs_title}",
                    "x": 0.4,
                    "xanchor": "center",
                    "yanchor": "top",
                },
        )

        st.plotly_chart(fig)
