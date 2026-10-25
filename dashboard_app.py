# -*- coding: utf-8 -*-
# =============================================================================
#  لوحة تحكم تفاعلية - جمعية رعاية الأيتام  (Streamlit + Plotly)
#  الترتيب: ترويسة ← فلاتر ← بطاقات المؤشرات ← الملخص التنفيذي الديناميكي ← الرسوم ← البيانات
# =============================================================================

import html as _html
import io
import os
import re
import unicodedata

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =============================================================================
# 0) الإعدادات
# =============================================================================
ORG_NAME = "جمعية رعاية الأيتام"
ANALYST_TEXT = "محلل البيانات: رهف الجهني"
DASH_TITLE = "لوحة تحكم الأداء والأثر"
DATA_FILE = "Data_Cleaned.csv"

C_MONTH, C_BRANCH, C_ITEM, C_PROGRAM = "الشهر", "الفرع / المنطقة", "البند في الموازنة", "اسم البرنامج"
C_BEN, C_UNIT, C_COST = "عدد المستفيدين", "تكلفة المستفيد (ريال)", "إجمالي التكلفة (ريال)"
C_ATT, C_COMP, C_SAT = "نسبة الحضور (%)", "نسبة إكمال البرنامج (%)", "معدل رضا المستفيدين (%)"
C_VOL, C_VOLH, C_GOV = "عدد المتطوعين", "ساعات التطوع", "نسبة التوافق بالحوكمة (%)"
C_IMPACT, C_STORY = "مؤشر قياس الأثر (%)", "عدد قصص النجاح"
NUMERIC_COLS = [C_BEN, C_UNIT, C_COST, C_ATT, C_COMP, C_SAT, C_VOL, C_VOLH, C_GOV, C_IMPACT, C_STORY]
REQUIRED_COLS = [C_MONTH, C_BRANCH, C_ITEM, C_PROGRAM] + NUMERIC_COLS

# حدود الإنذار المبكر (افتراضات قابلة للتعديل)
EARLY_WARNING = {C_ATT: 75, C_COMP: 75, C_SAT: 80, C_GOV: 85}

FILTER_KEYS = ["f_month", "f_branch", "f_program"]

LIGHT = dict(bg="#f4f7f9", card="#ffffff", text="#1b2a33", muted="#5c6770", border="#dbe3e8",
             primary="#0f4c5c", accent="#e36414", input="#ffffff", grid="#e6ecef",
             good="#1b8a5a", bad="#c62828", btn_text="#ffffff", h1="#0f4c5c", h2="#2a8197")
DARK = dict(bg="#0d1a21", card="#15262f", text="#e7eff3", muted="#9fb2bc", border="#2a4350",
            primary="#62b6cc", accent="#ff9a4d", input="#1c313c", grid="#2a4350",
            good="#4cd08f", bad="#ff6b6b", btn_text="#0b1a21", h1="#0a2b36", h2="#16607a")

st.set_page_config(page_title=f"{ORG_NAME} | {DASH_TITLE}", page_icon="📊", layout="wide",
                   initial_sidebar_state="expanded")

# =============================================================================
# 1) الترويسة + زر تبديل المظهر
# =============================================================================
st.session_state.setdefault("dark_mode", False)
col_hero, col_toggle = st.columns([5, 1.3])
with col_toggle:
    st.write("")
    st.write("")
    dark = st.toggle("🌙 الوضع الليلي", key="dark_mode")      # زر التبديل ليلي/نهاري
