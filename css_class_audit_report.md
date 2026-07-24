# CSS 类名对照审计报告

**项目**: Intima Wellness Website (bibi)  
**审计日期**: 2026-07-24  
**问题根因**: CSS (`style.css`) 使用 BEM 双下划线命名（如 `hero__title`），HTML 模板使用连字符命名（如 `hero-heading`），全站样式大面积失效。

---

## 统计概览

| 指标 | 数值 |
|---|---|
| CSS 中定义的类选择器 | 164 |
| HTML 模板中使用的唯一类名 | 328 |
| HTML 中有但 CSS 中缺失 | **262** |
| CSS 中有但 HTML 未使用 | 98 |
| 可简单改 HTML 修复（BEM 对应） | 约 35 |
| 需新增 CSS 规则 | 约 227 |

---

## 逐组件失配明细

### 1. Hero 区 (home.html)

| 当前 HTML 类名 | CSS 对应 BEM 版本 | 修复方向 |
|---|---|---|
| `hero-overlay` | 无对应 | **新增 CSS**（遮罩层） |
| `hero-content` | `hero__content` | **改 HTML** |
| `hero-heading` | `hero__title` | **改 HTML** |
| `hero-subheading` | `hero__subtitle` | **改 HTML** |
| `hero-cta` | `hero__cta` | **改 HTML** |

---

### 2. Brand Values / Value Props (home.html, about.html)

home.html 用 `value-card`/`value-icon`/`value-title`/`value-desc`/`values-grid`，  
about.html 用 `about-value-card`/`about-values-grid` 等变体。

| 当前 HTML 类名 | CSS 对应 BEM 版本 | 修复方向 |
|---|---|---|
| `values-grid` | `brand-values__grid` | **改 HTML** |
| `value-card` | `brand-value` | **改 HTML** |
| `value-icon` | `brand-value__icon` | **改 HTML** |
| `value-title` | `brand-value__title` | **改 HTML** |
| `value-desc` | `brand-value__desc` | **改 HTML** |
| `about-value-card` | 无直接对应 | **新增 CSS** 或复用 `brand-value` |
| `about-values-grid` | 无直接对应 | **新增 CSS** |
| `about-hero-content` / `about-hero-title` / `about-hero-subtitle` | 无对应 | **新增 CSS** |
| `about-mission-content` / `about-mission-text` | 无对应 | **新增 CSS** |
| `about-team-placeholder` | 无对应 | **新增 CSS** |
| `section-about-hero` / `section-about-mission` / `section-about-values` / `section-about-team` | 无对应 | **新增 CSS** |
| `section-brand-values` | 无对应 | **新增 CSS** |

---

### 3. Section 标题 (全站多文件)

CSS 定义: `section__header` / `section__title` / `section__subtitle`。  
HTML 使用: `section-heading`。

| 当前 HTML 类名 | CSS 对应 BEM 版本 | 修复方向 |
|---|---|---|
| `section-heading` | `section__title` | **改 HTML** |

HTML 中还有大量 `section-*` 变体（`section-new-arrivals`、`section-best-sellers` 等），CSS 中无对应，需逐一新增或改用 `section` 基类。

---

### 4. Product Card (product_card.html, category.html)

| 当前 HTML 类名 | CSS 对应 BEM 版本 | 修复方向 |
|---|---|---|
| `product-grid-3col` | `product-grid--3col` | **改 HTML**（单横线→双横线） |

> 注: category.html 中的 `product-grid-3col` 应改为 `product-grid--3col`。

---

### 5. Product Detail (product.html) — 重灾区

