# Walmart CSV Generator – NOFO VIBES

This is a Streamlit web app that converts your Shopify product export into a Walmart-ready CSV file.  
Designed specifically for NOFO VIBES baby bodysuit listings with GTIN exemption.

---

### ✅ Features

- Upload your Shopify `products_export.csv`
- Automatically generates:
  - Walmart-compliant parent/child SKUs
  - Proper variation mapping (Size, Color, Sleeve)
  - Image structure with static alt images
  - Smart product titles (Amazon-style)
- Download a final `.csv` file ready for manual upload to Walmart Seller Center

---

### 📦 Requirements

```bash
pip install -r requirements.txt
