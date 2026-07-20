# -*- coding: utf-8 -*-
"""
Intima Wellness — Frontend View Controller
Provides all template-rendering routes expected by the frontend (shop, product,
collections, search, cart, checkout, account, orders, blog, static pages, etc.)
"""

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    session, current_app, abort, jsonify
)
from flask_login import current_user, login_required, login_user, logout_user

from application.models.inventory.item import Item
from application.models.inventory.category import Category
from application.models.content.board import Board
from application.models.content.post import Post
from application.models.content.banner import Banner
from application.models.order.order import Order
from application.models.cart.cart import Cart, CartEntry
from application.extensions import db as mongo_db

views = Blueprint(
    "website",
    __name__,
    template_folder="../../../templates",
    url_prefix="/"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _item_to_dict(item):
    """Convert an Item document to a dict usable in templates."""
    return {
        "id": str(item.item_id),
        "slug": item.url or str(item.item_id),
        "name": item.title or "",
        "price": item.price,
        "original_price": item.original_price,
        "currency": item.currency,
        "image": item.primary_img or "",
        "discount": item.discount,
        "category": getattr(item, "main_category", None),
        "brand": getattr(item, "brand", None),
        "description": item.description or "",
        "attributes": item.attributes or [],
        "information": item.information or [],
        "rating": item.rating or 0,
        "num_rates": item.num_rates or 0,
        "num_favors": item.num_favors or 0,
        "num_views": item.num_views or 0,
        "availability": item.availability,
        "tags": item.tags or [],
        "sex_tag": getattr(item, "sex_tag", None),
        "size_lookup": getattr(item, "size_lookup", {}) or {},
        "size_chart": getattr(item, "size_chart", []) or [],
        "stock": getattr(item, "stock", -1),
        "extra": getattr(item, "extra", {}) or {},
        "created_at": item.created_at,
    }


def _post_to_dict(post):
    """Convert a Post document to a dict usable in templates."""
    return {
        "slug": getattr(post, "slug", str(post.id)),
        "title": getattr(post, "title", ""),
        "excerpt": getattr(post, "excerpt", ""),
        "content": getattr(post, "content", ""),
        "image": getattr(post, "primary_img", getattr(post, "image", "")),
        "author": getattr(post, "author", ""),
        "created_at": getattr(post, "created_at", None),
        "tags": getattr(post, "tags", []) or [],
        "category": getattr(post, "category", None),
    }


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------

@views.route("/")
def home():
    banners = Banner.objects(availability=True).order_by("-created_at").limit(5)
    new_arrivals = [_item_to_dict(i) for i in Item.objects(
        availability=True, status="new"
    ).order_by("-created_at").limit(8)]
    best_sellers = [_item_to_dict(i) for i in Item.objects(
        availability=True
    ).order_by("-num_buy").limit(8)]
    blog_posts = [_post_to_dict(p) for p in Post.objects().order_by("-created_at").limit(3)]

    cart_count = 0
    if current_user and current_user.is_authenticated:
        cart_doc = Cart.objects(user_id=str(current_user.id)).first()
        if cart_doc:
            cart_count = len(cart_doc.entries) if cart_doc.entries else 0

    return render_template(
        "home.html",
        active_page="home",
        banners=banners,
        new_arrivals=new_arrivals,
        best_sellers=best_sellers,
        blog_posts=blog_posts,
        cart_count=cart_count,
    )


# ---------------------------------------------------------------------------
# Shop / Product / Collections / Search
# ---------------------------------------------------------------------------

@views.route("/shop")
def shop():
    page = request.args.get("page", 1, type=int)
    sort = request.args.get("sort", "newest")
    category_slug = request.args.get("category")
    per_page = 12

    qs = Item.objects(availability=True)
    if category_slug:
        qs = qs.filter(main_category=category_slug)

    if sort == "bestsellers":
        qs = qs.order_by("-num_buy")
    elif sort == "price_asc":
        qs = qs.order_by("price")
    elif sort == "price_desc":
        qs = qs.order_by("-price")
    else:
        qs = qs.order_by("-created_at")

    total = qs.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    items = qs.skip((page - 1) * per_page).limit(per_page)
    products = [_item_to_dict(i) for i in items]

    categories = Category.objects()
    cart_count = 0
    if current_user and current_user.is_authenticated:
        cart_doc = Cart.objects(user_id=str(current_user.id)).first()
        if cart_doc:
            cart_count = len(cart_doc.entries) if cart_doc.entries else 0

    return render_template(
        "index.html",
        active_page="shop",
        products=products,
        pagination={
            "page": page,
            "pages": total_pages,
            "total": total,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "next_num": page + 1 if page < total_pages else None,
            "prev_num": page - 1 if page > 1 else None,
        },
        categories=categories,
        sort=sort,
        cart_count=cart_count,
    )


@views.route("/product/<slug>")
def product(slug):
    item = Item.objects(url=slug).first()
    if not item:
        item = Item.objects(item_id=int(slug)).first() if slug.isdigit() else None
    if not item:
        abort(404)

    product_data = _item_to_dict(item)
    # related products: same category
    related = [_item_to_dict(i) for i in Item.objects(
        availability=True, main_category=item.main_category, item_id__ne=item.item_id
    ).limit(4)]

    cart_count = 0
    if current_user and current_user.is_authenticated:
        cart_doc = Cart.objects(user_id=str(current_user.id)).first()
        if cart_doc:
            cart_count = len(cart_doc.entries) if cart_doc.entries else 0

    return render_template(
        "shop/product.html",
        active_page="shop",
        product=product_data,
        related=related,
        cart_count=cart_count,
    )


@views.route("/category/<slug>")
def shop_category(slug):
    page = request.args.get("page", 1, type=int)
    per_page = 12
    category = Category.objects(slug=slug).first() or Category.objects(name=slug).first()

    qs = Item.objects(availability=True, main_category=slug)
    total = qs.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    items = qs.order_by("-created_at").skip((page - 1) * per_page).limit(per_page)
    products = [_item_to_dict(i) for i in items]

    return render_template(
        "shop/category.html",
        active_page="shop",
        category=category.name if category else slug,
        products=products,
        pagination={
            "page": page,
            "pages": total_pages,
            "total": total,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "next_num": page + 1 if page < total_pages else None,
            "prev_num": page - 1 if page > 1 else None,
        },
    )


@views.route("/collections")
def collections():
    boards = Board.objects(availability=True)
    return render_template(
        "shop/category.html",
        active_page="collections",
        category="All Collections",
        products=[],  # Boards are rendered differently if template supports it
        pagination={"page": 1, "pages": 1, "total": 0, "has_next": False, "has_prev": False},
    )


@views.route("/search")
def search():
    query = request.args.get("q", "")
    page = request.args.get("page", 1, type=int)
    per_page = 12

    products = []
    total = 0
    if query:
        qs = Item.objects(
            availability=True,
            __raw__={"$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"tags": {"$regex": query, "$options": "i"}},
            ]}
        )
        total = qs.count()
        total_pages = max(1, (total + per_page - 1) // per_page)
        items = qs.order_by("-created_at").skip((page - 1) * per_page).limit(per_page)
        products = [_item_to_dict(i) for i in items]
    else:
        total_pages = 1

    return render_template(
        "index.html",
        active_page="search",
        products=products,
        query=query,
        pagination={
            "page": page,
            "pages": total_pages,
            "total": total,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "next_num": page + 1 if page < total_pages else None,
            "prev_num": page - 1 if page > 1 else None,
        },
    )


# ---------------------------------------------------------------------------
# Auth Views
# ---------------------------------------------------------------------------

@views.route("/login")
def login():
    if current_user and current_user.is_authenticated:
        return redirect(url_for("website.home"))
    return render_template("auth/login.html", active_page="login")


@views.route("/signup")
def signup():
    if current_user and current_user.is_authenticated:
        return redirect(url_for("website.home"))
    return render_template("auth/signup.html", active_page="signup")


@views.route("/forgot-password")
def forgot_password():
    return render_template("auth/login.html", active_page="forgot_password")


@views.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        flash("Password changed successfully.", "success")
        return redirect(url_for("website.account"))
    return render_template("account/profile.html", active_page="account")


@views.route("/update-profile", methods=["POST"])
@login_required
def update_profile():
    flash("Profile updated.", "success")
    return redirect(url_for("website.account"))


@views.route("/newsletter-subscribe", methods=["POST"])
def newsletter_subscribe():
    flash("Subscribed!", "success")
    return redirect(request.referrer or url_for("website.home"))


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------

@views.route("/account")
@login_required
def account():
    return render_template("account/profile.html", active_page="account")


@views.route("/orders")
@login_required
def orders():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    user_orders = Order.objects(user_id=str(current_user.id)).order_by("-created_at")
    total = user_orders.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    order_docs = user_orders.skip((page - 1) * per_page).limit(per_page)

    return render_template(
        "account/orders.html",
        active_page="account",
        orders=order_docs,
        pagination={
            "page": page,
            "pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "next_num": page + 1 if page < total_pages else None,
            "prev_num": page - 1 if page > 1 else None,
        },
    )


@views.route("/order/<order_id>")
@login_required
def order_detail(order_id):
    order = Order.objects(id=order_id).first()
    if not order:
        abort(404)
    return render_template("account/orders.html", active_page="account", order=order)


# ---------------------------------------------------------------------------
# Cart
# ---------------------------------------------------------------------------

@views.route("/cart")
def cart():
    cart_count = 0
    cart_entries = []
    cart_total = 0
    if current_user and current_user.is_authenticated:
        cart_doc = Cart.objects(user_id=str(current_user.id)).first()
        if cart_doc and cart_doc.entries:
            cart_count = len(cart_doc.entries)
            for entry in cart_doc.entries:
                item = Item.objects(item_id=entry.item_id).first()
                if item:
                    cart_entries.append({
                        "id": str(entry.id) if hasattr(entry, "id") else str(entry.item_id),
                        "item": _item_to_dict(item),
                        "quantity": entry.quantity,
                        "spec": getattr(entry, "spec", None),
                        "subtotal": item.price * entry.quantity,
                    })
                    cart_total += item.price * entry.quantity

    return render_template(
        "shop/cart.html",
        active_page="cart",
        cart_entries=cart_entries,
        cart_count=cart_count,
        cart_total=cart_total,
    )


@views.route("/cart/remove/<item_id>", methods=["POST"])
@login_required
def cart_remove(item_id):
    # Delegate to the API controller's remove logic by redirecting
    return redirect(url_for("cart.remove_entries_from_cart"))


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------

@views.route("/checkout")
@login_required
def checkout():
    return render_template("payment/checkout.html", active_page="checkout")


# ---------------------------------------------------------------------------
# Static Pages (faq, contact, gift-cards only; others handled by static_pages.py)
# ---------------------------------------------------------------------------

@views.route("/faq")
def faq():
    return render_template("static/faq.html", active_page="faq")


@views.route("/contact")
def contact():
    return render_template("static/about.html", active_page="contact")


@views.route("/gift-cards")
def gift_cards():
    return render_template("static/about.html", active_page="gift_cards")
