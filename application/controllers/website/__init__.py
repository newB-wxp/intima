# -*- coding: utf-8 -*-

from . import home
from . import auth
from . import user
from . import address
from . import order
from . import cart
from . import item
from . import logistic
from . import payment
from . import post
from . import payment_webhook
from . import health
from . import blog
from . import static_pages
from . import views

website_blueprints = [
    views.views,
    home.home,
    auth.auth,
    user.user,
    address.address,
    order.order,
    cart.cart,
    item.item,
    logistic.logistic,
    payment.payment,
    post.post,
    payment_webhook.payment_webhook,
    health.health,
    blog.blog,
    static_pages.static_pages,
]