T = DARK if dark else LIGHT

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
html, body, .stApp, label, button, input, textarea, [data-testid="stMarkdownContainer"]
{ font-family:'Tajawal','Segoe UI',Tahoma,sans-serif; }
.stApp { background:__BG__; color:__TEXT__; direction:rtl; }
[data-testid="stHeader"] { background:transparent; }
[data-testid="stSidebar"] { background:__CARD__; border-left:1px solid __BORDER__; direction:rtl; }
.stDeployButton, footer { display:none !important; }
:where(.stApp) :where(p, li, h1, h2, h3, h4, span) { color:__TEXT__; }
.stApp label, .stApp label p, [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p { color:__TEXT__ !important; }
div[data-baseweb="select"] > div { background:__INPUT__ !important; border-color:__BORDER__ !important; color:__TEXT__ !important; }
div[data-baseweb="select"] input { color:__TEXT__ !important; }
div[data-baseweb="select"] svg { fill:__MUTED__ !important; }
span[data-baseweb="tag"] { background:__PRIMARY__ !important; }
span[data-baseweb="tag"], span[data-baseweb="tag"] span { color:__BTN__ !important; }
div[data-baseweb="popover"] > div, div[data-baseweb="popover"] ul { background:__CARD__ !important; color:__TEXT__ !important; }
li[role="option"] { color:__TEXT__ !important; }
li[role="option"]:hover, li[aria-selected="true"] { background:__BORDER__ !important; }
.stButton button, .stDownloadButton button { background:__PRIMARY__; color:__BTN__ !important; border:0;
  border-radius:10px; font-weight:700; }
.stButton button p, .stDownloadButton button p { color:__BTN__ !important; }
[data-testid="stExpander"] { background:__CARD__; border:1px solid __BORDER__; border-radius:14px; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * { color:__TEXT__ !important; }
[data-testid="stPlotlyChart"] { background:__CARD__; border:1px solid __BORDER__; border-radius:16px; padding:6px; }
.js-plotly-plot { direction:ltr; }
.hero { background:linear-gradient(135deg,__H1__,__H2__); border-radius:18px; padding:22px 28px; color:#ffffff; }
.hero .org { font-size:32px; font-weight:800; line-height:1.3; }
.hero .sub { opacity:.88; font-size:15px; margin-top:2px; }
.hero .badge { display:inline-block; margin-top:12px; background:rgba(255,255,255,.16);
  border:1px solid rgba(255,255,255,.4); padding:5px 16px; border-radius:999px; font-size:14px; font-weight:700; }
.kpi-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin:16px 0 8px; }
@media (max-width:1000px){ .kpi-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
.kpi { background:__CARD__; border:1px solid __BORDER__; border-top:4px solid __PRIMARY__; border-radius:16px; padding:16px 18px; }
.kpi .v { font-size:27px; font-weight:800; color:__PRIMARY__; line-height:1.25; }
.kpi .l { font-size:13px; color:__MUTED__; margin-top:4px; }
.kpi .d { font-size:12px; margin-top:7px; font-weight:700; }
.kpi .d.good { color:__GOOD__; } .kpi .d.bad { color:__BAD__; } .kpi .d.flat { color:__MUTED__; }
.summary { background:__CARD__; border:1px solid __BORDER__; border-right:6px solid __ACCENT__;
  border-radius:16px; padding:18px 24px; margin:10px 0 8px; }
.summary h3 { margin:0 0 8px; color:__PRIMARY__; font-size:21px; font-weight:800; }
.summary ul { margin:0; padding-right:20px; }
.summary li { margin:8px 0; line-height:1.95; color:__TEXT__; font-size:15px; }
.summary .note { color:__MUTED__; font-size:12.5px; margin-top:10px; line-height:1.7; }
.sec { font-size:21px; font-weight:800; color:__PRIMARY__; margin:26px 0 10px;
  border-bottom:2px solid __ACCENT__; padding-bottom:6px; display:inline-block; }
.tbl-wrap { max-height:420px; overflow:auto; border:1px solid __BORDER__; border-radius:12px; background:__CARD__; }
.data-table { width:100%; border-collapse:collapse; font-size:13px; }
.data-table th { background:__PRIMARY__; color:__BTN__; padding:8px 6px; text-align:center; position:sticky; top:0; }
.data-table td { border-bottom:1px solid __BORDER__; padding:6px; text-align:center; color:__TEXT__; }
.foot { color:__MUTED__; font-size:12px; margin:26px 0 6px; text-align:center; }
</style>
"""
_tok = {"BG": T["bg"], "TEXT": T["text"], "CARD": T["card"], "BORDER": T["border"], "INPUT": T["input"],
        "MUTED": T["muted"], "PRIMARY": T["primary"], "ACCENT": T["accent"], "GOOD": T["good"],
        "BAD": T["bad"], "BTN": T["btn_text"], "H1": T["h1"], "H2": T["h2"]}
for _k, _v in _tok.items():
    CSS = CSS.replace(f"__{_k}__", _v)
st.markdown(CSS, unsafe_allow_html=True)

with col_hero:
    st.markdown(
        f'<div class="hero"><div class="org">{_html.escape(ORG_NAME)}</div>'
        f'<div class="sub">{_html.escape(DASH_TITLE)}</div>'
        f'<div class="badge">{_html.escape(ANALYST_TEXT)}</div></div>', unsafe_allow_html=True)

# =============================================================================
# 2) دوال مساعدة (حساب وتنسيق)
# =============================================================================
def esc(x):
    return _html.escape(str(x))


def fmt(n, d=0):
    return "—" if n is None or pd.isna(n) else f"{n:,.{d}f}"


def clean_text(v):
    s = unicodedata.normalize("NFKC", str(v))
    s = re.sub(r"[​-‏‪-‮﻿]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def to_number(series):
    s = series.astype(str).map(lambda v: unicodedata.normalize("NFKC", v))
    s = s.str.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩٫٬", "0123456789.,"))
    s = s.str.replace(r"[,%\s]|ريال|SAR", "", regex=True)
    return pd.to_numeric(s, errors="coerce")


def wavg(values, weights):
    """متوسط مرجّح بعدد المستفيدين"""
    m = values.notna() & weights.notna() & (weights > 0)
    return float(np.average(values[m], weights=weights[m])) if m.sum() else np.nan


def _ar_norm(s):
    s = clean_text(s).lower()
    s = re.sub(r"[إأآٱ]", "ا", s)
    return s.replace("ى", "ي").replace("ة", "ه")


MONTH_LISTS = [
    ["يناير", "فبراير", "مارس", "ابريل", "مايو", "يونيو", "يوليو", "اغسطس", "سبتمبر", "اكتوبر", "نوفمبر", "ديسمبر"],
    ["كانون الثاني", "شباط", "اذار", "نيسان", "ايار", "حزيران", "تموز", "اب", "ايلول", "تشرين الاول", "تشرين الثاني", "كانون الاول"],
    ["محرم", "صفر", "ربيع الاول", "ربيع الاخر", "جمادي الاولي", "جمادي الاخره", "رجب", "شعبان", "رمضان", "شوال", "ذو القعده", "ذو الحجه"],
    ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"],
]


def order_months(values):
    """يرتّب الأشهر زمنياً (عربي/هجري/إنجليزي/أرقام/تواريخ). وإلا يبقى ترتيب الظهور الأول."""
    vals = list(dict.fromkeys([str(v) for v in values]))
    if all(re.fullmatch(r"\d{1,2}", v) for v in vals):
        return sorted(vals, key=int)
    best, best_hits = None, 0
    for names in MONTH_LISTS:
        hits, keys = 0, {}
        for v in vals:
            nv = _ar_norm(v)
            idx = next((i for i, nm in enumerate(names) if nv == nm or nm in nv), None)
            if idx is not None:
                hits += 1
                y = re.search(r"(19|20)\d{2}|14\d{2}", nv)
                keys[v] = (int(y.group()) if y else 0, idx)
        if hits > best_hits:
            best, best_hits = keys, hits
    if best is not None and best_hits >= max(1, len(vals) * 0.6):
        return sorted(vals, key=lambda v: best.get(v, (9999, 99)))
    dt = pd.to_datetime(pd.Series(vals), errors="coerce")
    if dt.notna().all():
        return [v for _, v in sorted(zip(dt, vals))]
    return vals


# =============================================================================
# 3) تحميل البيانات (يبقى داخل بيئة التشغيل فقط)
# =============================================================================
def _read_bytes(raw):
    for enc in ("utf-8-sig", "utf-8", "cp1256"):
        try:
            return pd.read_csv(io.StringIO(raw.decode(enc)), dtype=str, keep_default_na=False)
        except UnicodeDecodeError:
            continue
    return None


@st.cache_data(show_spinner=False)
def prepare(raw_bytes):
    d = _read_bytes(raw_bytes)
    if d is None:
        return None, None, ["تعذرت قراءة الملف (جرّب UTF-8)"]
    d.columns = [clean_text(c) for c in d.columns]
    missing = [c for c in REQUIRED_COLS if c not in d.columns]
    if missing:
        return None, None, missing
    for c in d.columns:
        d[c] = d[c].map(clean_text)
    num = d.copy()
    for c in NUMERIC_COLS:
        num[c] = to_number(num[c])
    return d, num, []


def load_source():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "rb") as f:
            return f.read()
    up = st.file_uploader(f"ارفع الملف {DATA_FILE} (يُعالج داخل بيئة التشغيل فقط)", type=["csv"])
    if up is None:
        st.info(f"لم يُعثر على {DATA_FILE}. ارفعه هنا أو ضعه بجانب التطبيق.")
        st.stop()
    return up.getvalue()


df_str, df, missing_cols = prepare(load_source())
if missing_cols:
    st.error("أعمدة مطلوبة غير موجودة في الملف: " + "، ".join(missing_cols))
    st.stop()


def group_stats(d, col, order=None):
    """مؤشرات كل مجموعة (فرع/برنامج/شهر...) مع نسب مرجّحة بعدد المستفيدين"""
    rows = {}
    for key, g in d.groupby(col, sort=False):
        ben, cost = g[C_BEN].sum(), g[C_COST].sum()
        rows[key] = dict(n=len(g), ben=ben, cost=cost, cpb=cost / ben if ben > 0 else np.nan,
                         sat=wavg(g[C_SAT], g[C_BEN]), imp=wavg(g[C_IMPACT], g[C_BEN]),
                         att=wavg(g[C_ATT], g[C_BEN]), comp=wavg(g[C_COMP], g[C_BEN]),
                         gov=g[C_GOV].mean(), story=g[C_STORY].sum(), volh=g[C_VOLH].sum())
    out = pd.DataFrame.from_dict(rows, orient="index")
    if order is not None and len(out):
        out = out.reindex([o for o in order if o in out.index])
    return out


def kpis(d):
    ben, cost = d[C_BEN].sum(), d[C_COST].sum()
    return dict(n=len(d), ben=ben, cost=cost, cpb=cost / ben if ben > 0 else np.nan,
                sat=wavg(d[C_SAT], d[C_BEN]), imp=wavg(d[C_IMPACT], d[C_BEN]),
                att=wavg(d[C_ATT], d[C_BEN]), comp=wavg(d[C_COMP], d[C_BEN]),
                gov=d[C_GOV].mean(), volh=d[C_VOLH].sum(), story=d[C_STORY].sum())


# =============================================================================
# 4) الفلاتر (الشريط الجانبي)
# =============================================================================
months_order = order_months(df[C_MONTH].unique())
branch_opts = list(df.groupby(C_BRANCH)[C_BEN].sum().sort_values(ascending=False).index)
program_opts = sorted(df[C_PROGRAM].unique())


def _reset_filters():
    for k in FILTER_KEYS:
        st.session_state[k] = []


with st.sidebar:
    st.markdown("### 🎛️ الفلاتر")
    st.caption("بدون اختيار = عرض الكل")
    sel_m = st.multiselect("الشهر", months_order, key="f_month")
    sel_b = st.multiselect("الفرع / المنطقة", branch_opts, key="f_branch")
    sel_p = st.multiselect("اسم البرنامج", program_opts, key="f_program")
    st.button("↺ إعادة ضبط الفلاتر", on_click=_reset_filters)

mask = pd.Series(True, index=df.index)
if sel_m:
    mask &= df[C_MONTH].isin(sel_m)
if sel_b:
    mask &= df[C_BRANCH].isin(sel_b)
if sel_p:
    mask &= df[C_PROGRAM].isin(sel_p)
d, d_view = df[mask], df_str[mask]
is_filtered = bool(sel_m or sel_b or sel_p)

with st.sidebar:
    st.markdown(f"**السجلات المطابقة:** {len(d):,} من {len(df):,}")

if d.empty:
    st.warning("لا توجد سجلات تطابق هذه الفلاتر. وسّع الاختيار أو اضغط «إعادة ضبط الفلاتر».")
    st.stop()

K, K_all = kpis(d), kpis(df)

# =============================================================================
# 5) بطاقات مؤشرات الأداء
# =============================================================================
def delta_html(cur, base, kind):
    """مقارنة المؤشر بمتوسط الجمعية الكامل (تظهر فقط عند تفعيل فلتر)"""
    if not is_filtered or pd.isna(cur) or pd.isna(base) or not base:
        return ""
    if kind == "pts":
        diff = cur - base
        if abs(diff) < 0.05:
            return '<div class="d flat">≈ مثل متوسط الجمعية</div>'
        cls = "good" if diff > 0 else "bad"
        return f'<div class="d {cls}">{"▲" if diff > 0 else "▼"} {abs(diff):.1f} نقطة عن متوسط الجمعية</div>'
    diff = (cur / base - 1) * 100          # kind == "cost": الأقل أفضل
    if abs(diff) < 0.5:
        return '<div class="d flat">≈ مثل متوسط الجمعية</div>'
    cls = "good" if diff < 0 else "bad"
    return f'<div class="d {cls}">{"▲" if diff > 0 else "▼"} {abs(diff):.1f}% عن متوسط الجمعية</div>'


def share_html(cur, tot):
    if not is_filtered or not tot:
        return ""
    return f'<div class="d flat">{cur / tot * 100:.1f}% من إجمالي الجمعية</div>'


cards = [
    (fmt(K["ben"]), "إجمالي المستفيدين", share_html(K["ben"], K_all["ben"])),
    (fmt(K["cost"]), "إجمالي التكاليف (ريال)", share_html(K["cost"], K_all["cost"])),
    (fmt(K["cpb"], 1), "تكلفة المستفيد (ريال)", delta_html(K["cpb"], K_all["cpb"], "cost")),
    (fmt(K["sat"], 1) + "%", "معدل الرضا (مرجّح)", delta_html(K["sat"], K_all["sat"], "pts")),
    (fmt(K["imp"], 1) + "%", "مؤشر الأثر (مرجّح)", delta_html(K["imp"], K_all["imp"], "pts")),
    (fmt(K["volh"]), "ساعات التطوع", share_html(K["volh"], K_all["volh"])),
    (fmt(K["story"]), "قصص النجاح", share_html(K["story"], K_all["story"])),
    (fmt(K["gov"], 1) + "%", "التوافق بالحوكمة", delta_html(K["gov"], K_all["gov"], "pts")),
]
st.markdown('<div class="kpi-grid">' + "".join(
    f'<div class="kpi"><div class="v">{v}</div><div class="l">{l}</div>{dl}</div>' for v, l, dl in cards)
    + "</div>", unsafe_allow_html=True)

# =============================================================================
# 6) الملخص التنفيذي الديناميكي (يتغير مع الفلاتر)
# =============================================================================
def scope_text(sel, total, singular_all, label):
    if not sel:
        return singular_all
    if len(sel) <= 3:
        return "، ".join(esc(s) for s in sel)
    return f"{len(sel)} من {total} {label}"


def build_summary():
    items = []
    scope = (f"<b>نطاق التحليل:</b> {scope_text(sel_m, len(months_order), 'كل الأشهر', 'أشهر')} | "
             f"{scope_text(sel_b, len(branch_opts), 'كل الفروع', 'فروع')} | "
             f"{scope_text(sel_p, len(program_opts), 'كل البرامج', 'برامج')} — "
             f"{K['n']:,} سجل من أصل {K_all['n']:,}.")
    items.append(scope)

    size = (f"<b>الحجم والإنفاق:</b> يخدم هذا النطاق {fmt(K['ben'])} مستفيداً بإنفاق {fmt(K['cost'])} ريال "
            f"(متوسط {fmt(K['cpb'], 1)} ريال للمستفيد).")
    if is_filtered:
        size += (f" ويمثل {K['ben'] / K_all['ben'] * 100:.1f}% من مستفيدي الجمعية "
                 f"و{K['cost'] / K_all['cost'] * 100:.1f}% من إنفاقها.")
    items.append(size)

    gb = group_stats(d, C_BRANCH)
    gb_eff = gb[(gb["cost"] > 0) & (gb["ben"] > 0)]
    if len(gb) > 1:
        top = gb["ben"].idxmax()
        t = f"<b>الفروع:</b> يتصدر {esc(top)} بـ {gb['ben'].max() / K['ben'] * 100:.0f}% من المستفيدين."
        if len(gb_eff) > 1:
            lo, hi = gb_eff["cpb"].idxmin(), gb_eff["cpb"].idxmax()
            gap = (gb_eff["cpb"].max() / gb_eff["cpb"].min() - 1) * 100
            t += (f" تتراوح تكلفة المستفيد بين {fmt(gb_eff['cpb'].min(), 1)} ريال ({esc(lo)}) و"
                  f"{fmt(gb_eff['cpb'].max(), 1)} ريال ({esc(hi)}) بفارق {gap:.0f}%، "
                  "وقد يعكس الفارق اختلاف نوع البرامج لا الكفاءة وحدها.")
        items.append(t)
    elif len(gb) == 1 and not pd.isna(K["cpb"]) and not pd.isna(K_all["cpb"]):
        diff = (K["cpb"] / K_all["cpb"] - 1) * 100
        word = "أعلى" if diff > 0 else "أقل"
        items.append(f"<b>الفرع:</b> تكلفة المستفيد في {esc(gb.index[0])} {fmt(K['cpb'], 1)} ريال، "
                     f"{word} من متوسط الجمعية ({fmt(K_all['cpb'], 1)}) بنسبة {abs(diff):.1f}%.")

    q = (f"<b>الجودة والأثر:</b> الرضا {fmt(K['sat'], 1)}% والأثر {fmt(K['imp'], 1)}% "
         f"والحضور {fmt(K['att'], 1)}% والإكمال {fmt(K['comp'], 1)}% (مرجّحة بعدد المستفيدين).")
    gb_imp = gb.dropna(subset=["imp"])
    if len(gb_imp) > 1:
        q += (f" أعلى أثر في {esc(gb_imp['imp'].idxmax())} ({gb_imp['imp'].max():.1f}%) "
              f"وأدناه في {esc(gb_imp['imp'].idxmin())} ({gb_imp['imp'].min():.1f}%).")
    items.append(q)

    gp = group_stats(d, C_PROGRAM)
    if len(gp) > 1:
        top_p = gp["ben"].idxmax()
        t = f"<b>البرامج:</b> أكبر البرامج وصولاً «{esc(top_p)}» ({gp['ben'].max() / K['ben'] * 100:.0f}% من المستفيدين)."
        gp_imp = gp.dropna(subset=["imp"])
        if len(gp_imp) > 1:
            t += (f" أعلاها أثراً «{esc(gp_imp['imp'].idxmax())}» ({gp_imp['imp'].max():.1f}%) "
                  f"وأدناها «{esc(gp_imp['imp'].idxmin())}» ({gp_imp['imp'].min():.1f}%).")
        items.append(t)
    elif len(gp) == 1:
        items.append(f"<b>البرنامج:</b> «{esc(gp.index[0])}» هو البرنامج الوحيد ضمن النطاق.")

    months_in = [m for m in months_order if m in set(d[C_MONTH])]
    if len(months_in) >= 2:
        gm = group_stats(d, C_MONTH, order=months_in)
        m1, m2 = gm.index[0], gm.index[-1]
        parts = []
        if gm.loc[m1, "ben"] > 0:
            ch = (gm.loc[m2, "ben"] / gm.loc[m1, "ben"] - 1) * 100
            if abs(ch) < 0.5:
                parts.append("المستفيدون ثابتون تقريباً")
            else:
                parts.append(f"المستفيدون {'ارتفعوا' if ch >= 0 else 'انخفضوا'} {abs(ch):.0f}%")
        if not pd.isna(gm.loc[m1, "sat"]) and not pd.isna(gm.loc[m2, "sat"]):
            ds = gm.loc[m2, "sat"] - gm.loc[m1, "sat"]
            if abs(ds) < 0.05:
                parts.append("الرضا ثابت تقريباً")
            else:
                parts.append(f"الرضا {'ارتفع' if ds >= 0 else 'انخفض'} {abs(ds):.1f} نقطة")
        if parts:
            items.append(f"<b>الاتجاه:</b> من {esc(m1)} إلى {esc(m2)}: " + "، و".join(parts) + ".")

    flagged = pd.Series(False, index=d.index)
    counts = {}
    for col, thr in EARLY_WARNING.items():
        m = d[col] < thr
        counts[col] = int(m.sum())
        flagged |= m
    k = int(flagged.sum())
    if k == 0:
        items.append("<b>الإنذار المبكر:</b> لا سجلات تحت حدود الإنذار المقترحة ضمن هذا النطاق.")
    else:
        worst = max(counts, key=counts.get)
        items.append(f"<b>الإنذار المبكر:</b> {k:,} سجل ({k / len(d) * 100:.1f}%) تحت حد واحد على الأقل، "
                     f"والأكثر تكراراً: {esc(worst.replace(' (%)', ''))} ({counts[worst]:,} سجل).")

    if K["n"] < 10:
        items.append(f"⚠️ <b>تنبيه:</b> عدد السجلات ({K['n']}) قليل، فتجنّب تعميم النتائج.")
    return items


summary_items = build_summary()
st.markdown(
    '<div class="summary"><h3>الملخص التنفيذي (Executive Summary)</h3><ul>'
    + "".join(f"<li>{i}</li>" for i in summary_items) + "</ul>"
    '<div class="note">المستفيدون = مجموع السجلات، وقد يُحسب المستفيد نفسه أكثر من مرة عبر الأشهر أو البرامج. '
    "حدود الإنذار (الحضور والإكمال 75%، الرضا 80%، الحوكمة 85%) افتراضات قابلة للتعديل.</div></div>",
    unsafe_allow_html=True)

# =============================================================================
# 7) الرسوم التفاعلية (Plotly) في الأسفل
# =============================================================================
st.markdown('<div class="sec">الرسوم البيانية التفاعلية</div>', unsafe_allow_html=True)
PALETTE = ["#2a9d8f", "#e76f51", "#457b9d", "#e9c46a", "#8d6cab", "#6a994e"] if not dark else \
          ["#4cc9b0", "#ff8a65", "#6fb1e0", "#f2d36b", "#b79ae0", "#9ccc65"]
FONT = "Tajawal, Tahoma, Arial, sans-serif"


def style(fig, title, height=390):
    fig.update_layout(
        template="plotly_dark" if dark else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=T["text"], size=13),
        title=dict(text=title, x=1, xanchor="right", font=dict(size=16)),
        height=height, margin=dict(l=20, r=20, t=60, b=40),
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5),
        hoverlabel=dict(font_family=FONT))
    fig.update_xaxes(gridcolor=T["grid"], linecolor=T["grid"])
    fig.update_yaxes(gridcolor=T["grid"], linecolor=T["grid"])
    return fig


def show(fig):
    cfg = {"displaylogo": False}
    try:
        st.plotly_chart(fig, theme=None, config=cfg)      # theme=None: نتحكم نحن بالألوان
    except TypeError:
        st.plotly_chart(fig)


def empty_note(msg):
    st.info(msg)


gb = group_stats(d, C_BRANCH).sort_values("ben", ascending=False)
months_in = [m for m in months_order if m in set(d[C_MONTH])]
gm = group_stats(d, C_MONTH, order=months_in)

row1 = st.columns(2)
with row1[0]:   # 1) المستفيدون حسب الفرع
    fig = go.Figure(go.Bar(x=list(gb.index), y=gb["ben"], marker_color=PALETTE[0],
                           texttemplate="%{y:,.0f}", textposition="outside",
                           hovertemplate="<b>%{x}</b><br>المستفيدون: %{y:,.0f}<extra></extra>"))
    show(style(fig, "توزيع المستفيدين حسب الفرع / المنطقة"))
with row1[1]:   # 2) التكاليف حسب الفرع
    fig = go.Figure(go.Bar(x=list(gb.index), y=gb["cost"], marker_color=PALETTE[1],
                           texttemplate="%{y:,.0f}", textposition="outside",
                           hovertemplate="<b>%{x}</b><br>التكلفة: %{y:,.0f} ريال<extra></extra>"))
    show(style(fig, "إجمالي التكاليف حسب الفرع / المنطقة (ريال)"))

row2 = st.columns(2)
with row2[0]:   # 3) تكلفة المستفيد حسب الفرع
    ge = gb.dropna(subset=["cpb"])
    if len(ge):
        avg = K["cpb"]
        colors_ = [T["accent"] if v > avg else PALETTE[0] for v in ge["cpb"]]
        fig = go.Figure(go.Bar(x=list(ge.index), y=ge["cpb"], marker_color=colors_,
                               texttemplate="%{y:,.0f}", textposition="outside",
                               hovertemplate="<b>%{x}</b><br>تكلفة المستفيد: %{y:,.1f} ريال<extra></extra>"))
        fig.add_hline(y=avg, line_dash="dash", line_color=T["muted"],
                      annotation_text=f"متوسط النطاق {avg:,.0f}", annotation_position="top left")
        show(style(fig, "تكلفة المستفيد الفعلية (البرتقالي = أعلى من المتوسط)"))
    else:
        empty_note("لا بيانات كافية لحساب تكلفة المستفيد.")
with row2[1]:   # 4) مؤشرات الجودة حسب الفرع
    fig = go.Figure()
    for name, key, colr in [("الرضا", "sat", PALETTE[0]), ("الأثر", "imp", PALETTE[1]),
                            ("الحضور", "att", PALETTE[2]), ("الإكمال", "comp", PALETTE[3])]:
        fig.add_trace(go.Bar(name=name, x=list(gb.index), y=gb[key], marker_color=colr,
                             hovertemplate="<b>%{x}</b><br>" + name + ": %{y:.1f}%<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(range=[0, 105])
    show(style(fig, "مؤشرات الجودة والأثر حسب الفرع (%)"))

row3 = st.columns(2)
with row3[0]:   # 5) الاتجاه الشهري: المستفيدون والتكلفة
    if len(gm) >= 1:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(name="المستفيدون", x=list(gm.index), y=gm["ben"], marker_color=PALETTE[0],
                             opacity=0.85), secondary_y=False)
        fig.add_trace(go.Scatter(name="التكلفة (ريال)", x=list(gm.index), y=gm["cost"], mode="lines+markers",
                                 line=dict(color=PALETTE[1], width=3)), secondary_y=True)
        fig.update_yaxes(title_text="المستفيدون", secondary_y=False)
        fig.update_yaxes(title_text="التكلفة (ريال)", secondary_y=True, showgrid=False)
        fig.update_xaxes(categoryorder="array", categoryarray=list(gm.index))
        show(style(fig, "الاتجاه الشهري: المستفيدون والتكلفة"))
with row3[1]:   # 6) الاتجاه الشهري للجودة
    if len(gm) >= 1:
        fig = go.Figure()
        for name, key, colr in [("الرضا", "sat", PALETTE[0]), ("الأثر", "imp", PALETTE[1]),
                                ("الحضور", "att", PALETTE[2]), ("الإكمال", "comp", PALETTE[3])]:
            fig.add_trace(go.Scatter(name=name, x=list(gm.index), y=gm[key], mode="lines+markers",
                                     line=dict(color=colr, width=3)))
        fig.update_xaxes(categoryorder="array", categoryarray=list(gm.index))
        fig.update_yaxes(range=[0, 105])
        show(style(fig, "الاتجاه الشهري لمؤشرات الجودة (%)"))

gp = group_stats(d, C_PROGRAM)
row4 = st.columns(2)
with row4[0]:   # 7) أكبر البرامج وصولاً
    top = gp.sort_values("ben", ascending=False).head(10).sort_values("ben")
    fig = go.Figure(go.Bar(x=top["ben"], y=list(top.index), orientation="h", marker_color=PALETTE[2],
                           texttemplate="%{x:,.0f}", textposition="outside",
                           hovertemplate="<b>%{y}</b><br>المستفيدون: %{x:,.0f}<extra></extra>"))
    show(style(fig, "أكبر 10 برامج من حيث المستفيدين"))
with row4[1]:   # 8) توزيع التكلفة حسب بند الموازنة
    gi = d.groupby(C_ITEM)[C_COST].sum().sort_values(ascending=False)
    if len(gi) > 8:
        gi = pd.concat([gi.head(8), pd.Series({"أخرى": gi.iloc[8:].sum()})])
    fig = go.Figure(go.Pie(labels=list(gi.index), values=list(gi.values), hole=0.55, sort=False,
                           marker=dict(colors=(PALETTE * 3)[:len(gi)]),
                           hovertemplate="<b>%{label}</b><br>%{value:,.0f} ريال (%{percent})<extra></extra>"))
    show(style(fig, "توزيع التكاليف حسب بند الموازنة"))

row5 = st.columns(2)
with row5[0]:   # 9) الكفاءة مقابل الأثر (البرامج)
    sc = gp[(gp["ben"] > 0)].dropna(subset=["cpb", "imp"])
    if len(sc) >= 2:
        sizeref = 2.0 * sc["ben"].max() / (46 ** 2)
        fig = go.Figure(go.Scatter(
            x=sc["cpb"], y=sc["imp"], mode="markers", text=list(sc.index),
            marker=dict(size=sc["ben"], sizemode="area", sizeref=sizeref, sizemin=6,
                        color=PALETTE[2], opacity=0.75, line=dict(width=1, color=T["card"])),
            hovertemplate="<b>%{text}</b><br>تكلفة المستفيد: %{x:,.1f} ريال<br>الأثر: %{y:.1f}%<extra></extra>"))
        fig.add_vline(x=K["cpb"], line_dash="dot", line_color=T["muted"])
        fig.add_hline(y=K["imp"], line_dash="dot", line_color=T["muted"])
        fig.update_xaxes(title_text="تكلفة المستفيد (ريال) ← الأقل أفضل")
        fig.update_yaxes(title_text="مؤشر الأثر %")
        show(style(fig, "الكفاءة مقابل الأثر لكل برنامج (حجم الدائرة = المستفيدون)"))
    else:
        empty_note("يلزم برنامجان على الأقل لرسم الكفاءة مقابل الأثر.")
with row5[1]:   # 10) خريطة حرارية: الأثر بالفرع والشهر
    brs, mos = list(gb.index), months_in
    if len(brs) >= 1 and len(mos) >= 1:
        z = []
        for b_ in brs:
            row = []
            for m_ in mos:
                g = d[(d[C_BRANCH] == b_) & (d[C_MONTH] == m_)]
                row.append(wavg(g[C_IMPACT], g[C_BEN]) if len(g) else np.nan)
            z.append(row)
        fig = go.Figure(go.Heatmap(z=z, x=mos, y=brs, colorscale="Tealgrn", reversescale=False,
                                   texttemplate="%{z:.0f}", hoverongaps=False,
                                   hovertemplate="<b>%{y}</b> — %{x}<br>الأثر: %{z:.1f}%<extra></extra>"))
        fig.update_xaxes(categoryorder="array", categoryarray=mos)
        show(style(fig, "مؤشر الأثر (%) حسب الفرع والشهر"))

# =============================================================================
# 8) البيانات المصفّاة + تنزيلها
# =============================================================================
with st.expander(f"عرض البيانات المصفّاة ({len(d_view):,} سجل)"):
    html_tbl = d_view.head(200).to_html(index=False, classes="data-table", border=0)
    html_tbl = "".join(line.strip() for line in html_tbl.splitlines())
    st.markdown(f'<div class="tbl-wrap">{html_tbl}</div>', unsafe_allow_html=True)
    if len(d_view) > 200:
        st.caption("عُرض أول 200 سجل فقط؛ نزّل الملف للحصول على الكل.")
    st.download_button("⬇️ تنزيل البيانات المصفّاة (CSV)", d_view.to_csv(index=False).encode("utf-8-sig"),
                       file_name="Filtered_Data.csv", mime="text/csv")

st.markdown(f'<div class="foot">{esc(ORG_NAME)} — {esc(ANALYST_TEXT)} — بيانات مجمّعة بلا هويات شخصية</div>',
            unsafe_allow_html=True)
