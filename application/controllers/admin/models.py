# -*- coding: utf-8 -*-

from flask_admin.babel import gettext
from flask_admin.contrib.mongoengine.filters import BaseMongoEngineFilter
from application.extensions import admin
import application.models as Models
from . import MBModelView
from .i18n import CATEGORY_ZH


class UserView(MBModelView):
    form_subdocuments = {
        'account': {
            'form_columns': ('email',  'mobile_number', 'activation_key', 'activate_key_expire_date')
        },
    }

class LogView(MBModelView):
    can_create = False
    column_default_sort = ('created_at', True)
    column_filters = ('log_type', )

    # Chinese labels for LogView-specific fields
    column_labels = {
        'log_type': '日志类型',
    }
    form_labels = {
        'log_type': '日志类型',
    }


admin.add_view(MBModelView(Models.Role, category=CATEGORY_ZH['Admin'], name='角色'))
admin.add_view(MBModelView(Models.BackendPermission, category=CATEGORY_ZH['Admin'], name='后台权限'))

admin.add_view(UserView(Models.User, category=CATEGORY_ZH['User'], endpoint='usermodel', name='用户'))
admin.add_view(MBModelView(Models.SocialOAuth, category=CATEGORY_ZH['User'], name='社交登录'))
admin.add_view(MBModelView(Models.Cart, category=CATEGORY_ZH['User'], endpoint='cartmodel', name='购物车'))
admin.add_view(MBModelView(Models.EntrySpec, category=CATEGORY_ZH['User'], name='商品规格'))
admin.add_view(MBModelView(Models.Coupon, category=CATEGORY_ZH['User'], name='优惠券'))
admin.add_view(MBModelView(Models.CouponWallet, category=CATEGORY_ZH['User'], name='券包'))
admin.add_view(MBModelView(Models.OrderEntry, category=CATEGORY_ZH['User'], name='订单条目'))
admin.add_view(MBModelView(Models.CoinWallet, category=CATEGORY_ZH['User'], name='积分钱包'))
admin.add_view(MBModelView(Models.CoinTrade, category=CATEGORY_ZH['User'], name='积分流水'))
admin.add_view(MBModelView(Models.Address, category=CATEGORY_ZH['User'], endpoint='addressmodel', name='收货地址'))
admin.add_view(MBModelView(Models.GuestRecord, category=CATEGORY_ZH['User'], name='访客记录'))

admin.add_view(MBModelView(Models.Item, category=CATEGORY_ZH['Inventory'], endpoint='itemmodel', name='商品'))
admin.add_view(MBModelView(Models.ItemSpec, category=CATEGORY_ZH['Inventory'], name='商品规格'))
admin.add_view(MBModelView(Models.Brand, category=CATEGORY_ZH['Inventory'], name='品牌'))
admin.add_view(MBModelView(Models.Category, category=CATEGORY_ZH['Inventory'], name='分类'))
admin.add_view(MBModelView(Models.Tag, category=CATEGORY_ZH['Inventory'], name='标签'))
admin.add_view(MBModelView(Models.Vendor, category=CATEGORY_ZH['Inventory'], name='供应商'))
admin.add_view(MBModelView(Models.PriceHistory, category=CATEGORY_ZH['Inventory'], name='价格历史'))
admin.add_view(MBModelView(Models.ForexRate, category=CATEGORY_ZH['Inventory'], name='汇率'))

admin.add_view(MBModelView(Models.Payment, category=CATEGORY_ZH['Order'], endpoint='paymentmodel', name='支付'))
admin.add_view(MBModelView(Models.LogisticProvider, category=CATEGORY_ZH['Logistics'], name='物流商'))
admin.add_view(MBModelView(Models.ChannelProvider, category=CATEGORY_ZH['Logistics'], name='渠道商'))
admin.add_view(MBModelView(Models.Partner, category=CATEGORY_ZH['Logistics'], name='合作伙伴'))
admin.add_view(MBModelView(Models.Order, category=CATEGORY_ZH['Order'], name='订单'))
admin.add_view(MBModelView(Models.TransferOrderCode, category=CATEGORY_ZH['Order'], name='订单转移码'))
admin.add_view(MBModelView(Models.OrderExtra, category=CATEGORY_ZH['Order'], name='订单附加'))

admin.add_view(MBModelView(Models.Board, category=CATEGORY_ZH['Content'], name='看板'))
admin.add_view(MBModelView(Models.Post, category=CATEGORY_ZH['Content'], name='帖子'))
admin.add_view(MBModelView(Models.PostComment, category=CATEGORY_ZH['Content'], name='评论'))
admin.add_view(MBModelView(Models.PostLike, category=CATEGORY_ZH['Content'], name='点赞'))
admin.add_view(MBModelView(Models.PostActivity, category=CATEGORY_ZH['Content'], name='动态'))
admin.add_view(MBModelView(Models.PostFeedback, category=CATEGORY_ZH['Content'], name='反馈'))
admin.add_view(MBModelView(Models.PostTag, category=CATEGORY_ZH['Content'], name='帖子标签'))
