import numpy as np
import os
import pandas as pd
from PIL import Image
import plotly.express as px
import streamlit as st

import DR_Predict
import Helpers

# Import DFs
try:
    df = st.session_state["base_data"]
except KeyError:
    df = Helpers.read_data("./Data/HousingAllFeatures/HousingAllFeatures.csv")

predictions = pd.read_csv("./Data/Prediction_Explanations.csv")

st.write("# House Price Predictor")

# Prediction form
schools = df["elementary"].unique()

#Autofill prediction form
try: 
    viewing_data = st.session_state['viewing_data']
    sqft_def = int(viewing_data['sq_ft'].iloc[0])
    car_def = viewing_data['car_garage'].iloc[0]
    bdrm_def = viewing_data['bedrooms'].iloc[0]
    patio_def = viewing_data['patios'].iloc[0]
    bath_def = viewing_data['bathrooms'].iloc[0]
    elementary_def = viewing_data['elementary'].iloc[0]

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
        num_patio = st.number_input("Patios", min_value=0, max_value=5, value=patio_def, step=1)

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

st.write("> ### House Price Plot")

# SelectBox for x-axis
xAxis = st.selectbox(
    "Select X-Axis:", ("sq_ft", "price", "acres", "bathrooms", "bedrooms"), index=0
)

fig1 = st.container().empty()
plotting_df = st.session_state.get('update_graph_df', predictions) 
# Scatter plot
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
    },
)

fig.update_layout(
    font=dict(size=16, color="LightBlue"),
    title={"text": "Pricing Plot", "x": 0.5, "xanchor": "center", "yanchor": "top"},
)

fig.update_traces(
    marker=dict(size=10, color="blue", line=dict(width=2, color="DarkSlateGrey")),
    selector=dict(mode="markers"),
)
fig1.plotly_chart(fig)

# On clicl 'get prediction'
if submit_button:
    try: 
        predict_df = st.session_state['viewing_data']
    
    except KeyError:
        rand = np.random.choice(df["listing_id"])
        predict_df = df.loc[df["listing_id"] == rand]

    # Builing prediction features DF
    predict_df["sq_ft"] = sq_ft
    predict_df["bedrooms"] = num_bdrm
    predict_df["bathrooms"] = num_bath
    predict_df["car_garage"] = num_car
    predict_df["patios"] = num_patio
    predict_df["elementary"] = elementary

    image_path = list(predict_df["exterior_image"])[0]

    img = Image.open(os.path.join("./Data/HousingAllFeatures", image_path))
    b64_img = DR_Predict.image_to_base64(img)

    df_predict = predict_df.assign(exterior_image=b64_img)

    df_predict_json = df_predict.to_json(orient="records")


    with loading:
        with st.spinner("Getting prediction, this might take a minute..."):
            res = DR_Predict.make_prediction(df_predict_json, input_type="json")

    # Getting predictions & explanations from DR
    res_price = res[0]["prediction"]
    est_price = "${:,.2f}".format(res_price)
    price_est.write("## Estimated Price: " + est_price)

    explain1 = res[0]["predictionExplanations"][0]["feature"]
    explain2 = res[0]["predictionExplanations"][1]["feature"]
    explain3 = res[0]["predictionExplanations"][2]["feature"]

    explain1 = Helpers.clean_string(explain1)
    explain2 = Helpers.clean_string(explain2)
    explain3 = Helpers.clean_string(explain3)

    value1 = str(res[0]["predictionExplanations"][0]["featureValue"])
    value2 = str(res[0]["predictionExplanations"][1]["featureValue"])
    value3 = str(res[0]["predictionExplanations"][2]["featureValue"])
    strength1 = res[0]["predictionExplanations"][0]["strength"]
    strength2 = res[0]["predictionExplanations"][1]["strength"]
    strength3 = res[0]["predictionExplanations"][2]["strength"]
    qual_strgth1 = str(res[0]["predictionExplanations"][0]["qualitativeStrength"])
    qual_strgth2 = str(res[0]["predictionExplanations"][1]["qualitativeStrength"])
    qual_strgth3 = str(res[0]["predictionExplanations"][2]["qualitativeStrength"])

    # Adding prediction to DF
    predict_df['price_PREDICTION'] = res_price
    plot_df=predictions.append(predict_df)
    plot_df["is_New"] = False
    plot_df.loc[plot_df.index == plot_df.index[-1],'is_New']=True

    st.session_state['update_graph_df'] = plot_df

    # Removing geo data
    if explain1 == "zip_geometry":
        if strength1 >= 0:
            value1 = "Good location"
        else:
            value1 = "Bad location"
    else:
        explain1 = explain1

    if explain2 == "zip_geometry":
        if strength2 >= 0:
            value2 = "Good location"
        else:
            value2 = "Bad location"
    else:
        explain2 = explain2

    if explain3 == "zip_geometry":
        if strength3 >= 0:
            value3 = "Good location"
        else:
            value3 = "Bad location"
    else:
        explain3 = explain3

    predict_expl_title.write("> ### Prediction Explanations")

    # Show prediction explanations in 3 columns
    with predict_expl.container():
        st.write(
            "#### Showing the 3 features with the largest impact on your prediction:"
        )
        exp1, exp2, exp3 = st.columns(3, gap="medium")

        with exp1:
            feat1 = st.expander("1. " + explain1 + "  " + qual_strgth1)
            feat1.write(explain1 + ": " + value1)
            feat1.write("Strength: " + str(strength1))

            if strength1 >= 0:
                feat1.write(explain1 + " positively impacts prediction")
            else:
                feat1.write(explain1 + " negatively impacts prediction")

        with exp2:
            feat2 = st.expander("2. " + explain2 + "  " + qual_strgth2)
            feat2.write(explain2 + ": " + value2)
            feat2.write("Strength: " + str(strength2))

            if strength2 >= 0:
                feat2.write(explain2 + " positively impacts prediction")
            else:
                feat2.write(explain2 + " negatively impacts prediction")

        with exp3:
            feat3 = st.expander("3. " + explain3 + "  " + qual_strgth3)
            feat3.write(explain3 + ": " + value3)
            feat3.write("Strength: " + str(strength3))

            if strength3 >= 0:
                feat3.write(explain3 + " positively impacts prediction")
            else:
                feat3.write(explain3 + " negatively impacts prediction")

    #Updated plot
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
        symbol='is_New',
    )

    fig.update_layout(
    font=dict(size=16, color="LightBlue"),
    title={"text": "Pricing Plot", "x": 0.5, "xanchor": "center", "yanchor": "top"},
    )

    fig1.plotly_chart(fig)