| 当前 HTML 类名 | CSS 对应 BEM 版本 | 修复方向 |
|---|---|---|
| `product-detail-gallery` | `product-detail__gallery` | **改 HTML** |
| `product-detail-main-image` | `product-detail__main-image` | **改 HTML** |
| `product-detail-thumbnails` | `product-detail__thumbnails` | **改 HTML** |
| `product-detail-thumb` | `product-detail__thumb` | **改 HTML** |
| `product-detail-info` | `product-detail__info` | **改 HTML** |
| `product-detail-name` | `product-detail__title` | **改 HTML** |
| `product-detail-price` | `product-detail__price` | **改 HTML** |
| `product-detail-description` | `product-detail__description` | **改 HTML** |
| `product-detail-img` | 无对应 | **新增 CSS** |
| `product-detail-pricing` | 无对应 | **新增 CSS** |
| `product-detail-compare-price` | 无对应 | **新增 CSS** |
| `product-detail-rating` | 无对应 | **新增 CSS** |
| `product-detail-review-count` | 无对应 | **新增 CSS** |
| `product-detail-tags` | 无对应 | **新增 CSS** |
| `product-tag` | 无对应 | **新增 CSS** |
| `product-detail-cart` | 无对应 | **新增 CSS** |
| `product-detail-extra` | 无对应 | **新增 CSS** |
| `product-description` | 无对应 | **新增 CSS** |
| `product-section-title` | 无对应 | **新增 CSS** |
| `product-description-content` | 无对应 | **新增 CSS** |
| `product-specs` | 无对应 | **新增 CSS** |
| `specs-table` | 无对应 | **新增 CSS** |
| `product-related` | 无对应 | **新增 CSS** |
| `shipping-note` | 无对应 | **新增 CSS** |
| `stars` / `star` / `star-filled` / `star-half` / `star-empty` | 无对应 | **新增 CSS** |
| `quantity-selector` / `quantity-btn` / `quantity-minus` / `quantity-plus` / `quantity-input` | 无对应 | **新增 CSS** |
| `add-to-cart-btn` | 无对应 | **新增 CSS** |
| `breadcrumb` / `breadcrumb-list` / `breadcrumb-item` / `breadcrumb-separator` | 无对应 | **新增 CSS** |

---

### 6. Blog Card (home.html, blog/list.html, blog/post.html)

| 当前 HTML 类名 | CSS 对应 BEM 版本 | 修复方向 |
|---|---|---|
| `blog-card-image` | `blog-card__image` | **改 HTML** |
| `blog-card-body` | `blog-card__body` | **改 HTML** |
| `blog-card-content` | `blog-card__body` | **改 HTML** |
| `blog-card-category` | `blog-card__category` | **改 HTML** |
| `blog-card-title` | `blog-card__title` | **改 HTML** |
| `blog-card-excerpt` | `blog-card__excerpt` | **改 HTML** |
| `blog-card-summary` | `blog-card__excerpt` | **改 HTML** |
| `blog-card-meta` | `blog-card__meta` | **改 HTML** |
| `blog-card-date` | 无对应 | **新增 CSS** 或改用 `blog-card__meta` |
| `blog-card-link` | 无对应 | **新增 CSS** |
| `blog-card-tags` / `tag` | 无对应 | **新增 CSS** |
| `blog-preview-grid` | `blog-grid` | **改 HTML** |
| `blog-list` | 无对应 | **新增 CSS** |
| `blog-filters` / `filter-btn` | 无对应 | **新增 CSS** |
| `blog-post` | 无对应 | **新增 CSS** |
| `post-header` / `post-category` / `post-meta` / `post-tags` | 无对应 | **新增 CSS** |
| `post-featured-image` | 无对应 | **新增 CSS** |
| `post-content` | 无对应 | **新增 CSS** |
| `related-posts` / `related-grid` / `related-card` | 无对应 | **新增 CSS** |
| `separator` / `current` | 无对应 | **新增 CSS** |
| `subtitle` | 无对应 | **新增 CSS** |
| `empty-state` | 无对应 | **新增 CSS** |

---

### 7. Cart (cart.html) — 重度失配

