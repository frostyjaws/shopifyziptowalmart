import streamlit as st
import pandas as pd
import random
import re
from io import BytesIO

st.set_page_config(page_title="Walmart CSV Generator", layout="wide")
st.title("Walmart CSV Generator from Shopify Export")

uploaded_file = st.file_uploader("Upload your Shopify product export CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Clean variation data
    df = df.dropna(subset=['Option1 Value'])
    grouped = df.groupby('Handle')

    all_rows = []

    for handle, group in grouped:
        random_suffix = str(random.randint(100, 999))
        short_handle = re.sub(r'[^a-zA-Z0-9]', '', handle.lower())[:20]  # truncate if needed
        parent_sku = f"{short_handle}-Parent-{random_suffix}"
        title = group['Title'].iloc[0]
        description = group['Body (HTML)'].iloc[0]

        # Pull images
        images = df[df['Handle'] == handle][['Image Src', 'Image Position']].dropna()
        images = images.sort_values(by='Image Position')
        main_image = images.iloc[0]['Image Src'] if not images.empty else ''
        other_images = images['Image Src'].tolist()[1:6]

        # Add parent row (no price or image data)
        all_rows.append({
            'SKU': parent_sku,
            'Product Name': title,
            'Description': description,
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
            'Manufacturer Part Number': parent_sku
        })

        for _, row in group.iterrows():
            option = row['Option1 Value']
            parts = option.split()
            if len(parts) < 3 or pd.isna(row['Variant Price']) or not main_image:
                continue  # Skip if structure is unexpected, price or image is missing

            size = parts[0]
            color = parts[1]
            sleeve = ' '.join(parts[2:])
            price = row['Variant Price']
            sku = f"{short_handle}-{size}{color}{sleeve.replace(' ', '')}-{random_suffix}"

            all_rows.append({
                'SKU': sku,
                'Product Name': title,
                'Description': description,
                'Brand': 'NOFO VIBES',
                'Price': price,
                'Main Image URL': main_image,
                'Other Image URL1': other_images[0] if len(other_images) > 0 else '',
                'Other Image URL2': other_images[1] if len(other_images) > 1 else '',
                'Other Image URL3': other_images[2] if len(other_images) > 2 else '',
                'Other Image URL4': other_images[3] if len(other_images) > 3 else '',
                'Other Image URL5': other_images[4] if len(other_images) > 4 else '',
                'Parent SKU': parent_sku,
                'Relationship Type': 'variation',
                'Variation Theme': 'Size-Color-Sleeve',
                'Material': 'Cotton',
                'Fabric Content': '100% Cotton',
                'Country of Origin': 'Imported',
                'Gender': 'Unisex',
                'Age Group': 'Infant',
                'Manufacturer Part Number': sku
            })

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
