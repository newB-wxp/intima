#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intima Wellness — Dynamic Sitemap Generator
Generates sitemap.xml and sitemap-products.xml for SEO.
"""

import os
import json
import sys
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, ElementTree

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")
CONTENT_DIR = os.path.join(PROJECT_ROOT, "content")
BLOG_POSTS_FILE = os.path.join(CONTENT_DIR, "blog", "posts.json")

BASE_URL = os.environ.get("SITE_URL", "https://YOUR_DOMAIN")

PRIORITIES = {"product": "0.8", "category": "0.9", "blog": "0.6", "static": "0.5", "home": "1.0"}
CHANGEFREQ = {"product": "weekly", "category": "weekly", "blog": "monthly", "static": "monthly", "home": "daily"}


def get_lastmod():
    return datetime.utcnow().strftime("%Y-%m-%d")


def make_url(parent, loc, lastmod, cf, pri):
    url = SubElement(parent, "url")
    SubElement(url, "loc").text = loc
    SubElement(url, "lastmod").text = lastmod
    SubElement(url, "changefreq").text = cf
    SubElement(url, "priority").text = pri


def get_static_pages():
    return [
        {"slug": "", "type": "home"},
        {"slug": "about", "type": "static"},
        {"slug": "privacy", "type": "static"},
        {"slug": "terms", "type": "static"},
        {"slug": "returns", "type": "static"},
        {"slug": "shipping", "type": "static"},
        {"slug": "faq", "type": "static"},
        {"slug": "blog", "type": "blog"},
    ]


def get_categories():
    slugs = [
        "personal-massagers", "quiet-massagers", "travel-size-devices",
        "beginner-friendly", "waterproof-devices", "usb-rechargeable",
        "couples-wellness", "glass-collection", "metal-collection",
        "silicone-collection", "luxury-collection", "wellness-kits",
        "accessories", "new-arrivals", "best-sellers", "sale",
    ]
    return [{"slug": s, "type": "category"} for s in slugs]


def get_blog_posts():
    posts = []
    if os.path.exists(BLOG_POSTS_FILE):
        with open(BLOG_POSTS_FILE, "r", encoding="utf-8") as f:
            for post in json.load(f):
                posts.append({"slug": post.get("id", ""), "type": "blog"})
    return posts


def get_products():
    products = []
    try:
        sys.path.insert(0, PROJECT_ROOT)
        from application import models as Models
        from application.app import create_app
        app = create_app()
        with app.app_context():
            for item in Models.Item.objects(status="PUBLISHED").only("web_id"):
                products.append({"slug": str(item.web_id), "type": "product"})
    except Exception:
        pass
    return products


def build_sitemap(pages, categories, posts, products):
    urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    lm = get_lastmod()
    for p in pages:
        loc = BASE_URL if not p["slug"] else f"{BASE_URL}/{p['slug']}"
        make_url(urlset, loc, lm, CHANGEFREQ.get(p["type"], "monthly"), PRIORITIES.get(p["type"], "0.5"))
    for c in categories:
        make_url(urlset, f"{BASE_URL}/category/{c['slug']}", lm, CHANGEFREQ["category"], PRIORITIES["category"])
    for bp in posts:
        make_url(urlset, f"{BASE_URL}/blog/{bp['slug']}", lm, CHANGEFREQ["blog"], PRIORITIES["blog"])
    for prod in products:
        make_url(urlset, f"{BASE_URL}/product/{prod['slug']}", lm, CHANGEFREQ["product"], PRIORITIES["product"])
    return ElementTree(urlset)


def build_product_sitemap(products):
    if not products:
        return None
    urlset = Element("urlset",
        xmlns="http://www.sitemaps.org/schemas/sitemap/0.9",
        **{"xmlns:image": "http://www.google.com/schemas/sitemap-image/1.1"})
    lm = get_lastmod()
    for p in products:
        make_url(urlset, f"{BASE_URL}/product/{p['slug']}", lm, CHANGEFREQ["product"], PRIORITIES["product"])
    return ElementTree(urlset)


def main():
    pages = get_static_pages()
    categories = get_categories()
    posts = get_blog_posts()
    products = get_products()

    tree = build_sitemap(pages, categories, posts, products)
    out = os.path.join(STATIC_DIR, "sitemap.xml")
    tree.write(out, encoding="utf-8", xml_declaration=True)
    print(f"[OK] sitemap.xml → {out}  ({len(pages)}p/{len(categories)}c/{len(posts)}b/{len(products)}pr)")

    if products:
        pt = build_product_sitemap(products)
        po = os.path.join(STATIC_DIR, "sitemap-products.xml")
        pt.write(po, encoding="utf-8", xml_declaration=True)
        print(f"[OK] sitemap-products.xml → {po}  ({len(products)} products)")


if __name__ == "__main__":
    main()
