import streamlit as st
import pandas as pd
import random
import re
import zipfile
import os
from io import BytesIO

st.set_page_config(page_title="Walmart CSV Generator", layout="wide")
st.title("Walmart CSV Generator from Shopify Export")

uploaded_file = st.file_uploader("Upload your Shopify product export CSV", type="csv")

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

key_features = {
    'Key Features 1': '🎨 High-Quality Ink Printing: Vibrant, long-lasting colors thanks to DTG printing — your baby’s outfit stays beautiful wash after wash.',
    'Key Features 2': '🎖️ Proudly Veteran-Owned: Designed by a veteran-owned small business to bring style and heart to your baby’s wardrobe.',
    'Key Features 3': '👶 Comfort and Convenience: Soft, breathable cotton and snap closures for cozy wear and easy diaper changes.',
    'Key Features 4': '🎁 Perfect Baby Shower Gift: Makes a thoughtful gift for new parents — adorable and meaningful.',
    'Key Features 5': '📏 Versatile Sizing & Colors: Available in multiple sizes and colors for boys and girls — check the sizing guide for a perfect fit.'
}

static_description = """Celebrate the arrival of your little one with our adorable Custom Baby Bodysuit..."""

if uploaded_file:
    df = pd.read_csv(uploaded_file, low_memory=False)
    df = df.dropna(subset=['Handle'])
    grouped = df.groupby('Handle')

    all_parents = []

    for handle, group in grouped:
        title = group['Title'].iloc[0]
        smart_title = f"{title.split(' - ')[0]} - Baby Boy Girl Clothes Bodysuit Funny Cute"

        images = group[['Image Src', 'Image Position']].dropna().sort_values(by='Image Position')
        if images.empty:
            continue

        main_image = images.iloc[0]['Image Src']
        random_suffix = str(random.randint(100, 999))
        short_handle = re.sub(r'[^a-zA-Z0-9]', '', handle.lower())[:20]
        parent_sku = f"{short_handle}-Parent-{random_suffix}"

        parent_row = {
            'SKU': parent_sku,
            'Product Name': smart_title,
            'Description': static_description,
            'Brand': 'NOFO VIBES',
            'Price': '',
            'Main Image URL': '',
            'Other Image URL1': '',
            'Other Image URL2': '',
            'Other Image URL3': '',
            'Other Image URL4': '',
            'Other Image URL5': '',
            'Parent SKU': '',
            'Relationship Type': '',
            'Variation Theme': 'Size-Color-Sleeve',
            'Material': 'Cotton',
            'Fabric Content': '100% Cotton',
            'Country of Origin': 'Imported',
            'Gender': 'Unisex',
            'Age Group': 'Infant',
            'Manufacturer Part Number': parent_sku,
            'Fulfillment Lag Time': 2,
            'Product Tax Code': '2038710'
        }
        parent_row.update(key_features)
        rows = [parent_row]

        for variation, fixed_price in fixed_variations.items():
            parts = variation.split()
            if len(parts) < 3:
                continue
            size = parts[0]
            color = parts[1]
            sleeve = ' '.join(parts[2:])
            sku = f"{short_handle}-{size}{color}{sleeve.replace(' ', '')}-{random_suffix}"

            child_row = {
                'SKU': sku,
                'Product Name': smart_title,
                'Description': static_description,
                'Brand': 'NOFO VIBES',
                'Price': fixed_price,
                'Main Image URL': main_image,
                'Other Image URL1': forced_accessory_images[0],
                'Other Image URL2': forced_accessory_images[1],
                'Other Image URL3': forced_accessory_images[2],
                'Other Image URL4': forced_accessory_images[3],
                'Other Image URL5': forced_accessory_images[4],
                'Parent SKU': parent_sku,
                'Relationship Type': 'variation',
                'Variation Theme': 'Size-Color-Sleeve',
                'Material': 'Cotton',
                'Fabric Content': '100% Cotton',
                'Country of Origin': 'Imported',
                'Gender': 'Unisex',
                'Age Group': 'Infant',
                'Manufacturer Part Number': sku,
                'Fulfillment Lag Time': 2,
                'Product Tax Code': '2038710'
            }
            child_row.update(key_features)
            rows.append(child_row)

        all_parents.append(pd.DataFrame(rows))

    # Split into chunks
    batch_size = 150
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for i in range(0, len(all_parents), batch_size):
            batch_df = pd.concat(all_parents[i:i + batch_size], ignore_index=True)
            batch_df['Price'] = batch_df['Price'].astype(str)
            csv_bytes = batch_df.to_csv(index=False).encode('utf-8')
            zipf.writestr(f"walmart_upload_part{i//batch_size + 1}.csv", csv_bytes)

    st.download_button(
        label="Download Walmart Upload ZIP",
        data=zip_buffer.getvalue(),
        file_name="walmart_upload_ready.zip",
        mime="application/zip"
    )
