# -*- coding: utf-8 -*-
"""
Intima Wellness — Static Pages Controller
Routes: /privacy, /terms, /returns, /shipping, /about
"""

from flask import Blueprint, render_template

static_pages = Blueprint(
    "static",
    __name__,
    template_folder="templates",
    url_prefix="/"
)


@static_pages.route("/privacy")
def privacy():
    return render_template("static/privacy.html")


@static_pages.route("/terms")
def terms():
    return render_template("static/terms.html")


@static_pages.route("/returns")
def returns():
    return render_template("static/returns.html")


@static_pages.route("/shipping")
def shipping():
    return render_template("static/shipping.html")


@static_pages.route("/about")
def about():
    return render_template("static/about.html")
