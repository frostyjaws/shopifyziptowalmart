import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import requests
import re
import random
from datetime import datetime

# === WALMART API CREDENTIALS ===
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"

# === CONSTANTS ===
BRAND = "NOFO VIBES"
FULFILLMENT_LAG = "2"
GTIN_PLACEHOLDER = "000000000000"
IS_PREORDER = "No"

STATIC_DESCRIPTION = (
    "<p>Celebrate the arrival of your little one with our adorable Custom Baby Bodysuit, "
    "the perfect baby shower gift that will be cherished for years to come. This charming piece "
    "of baby clothing is an ideal new baby gift for welcoming a newborn into the world. Whether "
    "it's for a baby announcement, a pregnancy reveal, or a special baby shower, this baby bodysuit "
    "is sure to delight.</p>"
)

STATIC_BULLETS = [
    "🎨 <strong>High-Quality Ink Printing:</strong> Our Baby Bodysuit features vibrant, long-lasting colors thanks to direct-to-garment printing.",
    "👕 <strong>Soft Cotton Fabric:</strong> Crafted from premium cotton for ultimate comfort.",
    "💧 <strong>Machine Washable:</strong> Easy to clean and maintain for busy parents.",
    "🎁 <strong>Perfect Gift:</strong> A delightful present for newborns, baby showers, and announcements.",
]

ADDITIONAL_IMAGES = [
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/12efccc074d5a78e78e3e0be1150e85c5302d855_39118440-7324-4737-a9b6-9bc4e9dab73d.jpg?v=1740931622",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/9db0001144fa518c97c29ab557af269feae90acd_32129b22-54df-4f68-8da7-30b93a0e85cc.jpg?v=1740931622",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/2111f30dfd441733c577311e723de977c5c4bdce_07aeb493-bfd6-40d8-809d-709037313156.jpg?v=1740931622",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/1a38365ed663e060d2590b04a0ec16b00004fe45_f8aaa5cc-0182-4bf8-9ada-860c6d175f25.jpg?v=1740931622"
]

def generate_walmart_xml(df):
    root = ET.Element("ItemFeed", xmlns="http://walmart.com/")

    for _, row in df.iterrows():
        item = ET.SubElement(root, "item")

        # Basic product info
        ET.SubElement(item, "sku").text = row["Handle"]
        ET.SubElement(item, "productName").text = row["Title"]
        ET.SubElement(item, "brand").text = BRAND
        ET.SubElement(item, "productIdType").text = "GTIN"
        ET.SubElement(item, "productId").text = GTIN_PLACEHOLDER
        ET.SubElement(item, "productType").text = "Infant Clothing"

        # Description and bullets
        ET.SubElement(item, "longDescription").text = STATIC_DESCRIPTION
        for bullet in STATIC_BULLETS:
            ET.SubElement(item, "keyFeatures").text = bullet

        # Images
        ET.SubElement(item, "mainImageUrl").text = row["Image Src"]
        for idx, img_url in enumerate(ADDITIONAL_IMAGES):
            ET.SubElement(item, f"additionalImageUrl{idx + 1}").text = img_url

        # Pricing and shipping
        ET.SubElement(item, "price").text = str(row["Variant Price"])
        ET.SubElement(item, "fulfillmentLagTime").text = FULFILLMENT_LAG
        ET.SubElement(item, "isPreorder").text = IS_PREORDER
        ET.SubElement(item, "isPrimaryVariant").text = "true"
        ET.SubElement(item, "variantGroupId").text = re.sub(r'[^a-zA-Z0-9]', '', row["Title"])

        # Inventory
        inventory = ET.SubElement(item, "inventory")
        ET.SubElement(inventory, "fulfillmentCenterId").text = "WFS"
        ET.SubElement(inventory, "quantity").text = "999"

    return ET.tostring(root, encoding="utf-8", method="xml").decode()

# === STREAMLIT APP ===
st.title("Walmart XML Feed Generator")

uploaded_file = st.file_uploader("Upload your Shopify CSV export", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    if "Handle" in df.columns and "Title" in df.columns and "Image Src" in df.columns and "Variant Price" in df.columns:
        xml_output = generate_walmart_xml(df)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"walmart_feed_{timestamp}.xml"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(xml_output)

        st.success("XML feed generated!")
        st.download_button(label="Download Walmart XML", data=xml_output, file_name=filename, mime="application/xml")
    else:
        st.error("Your CSV must contain the following columns: Handle, Title, Image Src, Variant Price")
