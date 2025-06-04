import streamlit as st
import csv
import base64
import requests
import xml.etree.ElementTree as ET
from io import StringIO

# 🔐 SANDBOX CREDENTIALS
CLIENT_ID = "21fbdc27-d571-496e-bddb-6e99029a630d"
CLIENT_SECRET = "Y6vpggBcEWlY5OO23ewnYO2yctcPTo3m0abpoqMLWK-dklh34LyK961yTAAuTn5mGpIARtRE1qZqn-QD6V0hww"
TOKEN_URL = "https://sandbox.walmartapis.com/v3/token"
SUBMIT_FEED_URL = "https://sandbox.walmartapis.com/v3/feeds?feedType=item"

# 🔁 Your fixed variation set
VARIATIONS = {
    "Newborn White Short Sleeve": 27.99,
    "Newborn White Long Sleeve": 28.99,
    "Newborn Natural Short Sleeve": 31.99,
    "0-3M White Short Sleeve": 27.99,
    "0-3M White Long Sleeve": 28.99,
    "0-3M Pink Short Sleeve": 31.99,
    "0-3M Blue Short Sleeve": 31.99,
    "3-6M White Short Sleeve": 27.99,
    "3-6M White Long Sleeve": 28.99,
    "3-6M Pink Short Sleeve": 31.99,
    "3-6M Blue Short Sleeve": 31.99,
    "6M Natural Short Sleeve": 31.99,
    "6-9M White Short Sleeve": 27.99,
    "6-9M White Long Sleeve": 28.99,
    "6-9M Pink Short Sleeve": 31.99,
    "6-9M Blue Short Sleeve": 31.99,
    "12M White Short Sleeve": 27.99,
    "12M White Long Sleeve": 28.99,
    "12M Natural Short Sleeve": 31.99,
    "12M Pink Short Sleeve": 31.99,
    "12M Blue Short Sleeve": 31.99,
    "18M White Short Sleeve": 27.99,
    "18M White Long Sleeve": 28.99,
    "18M Natural Short Sleeve": 31.99,
    "24M White Short Sleeve": 27.99,
    "24M White Long Sleeve": 28.99,
    "24M Natural Short Sleeve": 31.99
}

# 🚪 Token retrieval with proper Basic auth
def get_walmart_token():
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}

    res = requests.post(TOKEN_URL, headers=headers, data=data)
    if res.status_code == 200:
        return res.json().get("access_token")
    else:
        st.error(f"❌ Auth Failed ({res.status_code}): {res.text}")
        return None

# 📦 Build the Walmart-compatible XML
def generate_xml(product_title):
    root = ET.Element("ItemFeed", xmlns="http://walmart.com/")

    for variant, price in VARIATIONS.items():
        item = ET.SubElement(root, "MPItem")
        sku = f"{product_title.replace(' ', '')}-{variant.replace(' ', '').replace('(', '').replace(')', '')}"
        ET.SubElement(item, "sku").text = sku
        ET.SubElement(item, "productName").text = f"{product_title} - {variant}"
        ET.SubElement(item, "productType").text = "BabyClothing"
        ET.SubElement(item, "price").text = str(price)
        ET.SubElement(item, "brand").text = "NOFO VIBES"
        ET.SubElement(item, "productIdType").text = "GTIN"
        ET.SubElement(item, "productId").text = "000000000000"
        ET.SubElement(item, "mainImageUrl").text = "https://cdn.shopify.com/sample.jpg"
        ET.SubElement(item, "shippingWeight").text = "0.3"
        ET.SubElement(item, "unit").text = "lb"

    return ET.ElementTree(root)

# 📤 Feed submission with all required headers
def submit_feed(xml_str, token):
    headers = {
        "WM_SVC.NAME": "Walmart Marketplace",
        "WM_QOS.CORRELATION_ID": "test-correlation-id",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/xml"
    }
    res = requests.post(SUBMIT_FEED_URL, headers=headers, data=xml_str)
    if res.status_code == 202:
        st.success("✅ Feed successfully submitted to Walmart Sandbox!")
        st.code(res.text)
    else:
        st.error(f"❌ Feed submission failed ({res.status_code}):\n{res.text}")

# 🌐 Streamlit UI
st.title("🍼 Walmart XML Generator (Sandbox Mode)")
uploaded = st.file_uploader("Upload your Shopify CSV", type=["csv"])

if uploaded:
    content = uploaded.read().decode("utf-8")
    reader = csv.reader(StringIO(content))
    rows = list(reader)

    if len(rows) < 2:
        st.error("❌ File missing product row.")
    else:
        title = rows[1][1].split("-")[0].strip()
        st.info(f"🧷 Title: **{title}**")

        xml_tree = generate_xml(title)
        xml_io = StringIO()
        xml_tree.write(xml_io, encoding="unicode", xml_declaration=True)
        xml_text = xml_io.getvalue()

        st.download_button("📥 Download XML", xml_text, "walmart_feed.xml")

        if st.button("🚀 Submit to Walmart Sandbox"):
            token = get_walmart_token()
            if token:
                submit_feed(xml_text, token)
