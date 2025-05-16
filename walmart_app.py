import streamlit as st
import pandas as pd
import random
import re
import requests
import xml.etree.ElementTree as ET
from io import BytesIO

# === WALMART API CREDENTIALS ===
CLIENT_ID = st.secrets["WALMART_CLIENT_ID"]
CLIENT_SECRET = st.secrets["WALMART_CLIENT_SECRET"]

# === UI SETUP ===
st.set_page_config(page_title="Walmart API Uploader", layout="wide")
st.title("Walmart Direct API Product Uploader")
st.markdown("Upload your Shopify CSV file. We'll format and push your products directly to Walmart via API.")

# === FILE UPLOAD ===
uploaded_file = st.file_uploader("Upload your Shopify CSV", type="csv")
if not uploaded_file:
    st.stop()

# === AUTH ===
@st.cache_data(ttl=300)
def get_walmart_access_token():
    url = "https://marketplace.walmartapis.com/v3/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    data = {
        "grant_type": "client_credentials"
    }
    r = requests.post(url, headers=headers, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
    if r.status_code != 200:
        st.error("Failed to authenticate with Walmart API.")
        st.stop()
    return r.json()["access_token"]

access_token = get_walmart_access_token()

# === SETUP ===
fixed_variations = {
    "Newborn White Short Sleeve": 24.99,
    "Newborn White Long Sleeve": 25.99,
    "Newborn (0-3M) Natural Short Sleeve": 26.99,
    "0-3M White Short Sleeve": 24.99,
    "0-3M White Long Sleeve": 25.99,
    "0-3M Pink Short Sleeve": 26.99,
    "0-3M Blue Short Sleeve": 26.99,
    "3-6M White Short Sleeve": 24.99,
    "3-6M White Long Sleeve": 25.99,
    "3-6M Pink Short Sleeve": 26.99,
    "3-6M Blue Short Sleeve": 26.99,
    "6-9M White Short Sleeve": 24.99,
    "6M Natural Short Sleeve": 26.99
}

forced_accessory_images = [
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/12efccc074d5a78e78e3e0be1150e85c5302d855_6fa13b1e-4e0d-40d0-ae35-4251523d5e93.jpg?v=1746713345",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/9db0001144fa518c97c29ab557af269feae90acd_22c6519e-ae87-4fc2-b0e4-35f75dac06e9.jpg?v=1746713345",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/ezgif.com-webp-to-jpg-converter.jpg?v=1746712913",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/2111f30dfd441733c577311e723de977c5c4bdce_73235f99-f321-4496-909e-6806f7ac1478.jpg?v=1746713345",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/8c9e801d190d7fcdd5d2cce9576aa8de994f16b5_c659fcfd-9bcf-4f8f-a54e-dd22c94da016.jpg?v=1746713345"
]

key_features = [
    "High-Quality Ink Printing: Vibrant, long-lasting colors thanks to DTG printing.",
    "Proudly Veteran-Owned: Designed by a veteran-owned small business.",
    "Comfort and Convenience: Soft cotton and snap closures for easy diaper changes.",
    "Perfect Baby Shower Gift: Adorable and meaningful.",
    "Versatile Sizing & Colors: Multiple options for boys and girls."
]

static_description = "Celebrate the arrival of your little one with our adorable Custom Baby Bodysuit..."

# === DATA PROCESSING ===
df = pd.read_csv(uploaded_file, low_memory=False)
df = df.dropna(subset=['Handle'])
grouped = df.groupby('Handle')

# === FEED XML GENERATOR ===
def build_walmart_item_feed(grouped):
    ns = "http://walmart.com/"
    ET.register_namespace("", ns)
    root = ET.Element("{%s}ItemFeed" % ns)

    for handle, group in grouped:
        title = group['Title'].iloc[0]
        smart_title = f"{title.split(' - ')[0]} - Baby Boy Girl Clothes Bodysuit Funny Cute"
        images = group[['Image Src', 'Image Position']].dropna().sort_values(by='Image Position')
        if images.empty:
            continue

        main_image = images.iloc[0]['Image Src']
        short_handle = re.sub(r'[^a-zA-Z0-9]', '', handle.lower())[:20]
        parent_sku = f"{short_handle}-Parent-{random.randint(100,999)}"

        for variation, price in fixed_variations.items():
            parts = variation.split()
            if len(parts) < 3:
                continue
            size = parts[0]
            color = parts[1]
            sleeve = ' '.join(parts[2:])
            child_sku = f"{short_handle}-{size}{color}{sleeve.replace(' ','')}-{random.randint(100,999)}"

            item = ET.SubElement(root, "Item")
            ET.SubElement(item, "sku").text = child_sku
            ET.SubElement(item, "productName").text = smart_title
            ET.SubElement(item, "longDescription").text = static_description
            ET.SubElement(item, "brand").text = "NOFO VIBES"
            ET.SubElement(item, "price").text = f"{price:.2f}"
            ET.SubElement(item, "mainImageUrl").text = main_image

            for i, img in enumerate(forced_accessory_images):
                ET.SubElement(item, f"additionalImageUrl{i+1}").text = img

            desc = ET.SubElement(item, "productIdentifiers")
            ET.SubElement(desc, "productIdType").text = "GTIN"
            ET.SubElement(desc, "productId").text = "000000000000"  # Use real or exempt value

            ET.SubElement(item, "category").text = "Clothing"
            ET.SubElement(item, "manufacturer").text = "NOFO VIBES"
            ET.SubElement(item, "manufacturerPartNumber").text = child_sku
            ET.SubElement(item, "fulfillmentLagTime").text = "2"
            ET.SubElement(item, "mainImageAltText").text = "Funny baby onesie design"

            kf = ET.SubElement(item, "keyFeatures")
            for feature in key_features:
                ET.SubElement(kf, "keyFeature").text = feature

            attrs = ET.SubElement(item, "additionalProductAttributes")
            ET.SubElement(attrs, "additionalProductAttribute", {"name": "Sleeve"}).text = sleeve
            ET.SubElement(attrs, "additionalProductAttribute", {"name": "Size"}).text = size
            ET.SubElement(attrs, "additionalProductAttribute", {"name": "Color"}).text = color

    return ET.tostring(root, encoding='utf-8', method='xml')

# === SUBMIT TO WALMART ===
def submit_to_walmart(xml_data, access_token):
    headers = {
        "WM_SVC.NAME": "Walmart Marketplace",
        "WM_QOS.CORRELATION_ID": "submit-" + str(random.randint(1000,9999)),
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/xml",
        "Content-Type": "application/xml"
    }

    url = "https://marketplace.walmartapis.com/v3/feeds?feedType=item"
    response = requests.post(url, headers=headers, data=xml_data)
    return response.status_code, response.text

# === RUN PROCESS ===
if st.button("Submit to Walmart API"):
    with st.spinner("Building Walmart feed and uploading..."):
        xml_feed = build_walmart_item_feed(grouped)
        status, result = submit_to_walmart(xml_feed, access_token)

        if status == 202:
            st.success("✅ Walmart feed submitted successfully.")
        else:
            st.error(f"❌ Submission failed: {status}\n\n{result}")
