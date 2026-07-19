# -*- coding: utf-8 -*-
"""
Intima Wellness — URL Slug Utilities
Converts product/category names into SEO-friendly URL slugs with
content-policy-safe word mappings.
"""

import re
import unicodedata


# Content-policy word replacement mapping
# These ensure URLs avoid flagged words by adult-content payment processors and ad networks.
DISALLOWED_WORD_MAP = {
    "sex": "wellness",
    "porn": "educational",
    "adult toys": "intimate care",
    "vibrator": "personal-massager",
    "dildo": "wellness-device",
    "masturbator": "personal-massager",
    "fleshlight": "personal-sleeve",
    "blow-up": "inflatable",
    "xxx": "adult",
    "erotic": "intimate",
    "bondage": "restraint",
    "bdsm": "couples-accessories",
    "fetish": "specialty",
    "kinky": "playful",
}


def slugify(text):
    """
    Convert a string into a URL-friendly slug.

    Example:
        "Body-Safe Silicone Massager" → "body-safe-silicone-massager"
        "Luxury Glass Dildo Set" → "luxury-glass-wellness-device-set"

    Steps:
        1. Replace disallowed words using DISALLOWED_WORD_MAP (case-insensitive)
        2. Normalize unicode characters (remove accents)
        3. Convert to lowercase
        4. Replace spaces and punctuation with hyphens
        5. Collapse multiple hyphens
        6. Strip leading/trailing hyphens
    """
    if not text:
        return ""

    # Step 1: Replace disallowed words (order by length descending to avoid partial matches)
    sorted_map = sorted(DISALLOWED_WORD_MAP.items(), key=lambda x: len(x[0]), reverse=True)

    # Build a case-insensitive regex
    for bad_word, replacement in sorted_map:
        pattern = re.compile(re.escape(bad_word), re.IGNORECASE)
        text = pattern.sub(replacement, text)

    # Step 2: Normalize unicode (decompose accented chars → ASCII base)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # Step 3: Lowercase
    text = text.lower()

    # Step 4: Replace non-alphanumeric characters with hyphens
    text = re.sub(r"[^a-z0-9]+", "-", text)

    # Step 5: Collapse multiple hyphens
    text = re.sub(r"-{2,}", "-", text)

    # Step 6: Strip leading/trailing hyphens
    text = text.strip("-")

    return text


def generate_product_url(product):
    """
    Generate a full product URL path.

    Args:
        product: A dict-like or object with 'name'/'id' or 'web_id' attributes.

    Returns:
        String like "/product/slug-{product_id}"

    Example:
        {"name": "Body-Safe Silicone Massager", "id": "abc123"}
        → "/product/body-safe-silicone-massager-abc123"
    """
    product_id = _get_id(product)
    name = _get_name(product)
    slug = slugify(name)
    return f"/product/{slug}-{product_id}"


def generate_category_url(category):
    """
    Generate a full category URL path.

    Args:
        category: A dict-like or object with 'name' or 'en' attributes.

    Returns:
        String like "/category/slug"

    Example:
        {"name": "Personal Massagers"}
        → "/category/personal-massagers"
    """
    name = _get_name(category)
    slug = slugify(name)
    return f"/category/{slug}"


def _get_name(obj):
    """Extract name from dict or object."""
    if isinstance(obj, dict):
        return obj.get("name", obj.get("en", ""))
    return getattr(obj, "name", getattr(obj, "en", ""))


def _get_id(obj):
    """Extract ID from dict or object."""
    if isinstance(obj, dict):
        return str(obj.get("id", obj.get("web_id", obj.get("_id", ""))))
    return str(getattr(obj, "id", getattr(obj, "web_id", "")))