| 当前 HTML 类名 | CSS 对应 BEM 版本 | 修复方向 |
|---|---|---|
| `cart-table` | `cart__table` | **改 HTML** |
| `cart-product` | `cart__product` | **改 HTML** |
| `cart-product-image` | `cart__product-img` | **改 HTML** |
| `cart-product-name` | `cart__product-name` | **改 HTML** |
| `cart-summary` | `cart__summary` | **改 HTML** |
| `cart-summary-row` | `cart__summary-row` | **改 HTML** |
| `cart-empty` | `cart__empty` | **改 HTML** |
| `cart-header` / `cart-title` / `cart-badge-count` | 无对应 | **新增 CSS** |
| `cart-layout` / `cart-main` / `cart-table-wrapper` | 无对应 | **新增 CSS** |
| `cart-col-product` / `cart-col-price` / `cart-col-quantity` / `cart-col-subtotal` / `cart-col-remove` | 无对应 | **新增 CSS** |
| `cart-item` | 无对应 | **新增 CSS** |
| `cart-product-info` / `cart-product-variant` | 无对应 | **新增 CSS** |
| `cart-remove-btn` | 无对应 | **新增 CSS** |
| `cart-continue-link` | 无对应 | **新增 CSS** |
| `cart-coupon` / `cart-coupon-form` | 无对应 | **新增 CSS** |
| `cart-summary-card` / `cart-summary-title` | 无对应 | **新增 CSS** |
| `cart-summary-free` / `cart-summary-muted` | 无对应 | **新增 CSS** |
| `cart-summary-discount` / `cart-summary-divider` / `cart-summary-total` / `cart-summary-secure` | 无对应 | **新增 CSS** |
| `cart-empty-icon` / `cart-empty-title` / `cart-empty-text` | 无对应 | **新增 CSS** |
| `quantity-selector` / `quantity-selector-sm` / `quantity-btn` / `quantity-minus` / `quantity-plus` / `quantity-input` | 无对应 | **新增 CSS** |

---

### 8. Category Page (category.html)

| 当前 HTML 类名 | CSS 对应 BEM 版本 | 修复方向 |
|---|---|---|
| `category-header` / `category-title` / `category-count` | 无对应 | **新增 CSS** |
| `category-layout` / `category-main` | 无对应 | **新增 CSS** |
| `category-sort` / `sort-label` | 无对应 | **新增 CSS** |
| `filter-sidebar` / `filter-panel` | 无对应 | **新增 CSS** |
| `filter-toggle-mobile` / `filter-toggle-btn` | 无对应 | **新增 CSS** |
| `filter-sort-mobile` | 无对应 | **新增 CSS** |
| `filter-group` / `filter-group-title` | 无对应 | **新增 CSS** |
| `filter-price-inputs` / `filter-price-separator` | 无对应 | **新增 CSS** |
| `filter-checkbox-list` / `checkbox-label` | 无对应 | **新增 CSS** |
| `filter-apply-btn` | 无对应 | **新增 CSS** |
| `breadcrumb` / `breadcrumb-list` / `breadcrumb-item` / `breadcrumb-separator` | 无对应 | **新增 CSS** |

---

### 9. Auth Pages (login.html, signup.html)

CSS 定义 `auth-card__title` / `auth-card__subtitle`。HTML 使用 `auth-title`。

| 当前 HTML 类名 | CSS 对应 BEM 版本 | 修复方向 |
|---|---|---|
| `auth-title` | `auth-card__title` | **改 HTML** |
| `auth-form` | 无对应 | **新增 CSS** |
| `auth-link` | 无对应 | **新增 CSS** |
| `auth-divider-text` | 无对应 | **新增 CSS** |
| `auth-footer` | 无对应 | **新增 CSS** |
| `btn-social` | 无对应 | **新增 CSS** |
| `form-row` / `form-row-between` | 无对应 | **新增 CSS** |
| `checkbox-label` / `checkbox-label-required` | 无对应 | **新增 CSS** |
| `password-strength` / `password-strength-bar` / `password-strength-bar-1` ~ `-4` | 无对应 | **新增 CSS** |

