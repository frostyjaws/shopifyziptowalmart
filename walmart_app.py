
import streamlit as st
import pandas as pd
import re
import random
from io import BytesIO

st.set_page_config(page_title="Walmart CSV Generator", layout="wide")

st.title("Walmart CSV Generator for NOFO VIBES")

uploaded_file = st.file_uploader("Upload your Shopify Export CSV", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    image_df = df[['Handle', 'Image Src', 'Image Position']].dropna()
    image_df['Image Position'] = image_df['Image Position'].astype(int)

    image_map = {}
    for handle, group in image_df.groupby('Handle'):
        main = group[group['Image Position'] == 1]['Image Src'].values[0] if 1 in group['Image Position'].values else ""
        others = group[group['Image Position'] > 1]['Image Src'].values[:5]
        image_map[handle] = {
            'main': main,
            'others': list(others)
        }

    output_rows = []
    grouped = df.dropna(subset=['Option1 Value']).groupby('Handle')
    for handle, group in grouped:
        rand_suffix = str(random.randint(100, 999))
        short_handle = re.sub(r'[^a-zA-Z0-9]', '', handle.lower())[:15]
        parent_sku = f"{short_handle}-Parent-{rand_suffix}"
        title = group['Title'].iloc[0]
        description = group['Body (HTML)'].iloc[0]
        image_data = image_map.get(handle, {"main": "", "others": []})

        output_rows.append({
            'SKU': parent_sku,
            'Product Name': title,
            'Brand': 'NOFO VIBES',
            'Description': description,
            'Gender': 'Unisex',
            'Age Group': 'Infant',
            'Material': 'Cotton',
            'Fabric Content': '100% Cotton',
            'Country of Origin': 'Imported',
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
            'Manufacturer Part Number': parent_sku,
            'Product ID': '',
            'Product ID Type': '',
            'Product ID Override': ''
        })

        for _, row in group.iterrows():
            opt_val = row['Option1 Value']
            parts = opt_val.split()
            size = parts[0]
            color = parts[1] if len(parts) > 2 else ''
            sleeve = parts[2] if len(parts) > 2 else parts[1]
            sku = f"{short_handle}-{size.replace('-', '').replace('(', '').replace(')', '')}{color}{sleeve.replace('Sleeve','')}-{rand_suffix}"
            output_rows.append({
                'SKU': sku,
                'Product Name': title,
                'Brand': 'NOFO VIBES',
                'Description': description,
                'Gender': 'Unisex',
                'Age Group': 'Infant',
                'Material': 'Cotton',
                'Fabric Content': '100% Cotton',
                'Country of Origin': 'Imported',
                'Price': row['Variant Price'],
                'Main Image URL': image_data['main'],
                'Other Image URL1': 'https://cdn.shopify.com/s/files/1/0545/2018/5017/files/12efccc074d5a78e78e3e0be1150e85c5302d855_6fa13b1e-4e0d-40d0-ae35-4251523d5e93.jpg?v=1746713345',
                'Other Image URL2': 'https://cdn.shopify.com/s/files/1/0545/2018/5017/files/9db0001144fa518c97c29ab557af269feae90acd_22c6519e-ae87-4fc2-b0e4-35f75dac06e9.jpg?v=1746713345',
                'Other Image URL3': 'https://cdn.shopify.com/s/files/1/0545/2018/5017/files/ezgif.com-webp-to-jpg-converter.jpg?v=1746712913',
                'Other Image URL4': 'https://cdn.shopify.com/s/files/1/0545/2018/5017/files/2111f30dfd441733c577311e723de977c5c4bdce_73235f99-f321-4496-909e-6806f7ac1478.jpg?v=1746713345',
                'Other Image URL5': 'https://cdn.shopify.com/s/files/1/0545/2018/5017/files/8c9e801d190d7fcdd5d2cce9576aa8de994f16b5_c659fcfd-9bcf-4f8f-a54e-dd22c94da016.jpg?v=1746713345',
                'Parent SKU': parent_sku,
                'Relationship Type': 'variation',
                'Variation Theme': 'Size-Color-Sleeve',
                'Manufacturer Part Number': sku,
                'Product ID': '',
                'Product ID Type': '',
                'Product ID Override': ''
            })

    walmart_df = pd.DataFrame(output_rows)
    st.success("Walmart file generated!")
    st.dataframe(walmart_df)

    def convert_df(df):
        output = BytesIO()
        df.to_csv(output, index=False)
        return output.getvalue()

    st.download_button(
        label="Download Walmart CSV",
        data=convert_df(walmart_df),
        file_name="walmart_upload_ready.csv",
        mime="text/csv"
    )
