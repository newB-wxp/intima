# -*- coding: utf-8 -*-
"""
Intima Wellness — Blog Controller
Routes: GET /blog (list), GET /blog/<slug> (post detail), ?category= filter
"""

import json
import os
import markdown
from flask import Blueprint, render_template, request, abort, current_app

blog = Blueprint("blog", __name__, url_prefix="/blog")

POSTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "content", "blog", "posts.json"
)
CONTENT_DIR = os.path.join(os.path.dirname(POSTS_FILE))


def _load_posts():
    """Load blog posts from JSON metadata file."""
    if not os.path.exists(POSTS_FILE):
        return []
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_post(slug):
    """Get a single post by slug."""
    posts = _load_posts()
    for p in posts:
        if p.get("id") == slug:
            return p
    return None


def _render_markdown(content_file):
    """Read and render a markdown content file to HTML."""
    md_path = os.path.join(CONTENT_DIR, content_file)
    if not os.path.exists(md_path):
        return "<p>Content coming soon.</p>"
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    return markdown.markdown(md_text, extensions=["extra", "codehilite", "toc"])


@blog.route("/")
def list_posts():
    """Blog listing page with optional category filter and pagination."""
    posts = _load_posts()
    category = request.args.get("category", "").strip()

    if category:
        posts = [p for p in posts if p.get("category") == category]

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = 9
    total = len(posts)
    total_pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    end = start + per_page
    posts_page = posts[start:end]

    # Collect unique categories for filter
    all_categories = sorted(set(p.get("category", "") for p in _load_posts() if p.get("category")))

    return render_template(
        "blog/list.html",
        posts=posts_page,
        current_category=category,
        all_categories=all_categories,
        page=page,
        total_pages=total_pages,
        total=total,
    )


@blog.route("/<slug>")
def post_detail(slug):
    """Single blog post detail page."""
    post = _get_post(slug)
    if not post:
        abort(404)

    content_html = _render_markdown(post.get("content_file", ""))

    # Get related posts (same category, excluding current)
    all_posts = _load_posts()
    related = [
        p for p in all_posts
        if p.get("category") == post.get("category") and p.get("id") != slug
    ][:3]

    return render_template(
        "blog/post.html",
        post=post,
        content_html=content_html,
        related_posts=related,
    )
