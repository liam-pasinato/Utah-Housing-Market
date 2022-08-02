import base64
import os

import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image
import requests

DEPLOYMENT_ID = st.secrets['DEPLOYMENT_ID']
API_KEY = st.secrets['API_KEY']
DATAROBOT_KEY = st.secrets['DATAROBOT_KEY']

API_URL = f'https://mlops.dynamic.orm.datarobot.com/predApi/v1.0/deployments/{DEPLOYMENT_ID}/predictions'    

def make_prediction(data: str, input_type='text') -> pd.DataFrame:
    """Uses the Prediction server to return class labels & probabilities given string representation of image
    Args:
        data (str): String representation of the Image DataFrame
    Returns:
        #TODO: Update
        List[Dict]: List of Dictionaries with returned class predictions for every image
    """
    assert input_type in ['text', 'csv', 'json']
    
    content_type = "application/json; charset=UTF-8" if input_type=='json' else "text/plain; charset=UTF-8"
    
    headers = {
        "Content-Type": content_type,
        "Authorization": "Bearer {}".format(API_KEY),
        "DataRobot-Key": DATAROBOT_KEY,
    }
    params = {
        # If explanations are required, uncomment the line below
        'maxExplanations': 3,
        # 'thresholdHigh': 0.5,
        # 'thresholdLow': 0.15,
        # Uncomment this for Prediction Warnings, if enabled for your deployment.
        # 'predictionWarningEnabled': 'true',
    }
    url = API_URL
    res = requests.post(
        url,
        data=data,
        headers=headers,
        params=params
    )
    predictions = res.json()["data"]
    return predictions


def image_to_base64(image: Image) -> str:
    """Convert a image to base64 text format for DataRobot
    https://docs.datarobot.com/en/docs/modeling/special-workflows/visual-ai/vai-predictions.html#deep-dive
    Args:
        image (Image): jpeg image
    Returns:
        str: base64 text encoding of image
    """
    img_bytes = BytesIO()
    image.save(img_bytes, "png", quality=90)
    image_base64 = base64.b64encode(img_bytes.getvalue()).decode("utf-8")
    return image_base64

def prep_image_for_scoring(img: Image) -> pd.DataFrame:
    img_resized = img.resize(
        (IMAGE_RESIZED_WIDTH, IMAGE_RESIZED_HEIGHT), Image.ANTIALIAS
    )
    b64_img = image_to_base64(img_resized)
    df = pd.DataFrame({IMAGE_COLUMN_NAME: [b64_img]})
    return df.to_string(index=False)




if __name__ == "__main__":
    df = pd.read_csv("Data/big/HousingAllFeatures.csv")
    df_filter = (df[df.index==1]
                 .drop(columns=['listing_id', 'price'])
                 # .assign(sold_date = lambda x: pd.to_datetime(x.sold_date))
                )
    image_path = list(df_filter['exterior_image'])[0]

    img = Image.open(os.path.join("Data/big", image_path))
    b64_img = image_to_base64(img)

    df_predict = df_filter.assign(exterior_image = b64_img)

    df_predict_json = df_predict.to_json(orient='records')

    # # Method 1
    # df_predict.to_csv('temp_encoded.csv',index=False)
    # data = open('temp_encoded.csv','rb').read()

    res = make_prediction(df_predict_json, input_type='json')
    print(res)