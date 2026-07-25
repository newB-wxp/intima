# -*- coding: utf-8 -*-

from bson import ObjectId

from wtforms import PasswordField
from wtforms import SelectMultipleField, widgets as wtf_widgets

from flask_admin.babel import gettext
from flask_admin.contrib.mongoengine.filters import BaseMongoEngineFilter
from application.extensions import admin
import application.models as Models
from . import MBModelView
from .i18n import CATEGORY_ZH


def _build_menu_choices():
    """Collect all registered admin view names, prefixed by category."""
    from application.extensions import admin
    choices = []
    for view in admin._views:
        name = view.name
        category = getattr(view, '_category', None)
        if category:
            label = '[{}] {}'.format(category, name)
        else:
            label = name
        choices.append((name, label))
    return choices


class UserView(MBModelView):
    form_subdocuments = {
        'account': {
            'form_columns': ('email',  'mobile_number', 'activation_key', 'activate_key_expire_date')
        },
    }
    # User model has heavy ListField(ReferenceField): addresses, followers,
    # followings and scala ReferenceField: default_address, cart, wallet.
    # Base MBModelView auto-excludes ListField(ReferenceField) from list.
    # Explicitly exclude remaining heavy ReferenceField from list view.
    column_exclude_list = (
        'default_address', 'cart', 'wallet',
        'password_hash', 'favor_items', 'like_posts', 'account',
        'information', 'addresses', 'followers', 'followings',
    )


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


class BackendPermissionView(MBModelView):
    form_excluded_columns = ('roles', 'menu_items')
    column_exclude_list = ('roles', 'menu_items')

    def scaffold_form(self):
        form_class = super().scaffold_form()
        role_choices = [(str(r.id), r.name) for r in Models.Role.objects.all()]
        menu_choices = _build_menu_choices()

        class _BackendPermissionForm(form_class):
            roles = SelectMultipleField(
                '所属角色',
                choices=role_choices,
                coerce=str,
                widget=wtf_widgets.ListWidget(prefix_label=False),
                option_widget=wtf_widgets.CheckboxInput(),
                description='勾选拥有此权限的角色。',
            )
            menu_items = SelectMultipleField(
                '可访问菜单',
                choices=menu_choices,
                widget=wtf_widgets.ListWidget(prefix_label=False),
                option_widget=wtf_widgets.CheckboxInput(),
                description='勾选此权限包允许访问的后台菜单模块。该权限包关联的角色登录后将只能看到被勾选的菜单。',
            )

        return _BackendPermissionForm

    def edit_form(self, obj=None):
        form = super().edit_form(obj=obj)
        if obj:
            role_ids = [str(r.id) for r in obj.roles if r is not None]
            if role_ids:
                form.roles.process_data(role_ids)
            if obj.menu_items:
                form.menu_items.process_data(obj.menu_items)
        return form

    def on_model_change(self, form, model, is_created):
        roles = []
        if form.roles.data:
            for rid in form.roles.data:
                try:
                    roles.append(Models.Role.objects.get(id=ObjectId(rid)))
                except Exception:
                    continue
        model.roles = roles
        model.menu_items = form.menu_items.data or []


class RoleView(MBModelView):
    form_extra_fields = {
        'password': PasswordField('密码'),
    }
    form_excluded_columns = ('password_hash', 'menu_permissions')
    column_exclude_list = ('password_hash',)

    def scaffold_form(self):
        form_class = super().scaffold_form()
        menu_choices = _build_menu_choices()

        class _RoleForm(form_class):
            menu_permissions = SelectMultipleField(
                '后台菜单权限',
                choices=menu_choices,
                widget=wtf_widgets.ListWidget(prefix_label=False),
                option_widget=wtf_widgets.CheckboxInput(),
                description='勾选该角色可访问的后台菜单模块。留空表示没有任何后台访问权限（仍可登录）。',
            )

        return _RoleForm

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.set_password(form.password.data)


class OrderView(MBModelView):
    """Order model has the heaviest ReferenceField footprint:
    address, entries (List), logistics (List), closed_logistics (List),
    refund_entries (List). Exclude them all from list view."""
    column_exclude_list = (
        'address', 'extra', 'discount',
        # Already excluded by base: entries, logistics, closed_logistics, refund_entries
    )
    can_create = False
    column_default_sort = ('created_at', True)


class PaymentView(MBModelView):
    """Payment has order (Ref) and logistic (Ref). Exclude from list."""
    column_exclude_list = ('order', 'logistic', 'extra')
    can_create = False
    column_default_sort = ('created_at', True)