---

### 10. Profile Page (profile.html)

| 当前 HTML 类名 | CSS 对应 BEM 版本 | 修复方向 |
|---|---|---|
| `profile-layout` / `profile-card` / `profile-card-title` / `profile-form` | 无对应 | **新增 CSS** |
| `profile-oauth-list` / `profile-oauth-item` / `profile-oauth-info` | 无对应 | **新增 CSS** |
| `profile-oauth-status` / `profile-oauth-connected` | 无对应 | **新增 CSS** |
| `form-hint` | 无对应 | **新增 CSS** |
| `form-input-readonly` | 无对应 | **新增 CSS** |

---

### 11. Orders Page (orders.html)

| 当前 HTML 类名 | CSS 对应 BEM 版本 | 修复方向 |
|---|---|---|
| `orders-table-wrapper` / `orders-table` | 无对应 | **新增 CSS** |
| `orders-order-number` | 无对应 | **新增 CSS** |
| `orders-empty` / `orders-empty-icon` / `orders-empty-title` / `orders-empty-text` | 无对应 | **新增 CSS** |
| `order-status-badge` | 无对应 | **新增 CSS** |
| `badge-processing` | `badge--processing` | **改 HTML**（单横线→双横线） |
| `badge-shipped` | `badge--shipped` | **改 HTML** |
| `badge-delivered` | `badge--delivered` | **改 HTML** |
| `badge-cancelled` | `badge--cancelled` | **改 HTML** |

---

### 12. Pagination (category.html, blog/list.html)

| 当前 HTML 类名 | CSS 对应 BEM 版本 | 修复方向 |
|---|---|---|
| `pagination` / `pagination-item` / `pagination-prev` / `pagination-next` / `pagination-ellipsis` | 无对应 | **新增 CSS** |
| `page-link` / `page-info` | 无对应 | **新增 CSS** |

---

### 13. FAQ Page (faq.html)

| 当前 HTML 类名 | CSS 对应 BEM 版本 | 修复方向 |
|---|---|---|
| `faq-accordion` / `faq-item` / `faq-question` / `faq-answer` | 无对应 | **新增 CSS** |
| `faq-contact-cta` / `faq-contact-title` / `faq-contact-text` | 无对应 | **新增 CSS** |

---

### 14. Policy Pages (shipping.html, returns.html, privacy.html, terms.html)

| 当前 HTML 类名 | CSS 对应 BEM 版本 | 修复方向 |
|---|---|---|
| `policy-page` | 无对应 | **新增 CSS** |
| `policy-table` | 无对应 | **新增 CSS** |
| `last-updated` | 无对应 | **新增 CSS** |
| `note` | 无对应 | **新增 CSS** |
| `process-steps` / `step` | 无对应 | **新增 CSS** |

---

### 15. Error Pages (404.html, 500.html)

| 当前 HTML 类名 | CSS 对应 BEM 版本 | 修复方向 |
|---|---|---|
| `error-content` / `error-code` / `error-title` / `error-description` / `error-actions` | 无对应 | **新增 CSS** |
| `error-search` / `error-search-input` | 无对应 | **新增 CSS** |

---

### 16. Newsletter Section (home.html)

| 当前 HTML 类名 | CSS 对应 BEM 版本 | 修复方向 |
|---|---|---|
| `newsletter-inner` / `newsletter-heading` / `newsletter-subheading` / `newsletter-form` / `newsletter-input` | 无对应 | **新增 CSS** |

---

### 17. 已匹配组件（无需修复）

以下组件 HTML 类名与 CSS 完全一致：

