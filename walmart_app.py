import base64
import requests
from datetime import datetime
from uuid import uuid4

# --- SANDBOX CREDENTIALS ---
client_id = "a57108a5-d1fd-417a-8189-1c0f649dacb7"
client_secret = "Qns8hUf4AQskVHtjVykx4M0WPswCKW_9OS2qwlb12UInSuDjMZ1XtCXFiPT9AO47vYTyCM2_vTZQG_Ds0ZEMQg"

# --- FILE TO SUBMIT ---
xml_file_path = "walmart_feed.xml"

# --- ENCODE HEADERS ---
auth_string = f"{client_id}:{client_secret}"
auth_encoded = base64.b64encode(auth_string.encode()).decode()

# --- REQUEST HEADERS ---
headers = {
    "Accept": "application/xml",
    "Content-Type": "application/xml",
    "Authorization": f"Basic {auth_encoded}",
    "WM_SVC.NAME": "Walmart Marketplace",
    "WM_QOS.CORRELATION_ID": str(uuid4()),
    "WM_SEC.ACCESS_TOKEN": "",  # Leave empty for sandbox when using Basic Auth
    "WM_CONSUMER.ID": client_id
}

# --- API ENDPOINT ---
url = "https://marketplace.sandbox.walmartapis.com/v3/feeds?feedType=item"

# --- READ FEED FILE ---
with open(xml_file_path, "rb") as f:
    xml_payload = f.read()

# --- SUBMIT FEED ---
response = requests.post(url, headers=headers, data=xml_payload)

# --- OUTPUT RESULTS ---
print("Status Code:", response.status_code)
print("Response:")
print(response.text)