class OrderEntryView(MBModelView):
    """OrderEntry has spec, item, _item_snapshot, _item_spec_snapshot (Ref)."""
    column_exclude_list = ('spec', 'item', '_item_snapshot', '_item_spec_snapshot')
    can_create = False


class LogisticView(MBModelView):
    """Logistic has order (Ref). ListField(Ref) auto-excluded by base."""
    column_exclude_list = ('order',)
    can_create = False


class OrderExtraView(MBModelView):
    """OrderExtra: order (Ref)."""
    column_exclude_list = ('order',)
    can_create = False


class PostCommentView(MBModelView):
    """PostComment: post (Ref)."""
    column_exclude_list = ('post',)
    can_create = False


class PostLikeView(MBModelView):
    """PostLike: post (Ref)."""
    column_exclude_list = ('post',)
    can_create = False


class PostActivityView(MBModelView):
    """PostActivity: post (Ref)."""
    column_exclude_list = ('post',)
    can_create = False


class PostFeedbackView(MBModelView):
    """PostFeedback: post (Ref)."""
    column_exclude_list = ('post',)
    can_create = False


class SocialOAuthView(MBModelView):
    """SocialOAuth: user (Ref)."""
    column_exclude_list = ('user',)
    can_create = False


# ---------------------------------------------------------------------------
# Registration — use optimized views for models with ReferenceField
# ---------------------------------------------------------------------------

admin.add_view(RoleView(Models.Role, category=CATEGORY_ZH['Admin'], name='角色'))
admin.add_view(BackendPermissionView(Models.BackendPermission, category=CATEGORY_ZH['Admin'], name='后台权限'))

admin.add_view(UserView(Models.User, category=CATEGORY_ZH['User'], endpoint='usermodel', name='用户'))
admin.add_view(SocialOAuthView(Models.SocialOAuth, category=CATEGORY_ZH['User'], name='社交登录'))
admin.add_view(MBModelView(Models.Cart, category=CATEGORY_ZH['User'], endpoint='cartmodel', name='购物车'))
admin.add_view(MBModelView(Models.EntrySpec, category=CATEGORY_ZH['User'], name='商品规格'))
admin.add_view(MBModelView(Models.Coupon, category=CATEGORY_ZH['User'], name='优惠券'))
admin.add_view(MBModelView(Models.CouponWallet, category=CATEGORY_ZH['User'], name='券包'))
admin.add_view(OrderEntryView(Models.OrderEntry, category=CATEGORY_ZH['User'], name='订单条目'))
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

admin.add_view(PaymentView(Models.Payment, category=CATEGORY_ZH['Order'], endpoint='paymentmodel', name='支付'))
admin.add_view(MBModelView(Models.LogisticProvider, category=CATEGORY_ZH['Logistics'], name='物流商'))
admin.add_view(MBModelView(Models.ChannelProvider, category=CATEGORY_ZH['Logistics'], name='渠道商'))
admin.add_view(MBModelView(Models.Partner, category=CATEGORY_ZH['Logistics'], name='合作伙伴'))
admin.add_view(OrderView(Models.Order, category=CATEGORY_ZH['Order'], name='订单'))
admin.add_view(MBModelView(Models.TransferOrderCode, category=CATEGORY_ZH['Order'], name='订单转移码'))
admin.add_view(OrderExtraView(Models.OrderExtra, category=CATEGORY_ZH['Order'], name='订单附加'))

admin.add_view(MBModelView(Models.Board, category=CATEGORY_ZH['Content'], name='看板'))
admin.add_view(MBModelView(Models.Post, category=CATEGORY_ZH['Content'], name='帖子'))
admin.add_view(PostCommentView(Models.PostComment, category=CATEGORY_ZH['Content'], name='评论'))
admin.add_view(PostLikeView(Models.PostLike, category=CATEGORY_ZH['Content'], name='点赞'))
admin.add_view(PostActivityView(Models.PostActivity, category=CATEGORY_ZH['Content'], name='动态'))
admin.add_view(PostFeedbackView(Models.PostFeedback, category=CATEGORY_ZH['Content'], name='反馈'))
admin.add_view(MBModelView(Models.PostTag, category=CATEGORY_ZH['Content'], name='帖子标签'))

# Register Logistic view — placed here to avoid circular import issues
# with the MBModelView class reference
admin.add_view(LogisticView(Models.Logistic, category=CATEGORY_ZH['Logistics'], name='物流'))