- **Header**: 全部 `header__*` 类名匹配
- **Footer**: 全部 `footer__*` 类名匹配
- **Age Gate**: 全部 `age-gate__*` 类名匹配
- **Flash Messages**: 全部 `flash-message*` 类名匹配
- **Product Card 组件** (`product_card.html`): 全部 `product-card__*` 匹配
- **Checkout**: `checkout__grid` / `checkout__main` / `checkout__sidebar` 匹配

---

## 修复策略建议

### 策略 A: 优先改 HTML（推荐用于 BEM 对应项）

适用场景：CSS 中已存在语义完全匹配的 BEM 版本，仅命名风格不一致。

涉及约 **35 处**，包括：
- Hero: `hero-content` → `hero__content` 等
- Product Detail: `product-detail-gallery` → `product-detail__gallery` 等
- Blog Card: `blog-card-image` → `blog-card__image` 等
- Cart: `cart-table` → `cart__table` 等
- Auth: `auth-title` → `auth-card__title`
- Orders badges: `badge-processing` → `badge--processing`
- Product Grid: `product-grid-3col` → `product-grid--3col`

### 策略 B: 新增 CSS 规则（用于无对应项）

适用场景：CSS 中完全不存在对应规则，需新增约 **227 条**规则。

按优先级排序：
1. **P0 — 核心功能**: `quantity-selector`、`add-to-cart-btn`、`breadcrumb`、`pagination`、`stars`
2. **P1 — 页面布局**: `cart-layout`、`category-layout`、`profile-layout`、`filter-*`、`auth-form`
3. **P2 — 内容展示**: `policy-page`、`faq-accordion`、`error-content`、`post-content`、`newsletter-*`
4. **P3 — 辅助**: `section-*` 变体、`form-hint`、`empty-state`、`tag` 等

---

## CSS 中定义但 HTML 未使用的类 (98 个)

以下 CSS 类在当前 HTML 模板中未被引用，可能为预留或冗余：

```
age-gate__footer, auth-page, badge--confirmed, badge--delivered, 
badge--pending, badge--refunded, brand-value__desc, brand-values, 
brand-values__grid, cart__product-remove, cart__qty, cart__qty-btn, 
cart__qty-input, cart__summary-row--total, checkout, checkout__grid, 
checkout__main, checkout__sidebar, fade-in, flash-message--error, 
flash-message--info, flash-message--warning, flash-message__close, 
flash-messages, footer__col-title, form-checkbox, form-error, 
form-select, form-textarea, header__link--active, header__user, 
header__user-dropdown, header__user-toggle, img[data-src], 
lazy-loaded, mobile-menu, mobile-menu__link, mt-1, mt-2, mt-3, mt-4, 
mb-1, mb-2, mb-3, mb-4, nav-open, product-card__badge--bestseller, 
product-card__badge--new, product-card__badge--sale, 
product-card__price--original, product-card__quick-add, 
product-card__rating, product-card__rating-count, 
product-detail__actions, product-detail__description, 
product-detail__price, product-detail__qty-btn, 
product-detail__qty-input, product-detail__quantity, 
product-detail__thumb--active, section, section__header, 
section__subtitle, section__title, skeleton, spinner, sr-only, 
text-center, text-left, text-right, toast, toast--error, 
toast--hide, toast--info, toast--success, toast--warning, 
toast-container

(注：其中部分通过 Jinja 动态拼接使用，如 flash-message--{{ category }}，实际运行时可能生效)
```

---

## 风险提示

1. **Cart 组件** HTML 使用 `cart-table` 等连字符命名，而 CSS 中定义了 BEM 版本的 `cart__table`。改 HTML 时需要确认 JS 脚本 `main.js` 是否有对类名的依赖。
2. **Jinja 动态类名**（如 `flash-message--{{ category }}`、`badge-{{ status }}` 等）在静态审计中可能被误报为"缺失"，实际运行时正确。
3. **部分 CSS 类**（如 `spinner`、`skeleton`、`toast-*`、`fade-in`）可能由 JS 动态注入，不在 HTML 模板中直接出现，属于正常运行所需，**不应删除**。
