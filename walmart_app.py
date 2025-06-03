import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import requests
import re
import random
from datetime import datetime

# === WALMART API CREDENTIALS ===
CLIENT_ID = "8206856f-c686-489f-b165-aa2126817d7c"
CLIENT_SECRET = "APzv6aIPN_ss3AzSFPPTmprRanVeHtacgjIXguk99PqwJCgKx9OBDDVuPBZ8kmr1jh2BCGpq2pLSTZDeSDg91Oo"

# === CONSTANTS ===
BRAND = "NOFO VIBES"
FULFILLMENT_LAG = "2"
PRODUCT_TYPE = "Clothing"
GTIN_PLACEHOLDER = "000000000000"
IS_PREORDER = "No"
STATIC_DESCRIPTION = "<p>Celebrate the arrival of your little one...</p>"
FEED_URL = "https://marketplace.walmartapis.com/v3/feeds?feedType=item"
STATUS_URL = "https://marketplace.walmartapis.com/v3/feeds/{}"

BULLETS = [
    "🎨 <strong>High-Quality Ink Printing:</strong> Our Baby Bodysuit features vibrant, long-lasting colors thanks to direct-to-garment printing, ensuring that your baby's outfit looks fantastic wash after wash.",
    "🎖️ <strong>Proudly Veteran-Owned:</strong> Show your support for our heroes while dressing your little one in style with this adorable newborn romper from a veteran-owned small business.",
    "👶 <strong>Comfort and Convenience:</strong> Crafted from soft, breathable materials, this Bodysuit provides maximum comfort for your baby. Plus, the convenient snap closure makes diaper changes a breeze.",
    "🎁 <strong>Perfect Baby Shower Gift:</strong> This funny Baby Bodysuit makes for an excellent baby shower gift or a thoughtful present for any new parents. It's a sweet and meaningful addition to any baby's wardrobe.",
    "📏 <strong>Versatile Sizing & Colors:</strong> Available in a range of sizes and colors, ensuring the perfect fit. Check our newborn outfit boy and girl sizing guide to find the right one for your little one."
]

IMAGES = [
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/12efccc.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/9db0001.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/ezgif.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/2111f30.jpg",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/8c9e801.jpg"
]

VARIATIONS = {
    "Newborn White Short Sleeve": "Newborn White Short Sleeve",
    "Newborn Natural Short Sleeve": "Newborn Natural Short Sleeve",
    "Newborn White Long Sleeve": "Newborn White Long Sleeve",
    "0-3M White Long Sleeve": "0-3M White Long Sleeve",
    "3-6M White Long Sleeve": "3-6M White Long Sleeve",
    "0-3M White Short Sleeve": "0-3M White Short Sleeve",
    "0-3M Pink Short Sleeve": "0-3M Pink Short Sleeve",
    "0-3M Blue Short Sleeve": "0-3M Blue Short Sleeve",
    "3-6M White Short Sleeve": "3-6M White Short Sleeve",
    "3-6M Pink Short Sleeve": "3-6M Pink Short Sleeve",
    "3-6M Blue Short Sleeve": "3-6M Blue Short Sleeve",
    "6M Natural Short Sleeve": "6M Natural Short Sleeve",
    "6-9M White Short Sleeve": "6-9M White Short Sleeve",
    "12M White Short Sleeve": "12M White Short Sleeve",
}

# === FUNCTIONS ===
def get_token():
    try:
        res = requests.post(
            "https://marketplace.walmartapis.com/v3/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials"},
            auth=(CLIENT_ID, CLIENT_SECRET)
        )
        res.raise_for_status()
        return res.json()["access_token"]
    except Exception as e:
        st.error(f"❌ Error getting access t
