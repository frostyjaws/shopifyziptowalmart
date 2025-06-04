import streamlit as st
import csv
import xml.etree.ElementTree as ET
import random
import os
import requests
from datetime import datetime
from io import StringIO

# ========== CONFIG ==========
CLIENT_ID = "8206856f-c686-489f-b165-aa2126817d7c"
CLIENT_SECRET = "APzv6aIPN_ss3AzSFPPTmprRanVeHtacgjIXguk99PqwJCgKx9OBDDVuPBZ8kmr1jh2BCGpq2pLSTZDeSDg91Oo"
CONSUMER_CHANNEL_TYPE = "9f3ce7f5-d168-4f2d-b7a2-e46d7a39cb17"
WALMART_FEED_URL = "https://marketplace.walmartapis.com/v3/feeds?feedType=MP_ITEM"

# ========== MASTER VARIATIONS ==========
MASTER_VARIATIONS = {
    "Newborn White Short Sleeve": 27.99,
    "Newborn White Long Sleeve": 28.99,
    "Newborn (0-3M) Natural Short Sleeve": 31.99,
    "0-3M White Short Sleeve": 27.99,
    "0-3M White Long Sleeve": 28.99,
    "0-3M Pink Short Sleeve": 31.99,
    "0-3M Blue Short Sleeve": 31.99,
    "3-6M White Short Sleeve": 27.99,
    "3-6M White Long Sleeve": 28.99,
    "3-6M Pink Short Sleeve": 31.99,
    "3-6M Blue Short Sleeve": 31.99,
    "6-9M White Short Sleeve": 27.99,
    "6M Natural Short Sleeve": 31.99
}

ADDITIONAL_IMAGE_URLS = [
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/12efccc074d5a78e78e3e0be1150e85c5302d855_39118440-7324-4737-a9b6-9bc4e9dab73d.jpg?v=1740931622",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/9db0001144fa518c97c29ab557af269feae90acd_32129b22-54df-4f68-8da7-30b93a0e85cc.jpg?v=1740931622",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/2111f30dfd441733c577311e723de977c5c4bdce_07aeb493-bfd6-40d8-809d-709037313156.jpg?v=1740931622",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/1a38365ed663e060d2590b04a0ec16b00004fe45_f8aaa5cc-0182-4bf8-9ada-860c6d175f25.jpg?v=1740931622"
]

def generate_sku(title, variation):
    base = ''.join(e for e in title if e.isalnum())[:30]
    color = next((c for c in ["White", "Pink", "Blue", "Natural"] if c in variation), "X")
    size_part = variation.split()[0]
    size = (
        size_part
        .replace("(", "")
        .replace(")", "")
        .replace("Newborn", "NB")
        .replace("6-9M", "6_9M")
        .replace("6M", "6M")
    )
    sleeve = "Long" if "Long" in variation else "Short"
    rand = random.randint(100, 999)
    return f"{base}-{size}-{color}-{sleeve}-{rand}"[:50]

