import streamlit as st
import pandas as pd
import random
import re
from io import BytesIO

st.set_page_config(page_title="Walmart CSV Generator", layout="wide")
st.title("Walmart CSV Generator from Shopify Export")

uploaded_file = st.file_uploader("Upload your Shopify product export CSV", type="csv")

# Define the 13 official variations and their fixed prices
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

# Define static accessory images
forced_accessory_images = [
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/12efccc074d5a78e78e3e0be1150e85c5302d855_6fa13b1e-4e0d-40d0-ae35-4251523d5e93.jpg?v=1746713345",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/9db0001144fa518c97c29ab557af269feae90acd_22c6519e-ae87-4fc2-b0e4-35f75dac06e9.jpg?v=1746713345",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/ezgif.com-webp-to-jpg-converter.jpg?v=1746712913",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/2111f30dfd441733c577311e723de977c5c4bdce_73235f99-f321-4496-909e-6806f7ac1478.jpg?v=1746713345",
    "https://cdn.shopify.com/s/files/1/0545/2018/5017/files/8c9e801d190d7fcdd5d2cce9576aa8de994f16b5_c659fcfd-9bcf-4f8f-a54e-dd22c94da016.jpg?v=1746713345"
]

# Define static key features (bullets)
key_features = {
    'Key Features 1': '🎨 High-Quality Ink Printing: Vibrant, long-lasting colors thanks to DTG printing — your baby’s outfit stays beautiful wash after wash.',
    'Key Features 2': '🎖️ Proudly Veteran-Owned: Designed by a veteran-owned small business to bring style and heart to your baby’s wardrobe.',
    'Key Features 3': '👶 Comfort and Convenience: Soft, breathable cotton and snap closures for cozy wear and easy diaper changes.',
    'Key Features 4': '🎁 Perfect Baby Shower Gift: Makes a thoughtful gift for new parents — adorable and meaningful.',
    'Key Features 5': '📏 Versatile Sizing & Colors: Available in multiple sizes and colors for boys and girls — check the sizing guide for a perfect fit.'
}

# Static long-form product description
static_description = """Celebrate the arrival of your little one with our adorable Custom Baby Bodysuit, the perfect baby shower gift that will be cherished for years to come. This charming piece of baby clothing is an ideal new baby gift for welcoming a newborn into the world. Whether it's for a baby announcement, a pregnancy reveal, or a special baby shower, this baby Bodysuit is sure to delight.

Our Custom Baby Bodysuit features a playful and cute design, perfect for showcasing your baby's unique personality. Made with love and care, this baby Bodysuit is designed to keep your baby comfortable and stylish. It's an essential item in cute baby clothes, making it a standout piece for any new arrival.

Perfect for both baby boys and girls, this versatile baby Bodysuit is soft, comfortable, and durable, ensuring it can withstand numerous washes. The easy-to-use snaps make changing a breeze, providing convenience for busy parents.

Whether you're looking for a personalized baby Bodysuit, a funny baby Bodysuit, or a cute baby Bodysuit, this Custom Baby Bodysuit has it all. It’s ideal for celebrating the excitement of a new baby, featuring charming and customizable designs. This makes it a fantastic option for funny baby clothes that bring a smile to everyone's face.

Imagine gifting this delightful baby Bodysuit at a baby shower or using it as a memorable baby announcement or pregnancy reveal. It’s perfect for anyone searching for a unique baby gift, announcement baby Bodysuit, or a special new baby Bodysuit. This baby Bodysuit is not just an item of clothing; it’s a keepsake that celebrates the joy and wonder of a new life.

From baby boy clothes to baby girl clothes, this baby Bodysuit is perfect for any newborn. Whether it’s a boho design, a Fathers Day gift, or custom baby clothes, this piece is a wonderful addition to any baby's wardrobe."""

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = df.dropna(subset=['Handle'])
    grouped = df.groupby('Handle')

    all_rows = []

    for handle, group in grouped:
        title = group['Title'].iloc[0]
        smart_title = f"{title.split(' - ')[0]} - Baby Boy Girl Clothes Bodysuit Funny Cute"

        images = group[['Image Src', 'Image Position']].dropna()
        images = images.sort_values(by='Image Position')
        if images.empty:
            continue

        main_image = images.iloc[0]['Image Src']
        random_suffix = str(random.randint(100, 999))
        short_handle = re.sub(r'[^a-zA-Z0-9]', '', handle.lower())[:20]
        parent_sku = f"{short_handle}-Parent-{random_suffix}"

        # Add parent row
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
        all_rows.append(parent_row)

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
            all_rows.append(child_row)

    output_df = pd.DataFrame(all_rows)
    st.success(f"Processed {len(output_df)} rows across {len(grouped)} products.")
    st.dataframe(output_df.head(50))

    # Download
    csv = output_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Walmart CSV",
        data=csv,
        file_name='walmart_upload_ready.csv',
        mime='text/csv'
    )
