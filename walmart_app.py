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
STATIC_DESCRIPTION = (
    "<p>Celebrate the arrival of your little one with our adorable Custom Baby Bodysuit, "
    "the perfect baby shower gift that will be cherished for years to come. This charming piece of "
    "baby clothing is an ideal new baby gift for welcoming a newborn into the world. Whether it's for "
    "a baby announcement, a pregnancy reveal, or a special baby shower, this baby bodysuit is sure to delight.</p>"
)
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

# === VARIATIONS DICTIONARY (your “template” mapping) ===
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
    # Fallback for single-variant listing:
    "Default Title": "Default Title"
}

# === FUNCTIONS ===

def get_token():
    """
    Retrieve OAuth token from Walmart.
    """
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
        st.error(f"❌ Error getting access token: {e}")
        return None


def build_xml(df):
    """
    Build a Walmart-compliant ItemFeed XML string from a Shopify DataFrame.
    - Always creates exactly one <Item> per handle, even if Option1 Value is "Default Title" or missing.
    - If Option1 Value is in VARIATIONS, split into size/color/sleeve; otherwise, treat as single-variant fallback.
    """
    try:
        # Ensure required columns exist (case-sensitive)
        required_cols = {
            "Title", "Handle",
            "Option1 Value", "Variant Price",
            "Variant Inventory Qty", "Image Src", "Image Position"
        }
        if not required_cols.issubset(df.columns):
            raise ValueError("Missing one or more required columns in the CSV.")

        # Create the XML root with Walmart namespace
        ns = "http://walmart.com/"
        ET.register_namespace("", ns)
        root = ET.Element("{%s}ItemFeed" % ns)

        # Group by Handle to process each product (and its variants) together
        for handle, group in df.groupby("Handle"):
            title = group["Title"].iloc[0]
            # Construct a “smart” productName that your script uses
            display_title = f"{title.split(' - ')[0]} - Baby Boy Girl Clothes Bodysuit Funny Cute"

            # Collect images for this handle; use Image Position to sort
            images = (
                group[["Image Src", "Image Position"]]
                .dropna()
                .sort_values(by="Image Position")
            )
            if images.empty:
                # Skip if no images at all (Walmart requires at least one)
                continue

            main_image = images.iloc[0]["Image Src"]
            # Generate a variantGroupId from the handle (alphanumeric, max 20 chars)
            group_id = re.sub(r"[^a-zA-Z0-9]", "", handle.lower())[:20]

            # For each row (variant) under this handle, build one <Item>
            for _, row in group.iterrows():
                raw_variant = str(row.get("Option1 Value", "")).strip()
                if raw_variant == "" or raw_variant == "Default Title":
                    # Fallback: single-variant listing
                    mapped = "Default Title"
                else:
                    mapped = VARIATIONS.get(raw_variant)
                    if mapped is None:
                        # Variation not found in your template mapping—warn and still proceed
                        st.warning(f"⚠️ Variation not mapped: '{raw_variant}', using fallback as-is.")
                        mapped = raw_variant

                # Attempt to split into size, color, sleeve (if format matches “Size Color Sleeve”)
                size = color = sleeve = ""
                parts = mapped.split(" ", 2)
                if len(parts) == 3:
                    size, color, sleeve = parts
                elif len(parts) == 2:
                    size, color = parts
                    sleeve = ""
                elif len(parts) == 1:
                    size = parts[0]
                    color = ""
                    sleeve = ""
                # else: leave all as empty strings

                price = row.get("Variant Price", 0)
                qty = int(float(row.get("Variant Inventory Qty", 1)))
                short_handle = re.sub(r"[^a-zA-Z0-9]", "", handle.lower())[:20]
                sku = f"{short_handle}-{size}{color}{sleeve.replace(' ', '')}-{random.randint(100,999)}"

                # Build the <Item> XML element
                item = ET.SubElement(root, "Item")
                ET.SubElement(item, "sku").text = sku
                ET.SubElement(item, "productName").text = display_title
                ET.SubElement(item, "productIdType").text = "GTIN"
                ET.SubElement(item, "productId").text = GTIN_PLACEHOLDER
                ET.SubElement(item, "manufacturerPartNumber").text = sku
                ET.SubElement(item, "price").text = f"{price:.2f}"
                ET.SubElement(item, "brand").text = BRAND
                ET.SubElement(item, "mainImageUrl").text = main_image

                # Add up to 5 additionalImageUrl elements
                for idx, img_url in enumerate(IMAGES):
                    ET.SubElement(item, f"additionalImageUrl{idx+1}").text = img_url

                # Build the longDescription (static + bullet points)
                full_desc = STATIC_DESCRIPTION + "".join(f"<p>{b}</p>" for b in BULLETS)
                ET.SubElement(item, "longDescription").text = full_desc

                ET.SubElement(item, "fulfillmentLagTime").text = FULFILLMENT_LAG
                ET.SubElement(item, "variantGroupId").text = group_id
                ET.SubElement(item, "swatchImageUrl").text = main_image
                ET.SubElement(item, "isPreorder").text = IS_PREORDER
                ET.SubElement(item, "productType").text = PRODUCT_TYPE

                # Always include an <inventory> block with <quantity>
                inventory = ET.SubElement(item, "inventory")
                ET.SubElement(inventory, "quantity").text = str(qty)

        # Serialize the XML tree to a string
        return ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")

    except Exception as e:
        st.error(f"❌ XML generation failed: {e}")
        return None