def build_walmart_xml(file_content):
    tree = ET.Element("WalmartEnvelope", xmlns="http://walmart.com/")
    header = ET.SubElement(tree, "Header")
    ET.SubElement(header, "version").text = "1.4"
    ET.SubElement(header, "requestId").text = "123456789"
    ET.SubElement(header, "requestType").text = "MP_ITEM"
    feed_header = ET.SubElement(tree, "MPItemFeedHeader")
    ET.SubElement(feed_header, "locale").text = "en"
    ET.SubElement(feed_header, "sellingChannel").text = "marketplace"

    reader = csv.DictReader(StringIO(file_content.decode("utf-8")))
    for row in reader:
        title = row["Title"].strip()
        image = row["Image Src"].strip()

        for variation, price in MASTER_VARIATIONS.items():
            sku = generate_sku(title, variation)
            mp_item = ET.SubElement(tree, "MPItem")
            ET.SubElement(mp_item, "sku").text = sku
            ET.SubElement(mp_item, "productName").text = f"{title} - {variation}"
            ET.SubElement(mp_item, "productId").text = "EXEMPT"
            ET.SubElement(mp_item, "productIdType").text = "GTIN"
            ET.SubElement(mp_item, "price").text = f"{price:.2f}"
            ET.SubElement(mp_item, "productTaxCode").text = "2038710"
            ET.SubElement(mp_item, "category").text = "Baby > Apparel > Bodysuits"
            ET.SubElement(mp_item, "description").text = (
                "Celebrate the arrival of your little one with our adorable Custom Baby Bodysuit, the perfect baby shower gift that will be cherished for years to come. "
                "Made with love and care, this baby bodysuit is designed to keep your baby comfortable and stylish. Whether you're looking for a personalized baby "
                "bodysuit, a funny baby bodysuit, or a cute baby bodysuit, this Custom Baby Bodysuit has it all. It's the ideal gift for a new baby."
            )
            ET.SubElement(mp_item, "brand").text = "NOFO VIBES"
            ET.SubElement(mp_item, "mainImageUrl").text = image
            for i, url in enumerate(ADDITIONAL_IMAGE_URLS):
                ET.SubElement(mp_item, f"additionalImageUrl{i+1}").text = url
            ET.SubElement(mp_item, "shippingWeight").text = "0.2 lb"
            ET.SubElement(mp_item, "fulfillmentLagTime").text = "2"
            ET.SubElement(mp_item, "productType").text = "Clothing"
            ET.SubElement(mp_item, "minAdvertisedPrice").text = f"{price:.2f}"
            ET.SubElement(mp_item, "mustShipAlone").text = "No"
            ET.SubElement(mp_item, "quantity").text = "999"

    filename = f"walmart_feed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
    ET.ElementTree(tree).write(filename, encoding="utf-8", xml_declaration=True)
    return filename

def submit_to_walmart_api(file_path):
    token_url = "https://marketplace.walmartapis.com/v3/token"
    token_data = {"grant_type": "client_credentials"}
    token_headers = {"Accept": "application/json"}

    # Use HTTP Basic Auth as required by Walmart
    response = requests.post(token_url, data=token_data, headers=token_headers, auth=(CLIENT_ID, CLIENT_SECRET))
    if response.status_code != 200:
        return False, f"❌ Auth Failed (status {response.status_code}): {response.text}"

    token = response.json().get("access_token")
    if not token:
        return False, "❌ Auth Failed (no access_token in response)"

    headers = {
        "WM_SVC.NAME": "Walmart Marketplace",
        "WM_QOS.CORRELATION_ID": str(random.randint(100000, 999999)),
        "WM_SEC.ACCESS_TOKEN": token,
        "WM_CONSUMER.CHANNEL.TYPE": CONSUMER_CHANNEL_TYPE,
        "Accept": "application/xml",
        "Content-Type": "application/xml"
    }

    with open(file_path, "rb") as file:
        post = requests.post(WALMART_FEED_URL, data=file.read(), headers=headers)

    if post.status_code in (200, 201):
        return True, "✅ Submitted to Walmart API"
    return False, f"❌ Submission Failed (status {post.status_code}): {post.text}"

# ========== STREAMLIT UI ==========
st.set_page_config(page_title="Walmart Feed Generator", layout="centered")
st.title("🍼 Shopify → Walmart XML + API")
st.markdown("Upload a Shopify CSV → Generate XML → Submit to Walmart API")

uploaded_file = st.file_uploader("📤 Upload your Shopify product CSV", type=["csv"])
if uploaded_file:
    with st.spinner("Generating Walmart XML..."):
        try:
            output_file = build_walmart_xml(uploaded_file.read())
            with open(output_file, "rb") as f:
                st.success("✅ XML generated!")
                st.download_button(
                    "📥 Download XML",
                    f,
                    file_name=output_file,
                    mime="application/xml"
                )
            if st.button("📡 Submit to Walmart API"):
                with st.spinner("Submitting to Walmart API..."):
                    success, msg = submit_to_walmart_api(output_file)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
        except Exception as e:
            st.error(f"❌ Error while generating XML: {str(e)}")
