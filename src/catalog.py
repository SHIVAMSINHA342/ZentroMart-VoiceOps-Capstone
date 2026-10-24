"""Catalog lookup functions for ZentroMart synthetic product data."""

from .data_loader import load_product_catalog


def lookup_product(sku):
    sku = str(sku).strip().upper()
    catalog = load_product_catalog()

    matches = catalog[catalog["sku"].str.upper() == sku]
    if matches.empty:
        return {
            "found": False,
            "sku": sku,
            "message": "That SKU was not found in the product catalog."
        }

    row = matches.iloc[0].to_dict()
    return {
        "found": True,
        "sku": row.get("sku", ""),
        "title": row.get("title", ""),
        "brand": row.get("brand", ""),
        "category": row.get("return_category", ""),
        "price_inr": row.get("price_inr", ""),
        "fulfilled_by": row.get("fulfilled_by", ""),
        "assured": str(row.get("assured", "")).strip().lower(),
        "warranty_months": row.get("warranty_months", ""),
        "description": row.get("description", "")
    }


def find_products_by_name(query, limit=5):
    query = str(query).strip().lower()
    if not query:
        return []

    catalog = load_product_catalog()
    searchable = (
        catalog["title"].astype(str) + " " +
        catalog["brand"].astype(str) + " " +
        catalog["sku"].astype(str)
    ).str.lower()

    terms = [term for term in query.split() if len(term) > 2]
    if not terms:
        return []

    scores = searchable.apply(
        lambda text: sum(term in text for term in terms)
    )
    matches = catalog.loc[scores > 0].copy()
    matches["match_score"] = scores[scores > 0]
    matches = matches.sort_values(
        ["match_score", "sku"], ascending=[False, True]
    ).head(max(1, int(limit)))

    return [
        {
            "sku": row["sku"],
            "title": row["title"],
            "brand": row["brand"],
            "category": row["return_category"],
            "price_inr": row["price_inr"],
            "fulfilled_by": row["fulfilled_by"],
            "assured": row["assured"],
            "warranty_months": row["warranty_months"]
        }
        for _, row in matches.iterrows()
    ]