def submit_feed(xml, token):
    """
    Submit the generated XML to Walmart and return the raw API response.
    """
    try:
        headers = {
            "WM_SVC.NAME": "Walmart Marketplace",
            "WM_QOS.CORRELATION_ID": f"submit-{random.randint(1000,9999)}",
            "Authorization": f"Bearer {token}",
            "Accept": "application/xml",
            "Content-Type": "application/xml"
        }
        res = requests.post(FEED_URL, headers=headers, data=xml)
        res.raise_for_status()
        return res.text
    except Exception as e:
        st.error(f"❌ Submission failed: {e}")
        return None


def track_feed(feed_id, token):
    """
    Poll Walmart for the status of a previously submitted feed.
    """
    try:
        res = requests.get(
            STATUS_URL.format(feed_id),
            headers={"Authorization": f"Bearer {token}", "WM_SVC.NAME": "Walmart Marketplace"}
        )
        res.raise_for_status()
        return res.text
    except Exception as e:
        st.error(f"❌ Feed tracking failed: {e}")
        return None


# === STREAMLIT UI ===
st.set_page_config(page_title="Walmart Product Feed Uploader", layout="wide")
st.title("🛒 Walmart Product Feed Uploader (All-in-One)")

uploaded = st.file_uploader(
    "Upload your Shopify products_export.csv",
    type="csv",
    help="Make sure headers: Title, Handle, Option1 Value, Variant Price, Variant Inventory Qty, Image Src, Image Position"
)

feed_status_id = st.text_input(
    "Enter Feed ID to track status:",
    placeholder="e.g. 1234567890"
)

if uploaded:
    try:
        df = pd.read_csv(uploaded)

        # Display detected columns and a small preview, so you can verify the CSV immediately
        st.write("▶️ Detected columns:", list(df.columns))
        st.write(df.head(2))

        if st.button("🧠 Generate Walmart XML"):
            xml = build_xml(df)
            if xml:
                filename = f"walmart_feed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(xml)

                st.success("✅ XML Generated!")
                st.code(xml[:3000] + "...", language="xml")

                # Allow user to download the XML file
                with open(filename, "rb") as f_bin:
                    st.download_button("📥 Download XML", f_bin, file_name=filename)

                # Only show “Submit” button after XML is generated
                if st.button("📤 Submit to Walmart"):
                    token = get_token()
                    if token:
                        response = submit_feed(xml, token)
                        if response:
                            st.success("✅ Feed Submitted!")
                            st.code(response)

    except Exception as e:
        st.error(f"❌ Could not process CSV: {e}")

# If the user has entered a Feed ID or we have a “last feed ID” (optional), allow status‐tracking
if feed_status_id:
    if st.button("🔍 Track Feed Status"):
        token = get_token()
        if token:
            result = track_feed(feed_status_id, token)
            if result:
                st.code(result)
