from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# OmniRetail Customer Analytics — focused interactive dashboard
# ============================================================

st.set_page_config(
    page_title="OmniRetail | Customer Insights",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "OmniRetail_Customer_Segments.xlsx"

SEGMENT_LABELS = {
    1: "Digital, Promotion-Dependent",
    2: "High-Value, Omnichannel",
    3: "Established, Store-Oriented",
}

SEGMENT_COLORS = {
    "Digital, Promotion-Dependent": "#69A7FF",
    "High-Value, Omnichannel": "#54D6A1",
    "Established, Store-Oriented": "#FFBD69",
}

SEGMENT_STORIES = {
    1: {
        "short": "Digital & deal responsive",
        "headline": "Make each promotion work harder.",
        "narrative": (
            "This is the largest group and the most promotion-responsive. "
            "Its lower average spending and higher complaint count make it worth "
            "testing more relevant offers and improving the experience—not simply "
            "sending more discounts."
        ),
        "objective": "Grow profitable repeat purchasing while improving customer experience.",
        "actions": [
            "Test targeted, purchase-linked offers against a control group.",
            "Investigate the reasons behind this group's higher complaint count.",
            "Use relevant loyalty milestones and complementary-product suggestions.",
        ],
        "kpis": [
            "Repeat purchase rate",
            "Average basket value",
            "Complaint rate",
            "Promotion redemption",
            "Incremental contribution margin",
        ],
        "caution": (
            "Promotion participation is an observed pattern, not proof that promotions "
            "cause low spending. Measure incremental sales and margin before scaling offers."
        ),
    },
    2: {
        "short": "High value & omnichannel",
        "headline": "Keep the relationship valuable.",
        "narrative": (
            "This smaller group has the highest average spending, basket value, loyalty "
            "points and satisfaction. The opportunity is to make staying worthwhile "
            "through relevant benefits and service—not to discount customers who already "
            "purchase at high value."
        ),
        "objective": "Retain high-value customers and protect long-term contribution margin.",
        "actions": [
            "Test personalised loyalty benefits and premium service experiences.",
            "Offer relevant complementary products based on purchase history.",
            "Keep online and in-store experiences consistent.",
        ],
        "kpis": [
            "Retention rate",
            "Repeat purchase rate",
            "Customer lifetime value",
            "Contribution margin per customer",
        ],
        "caution": (
            "High current spending does not guarantee future retention. Evaluate benefits "
            "against a baseline or control group."
        ),
    },
    3: {
        "short": "Established & store-oriented",
        "headline": "Make store visits more valuable.",
        "narrative": (
            "These customers visit stores most often and have the longest average tenure, "
            "but make a smaller share of purchases online. Focus on useful in-store "
            "experiences and convenient optional digital services rather than assuming "
            "they need to abandon physical stores."
        ),
        "objective": "Deepen store engagement and increase customer value.",
        "actions": [
            "Test relevant in-store loyalty benefits and complementary-product offers.",
            "Make digital ordering and account features convenient and optional.",
            "Personalise the experience using observed purchase history.",
        ],
        "kpis": [
            "Repeat store visits",
            "Average basket value",
            "Retention rate",
            "Digital adoption rate",
        ],
        "caution": (
            "Frequent visits do not necessarily imply higher profitability. Track purchases, "
            "retention and margin alongside visit frequency."
        ),
    },
}

COLORS = {
    "ink": "#EAF0F8",
    "muted": "#A9B7C9",
    "panel": "#182638",
    "border": "rgba(195, 214, 236, 0.16)",
    "accent": "#66B3FF",
}
PLOT_TEMPLATE = "plotly_dark"


# ---------------------------- Data ----------------------------
@st.cache_data
def load_data(path_string: str) -> pd.DataFrame:
    data = pd.read_excel(path_string)

    if "Customer_Segment" not in data.columns:
        raise ValueError(
            "The workbook must contain a 'Customer_Segment' column. "
            "Use data/OmniRetail_Customer_Segments.xlsx."
        )

    data["Customer_Segment"] = pd.to_numeric(
        data["Customer_Segment"], errors="coerce"
    )
    data = data.dropna(subset=["Customer_Segment"]).copy()
    data["Customer_Segment"] = data["Customer_Segment"].astype(int)
    data["Segment_Label"] = data["Customer_Segment"].map(SEGMENT_LABELS)
    data["Segment_Label"] = data["Segment_Label"].fillna(
        "Segment " + data["Customer_Segment"].astype(str)
    )
    return data


def mean_value(data: pd.DataFrame, column: str):
    if column not in data.columns:
        return None
    values = pd.to_numeric(data[column], errors="coerce").dropna()
    return float(values.mean()) if len(values) else None


def fmt(value, digits=2):
    if value is None or pd.isna(value):
        return "—"
    return f"{value:,.{digits}f}"


def ordered_segments(data: pd.DataFrame):
    found = set(data["Segment_Label"].dropna().unique())
    known = [
        SEGMENT_LABELS[key]
        for key in sorted(SEGMENT_LABELS)
        if SEGMENT_LABELS[key] in found
    ]
    return known + sorted(found - set(known))


def segment_mean_table(data: pd.DataFrame, columns: list[str]):
    columns = [column for column in columns if column in data.columns]
    if not columns:
        return pd.DataFrame()
    return (
        data.groupby(["Customer_Segment", "Segment_Label"])[columns]
        .mean(numeric_only=True)
        .reset_index()
    )


def style_fig(fig, height=370):
    fig.update_layout(
        template=PLOT_TEMPLATE,
        height=height,
        margin=dict(l=8, r=8, t=62, b=8),
        font=dict(family="Inter, Arial, sans-serif", size=12, color=COLORS["ink"]),
        title=dict(x=0.02, xanchor="left", font=dict(size=17)),
        legend_title_text="",
        transition_duration=350,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(190,210,230,0.12)", zeroline=False)
    return fig


def reset_filter_state():
    for key in list(st.session_state.keys()):
        if key == "segment_filter" or key.startswith("filter_"):
            del st.session_state[key]


if not DATA_PATH.exists():
    st.error(
        "I couldn't find the segmented customer workbook.\n\n"
        "**Expected file:** `data/OmniRetail_Customer_Segments.xlsx`\n\n"
        "Place the file in the existing `data` folder beside this app.py file."
    )
    st.stop()

try:
    df = load_data(str(DATA_PATH))
except Exception as exc:
    st.error(f"Could not load the segmented workbook: {exc}")
    st.stop()

if df.empty:
    st.error("The segmented workbook contains no usable customer records.")
    st.stop()


# ---------------------------- Styling ----------------------------
st.markdown(
    """
    <style>
      :root {
        --omni-panel: #182638;
        --omni-border: rgba(195, 214, 236, 0.16);
        --omni-muted: #A9B7C9;
      }

      .block-container {
        max-width: 1450px;
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
      }

      .omni-hero {
        padding: 1.35rem 1.55rem;
        border: 1px solid rgba(198, 222, 245, 0.13);
        border-radius: 18px;
        background:
          radial-gradient(circle at 88% 12%, rgba(65, 179, 184, 0.22), transparent 32%),
          linear-gradient(118deg, #10213A 0%, #183C55 65%, #155364 100%);
        margin-bottom: 0.8rem;
        animation: omniFadeUp .48s ease-out both;
      }

      .omni-eyebrow {
        text-transform: uppercase;
        letter-spacing: .13em;
        color: #A6DDE0;
        font-size: .76rem;
        font-weight: 700;
        margin-bottom: .55rem;
      }

      .omni-hero h1 {
        color: #F7FAFE;
        font-size: clamp(1.8rem, 3.4vw, 2.65rem);
        line-height: 1.12;
        margin: 0 0 .55rem 0;
      }

      .omni-hero p {
        color: #D7E5F0;
        font-size: 1rem;
        max-width: 850px;
        line-height: 1.55;
        margin: 0;
      }

      .omni-note {
        border-left: 3px solid #54D6A1;
        padding: .55rem .85rem;
        color: var(--omni-muted);
        margin: .4rem 0 1rem 0;
        font-size: .92rem;
      }

      /* Explicit contrast fix for Streamlit metric cards */
      div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #1A2A3E, #20364D) !important;
        border: 1px solid var(--omni-border) !important;
        border-radius: 14px !important;
        padding: .85rem 1rem !important;
        transition: transform .18s ease, border-color .18s ease,
                    box-shadow .18s ease;
        animation: omniFadeUp .42s ease-out both;
      }
      div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: rgba(102, 179, 255, .48) !important;
        box-shadow: 0 7px 22px rgba(0, 0, 0, .15);
      }
      div[data-testid="stMetric"] label,
      div[data-testid="stMetric"] label *,
      div[data-testid="stMetric"] [data-testid="stMetricLabel"],
      div[data-testid="stMetric"] [data-testid="stMetricLabel"] * {
        color: #B9C9DA !important;
      }
      div[data-testid="stMetric"] [data-testid="stMetricValue"],
      div[data-testid="stMetric"] [data-testid="stMetricValue"] * {
        color: #F6FAFF !important;
      }
      div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: #8DDDB6 !important;
      }

      div[data-testid="stPlotlyChart"] {
        animation: omniFadeUp .42s ease-out both;
      }

      .omni-story {
        background: rgba(124, 165, 205, .07);
        border: 1px solid var(--omni-border);
        padding: 1rem 1.05rem;
        border-radius: 14px;
        height: 100%;
      }
      .omni-story .story-kicker {
        color: #A6DDE0;
        text-transform: uppercase;
        letter-spacing: .09em;
        font-size: .74rem;
        font-weight: 700;
        margin-bottom: .45rem;
      }
      .omni-story h3 {
        color: #F3F7FC;
        font-size: 1.1rem;
        margin: 0 0 .55rem 0;
      }
      .omni-story p {
        color: #C1CFDE;
        line-height: 1.52;
        font-size: .92rem;
        margin: 0;
      }

      .omni-section-caption {
        color: var(--omni-muted);
        font-size: .93rem;
        margin-top: -.35rem;
        margin-bottom: .8rem;
      }

      @keyframes omniFadeUp {
        from { opacity: 0; transform: translateY(7px); }
        to   { opacity: 1; transform: translateY(0); }
      }

      @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
          animation-duration: .01ms !important;
          transition-duration: .01ms !important;
        }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------- Sidebar filters ----------------------------
st.sidebar.title("Explore the customers")
st.sidebar.caption(
    "Start with all customers, then narrow the view to answer a specific question."
)

available_segments = sorted(df["Customer_Segment"].unique().tolist())
selected_segments = st.sidebar.multiselect(
    "Customer segments",
    options=available_segments,
    default=available_segments,
    key="segment_filter",
    format_func=lambda value: (
        f"Segment {value} · {SEGMENT_LABELS.get(value, 'Other')}"
    ),
)

filtered = df[df["Customer_Segment"].isin(selected_segments)].copy()

filter_specs = [
    ("Region", "Region"),
    ("City_Tier", "City tier"),
    ("Membership_Tier", "Membership tier"),
    ("Preferred_Category", "Preferred category"),
    ("Acquisition_Channel", "Acquisition channel"),
]

for column, label in filter_specs:
    if column not in filtered.columns:
        continue
    value_col = filtered[column].fillna("Unknown").astype(str)
    options = sorted(value_col.unique().tolist())
    chosen = st.sidebar.multiselect(
        label,
        options=options,
        default=options,
        key=f"filter_{column}",
    )
    filtered = filtered[
        filtered[column].fillna("Unknown").astype(str).isin(chosen)
    ]

st.sidebar.divider()
st.sidebar.caption("Changes update the figures, summaries and segment stories.")
st.sidebar.button(
    "Reset all filters",
    use_container_width=True,
    on_click=reset_filter_state,
)


# ---------------------------- Header ----------------------------
st.markdown(
    """
    <div class="omni-hero">
      <div class="omni-eyebrow">Retail customer intelligence</div>
      <h1>OmniRetail Customer Analytics</h1>
      <p>Get to know the customers behind the numbers. Explore the segments, understand what makes each group different, and find practical next steps.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if filtered.empty:
    st.warning("No customers match these filters. Try widening your selection in the sidebar.")
    st.stop()

customer_count = (
    filtered["Customer_ID"].nunique()
    if "Customer_ID" in filtered.columns
    else len(filtered)
)
shown_segments = filtered["Customer_Segment"].nunique()
mean_spend = mean_value(filtered, "Annual_Spend_000")
mean_satisfaction = mean_value(filtered, "Satisfaction_Score")
mean_complaints = mean_value(filtered, "Complaints_Year")

st.markdown(
    f'<div class="omni-note">You are viewing <strong>{customer_count:,}</strong> customers '
    f'across <strong>{shown_segments}</strong> segment(s). '
    'Use the filters to focus the story; the figures below respond to your selection.</div>',
    unsafe_allow_html=True,
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Customers in view", f"{customer_count:,}")
k2.metric(
    "Mean annual spend",
    fmt(mean_spend),
    help="Mean of Annual_Spend_000, shown in the source dataset's recorded units.",
)
k3.metric(
    "Mean satisfaction",
    f"{mean_satisfaction:.2f}/10" if mean_satisfaction is not None else "—",
)
k4.metric(
    "Mean complaints per year",
    fmt(mean_complaints),
)

st.caption(
    "A note on the numbers: segment averages describe this dataset. "
    "They do not prove why customers behave this way or which intervention will work."
)

overview_tab, stories_tab, compare_tab, playbook_tab = st.tabs(
    ["At a glance", "Meet the segments", "Compare behaviours", "Business playbook"]
)


# ============================ AT A GLANCE ============================
with overview_tab:
    st.subheader("A quick read")
    st.markdown(
        '<div class="omni-section-caption">Three groups, three different conversations—not three labels to treat as fixed truths.</div>',
        unsafe_allow_html=True,
    )

    counts = (
        filtered.groupby(["Customer_Segment", "Segment_Label"])
        .size()
        .reset_index(name="Customers")
    )
    counts["Share"] = counts["Customers"] / counts["Customers"].sum() * 100
    order = ordered_segments(filtered)

    left, right = st.columns([1.1, 1])

    with left:
        fig = px.bar(
            counts,
            x="Segment_Label",
            y="Customers",
            color="Segment_Label",
            text="Customers",
            category_orders={"Segment_Label": order},
            color_discrete_map=SEGMENT_COLORS,
            title="Who's in the current view?",
            hover_data={"Share": ":.1f", "Customers": ":,"},
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(
            showlegend=False,
            xaxis_title="",
            yaxis_title="Customers",
            yaxis_rangemode="tozero",
        )
        st.plotly_chart(style_fig(fig, 355), use_container_width=True)

    with right:
        fig = px.pie(
            counts,
            values="Customers",
            names="Segment_Label",
            hole=0.63,
            color="Segment_Label",
            color_discrete_map=SEGMENT_COLORS,
            title="How the current view is split",
        )
        fig.update_traces(
            textposition="inside",
            textinfo="percent",
            hovertemplate="%{label}<br>%{value:,} customers<br>%{percent}<extra></extra>",
        )
        fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.16))
        st.plotly_chart(style_fig(fig, 355), use_container_width=True)

    st.subheader("What stands out")
    story_columns = st.columns(3)
    story_cards = [
        (
            "01 · Segment 1",
            "Promotions & experience",
            "This group is especially promotion-responsive and reports more complaints on average. "
            "Test whether better-targeted offers and service fixes add value.",
        ),
        (
            "02 · Segment 2",
            "Protect customer value",
            "This group leads on average spend and satisfaction. Focus on retaining relationships "
            "rather than automatically offering deeper discounts.",
        ),
        (
            "03 · Segment 3",
            "Make store visits count",
            "This group visits stores most often and buys a smaller share online. Improve the store "
            "experience and offer digital convenience as an option.",
        ),
    ]
    for column, (kicker, title, body) in zip(story_columns, story_cards):
        with column:
            st.markdown(
                f"""
                <div class="omni-story">
                  <div class="story-kicker">{kicker}</div>
                  <h3>{title}</h3>
                  <p>{body}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================ MEET THE SEGMENTS ============================
with stories_tab:
    st.subheader("Meet one segment at a time")
    st.markdown(
        '<div class="omni-section-caption">Pick a group to see its story, a few important numbers, and what the business could test next.</div>',
        unsafe_allow_html=True,
    )

    current_ids = sorted(filtered["Customer_Segment"].unique().tolist())
    selected_id = st.selectbox(
        "Which customer group would you like to understand?",
        options=current_ids,
        format_func=lambda value: (
            f"Segment {value} · {SEGMENT_LABELS.get(value, 'Other')}"
        ),
        key="story_segment",
    )

    segment_df = filtered[filtered["Customer_Segment"] == selected_id]
    label = SEGMENT_LABELS.get(selected_id, f"Segment {selected_id}")
    story = SEGMENT_STORIES.get(selected_id, {})

    st.markdown(f"### {story.get('headline', label)}")
    st.write(story.get("narrative", "Explore the statistics for this group below."))
    st.info(f"**Business objective:** {story.get('objective', 'Understand and engage this group.')}")

    count = (
        segment_df["Customer_ID"].nunique()
        if "Customer_ID" in segment_df.columns
        else len(segment_df)
    )
    spend = mean_value(segment_df, "Annual_Spend_000")
    online = mean_value(segment_df, "Online_Purchase_Pct")
    satisfaction = mean_value(segment_df, "Satisfaction_Score")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Customers in view", f"{count:,}")
    m2.metric("Mean annual spend", fmt(spend))
    m3.metric("Online purchase share", f"{online:.1f}%" if online is not None else "—")
    m4.metric(
        "Satisfaction",
        f"{satisfaction:.2f}/10" if satisfaction is not None else "—",
    )

    with st.expander("See more of this group's profile"):
        detailed_metrics = [
            ("Mean basket value", "Avg_Basket_Value"),
            ("Mean loyalty points", "Loyalty_Points"),
            ("Mean complaints per year", "Complaints_Year"),
            ("Mean online orders per year", "Online_Orders_Year"),
            ("Mean store visits per year", "Store_Visits_Year"),
            ("Mean promotion purchase share", "Promo_Purchase_Pct"),
            ("Mean tenure (months)", "Tenure_Months"),
        ]
        profile_rows = [
            {"Measure": name, "Average": mean_value(segment_df, col)}
            for name, col in detailed_metrics
            if col in segment_df.columns
        ]
        profile_table = pd.DataFrame(profile_rows)
        if not profile_table.empty:
            profile_table["Average"] = profile_table["Average"].round(2)
            st.dataframe(profile_table, hide_index=True, use_container_width=True)

        category_specs = [
            ("Membership_Tier", "Membership tier"),
            ("Preferred_Category", "Preferred category"),
            ("Acquisition_Channel", "Acquisition channel"),
            ("Region", "Region"),
        ]
        category_specs = [pair for pair in category_specs if pair[0] in segment_df.columns]
        if category_specs:
            category_col, category_title = st.selectbox(
                "Explore a characteristic",
                options=category_specs,
                format_func=lambda pair: pair[1],
                key=f"category_{selected_id}",
            )
            mix = (
                segment_df[category_col]
                .fillna("Unknown")
                .astype(str)
                .value_counts(normalize=True)
                .mul(100)
                .rename_axis("Category")
                .reset_index(name="Share")
                .sort_values("Share")
            )
            fig = px.bar(
                mix,
                x="Share",
                y="Category",
                orientation="h",
                text_auto=".1f",
                title=f"{category_title}: share within this filtered group",
            )
            fig.update_layout(xaxis_title="Share (%)", yaxis_title="")
            st.plotly_chart(style_fig(fig, max(300, 40 * len(mix))), use_container_width=True)

    st.markdown("#### What could we try?")
    for action in story.get("actions", []):
        st.markdown(f"- {action}")
    st.caption(f"**Keep in mind:** {story.get('caution', '')}")


# ============================ COMPARE BEHAVIOURS ============================
with compare_tab:
    st.subheader("Compare the behaviours that matter")
    st.markdown(
        '<div class="omni-section-caption">Choose one measure at a time to keep comparisons readable.</div>',
        unsafe_allow_html=True,
    )

    measure_options = [
        ("Annual spending", "Annual_Spend_000", "Mean spending (recorded units)"),
        ("Basket value", "Avg_Basket_Value", "Mean basket value (recorded units)"),
        ("Satisfaction", "Satisfaction_Score", "Mean satisfaction (0–10)"),
        ("Online purchase share", "Online_Purchase_Pct", "Mean share (%)"),
        ("Promotion purchase share", "Promo_Purchase_Pct", "Mean share (%)"),
        ("Store visits per year", "Store_Visits_Year", "Mean visits per year"),
        ("Online orders per year", "Online_Orders_Year", "Mean orders per year"),
        ("Complaints per year", "Complaints_Year", "Mean complaints per year"),
    ]
    measure_options = [item for item in measure_options if item[1] in filtered.columns]

    selected_measure = st.selectbox(
        "What would you like to compare?",
        options=measure_options,
        format_func=lambda item: item[0],
        key="comparison_measure",
    )
    _, measure_col, axis_label = selected_measure

    comparison = (
        filtered.groupby(["Customer_Segment", "Segment_Label"], as_index=False)[measure_col]
        .mean()
    )
    comparison["Customers"] = filtered.groupby("Customer_Segment").size().reindex(
        comparison["Customer_Segment"]
    ).to_numpy()
    fig = px.bar(
        comparison,
        x="Segment_Label",
        y=measure_col,
        color="Segment_Label",
        text_auto=".2f",
        category_orders={"Segment_Label": ordered_segments(filtered)},
        color_discrete_map=SEGMENT_COLORS,
        title=f"{selected_measure[0]} by segment",
        hover_data={"Customers": ":,", measure_col: ":.2f"},
    )
    fig.update_layout(xaxis_title="", yaxis_title=axis_label, showlegend=False)
    st.plotly_chart(style_fig(fig, 390), use_container_width=True)

    with st.expander("Explore a relationship between two variables"):
        possible_x = [
            ("Annual income", "Annual_Income_000"),
            ("Age", "Age"),
            ("Store visits per year", "Store_Visits_Year"),
            ("Online orders per year", "Online_Orders_Year"),
        ]
        possible_y = [
            ("Annual spending", "Annual_Spend_000"),
            ("Basket value", "Avg_Basket_Value"),
            ("Online purchase share", "Online_Purchase_Pct"),
            ("Promotion purchase share", "Promo_Purchase_Pct"),
            ("Satisfaction", "Satisfaction_Score"),
        ]
        possible_x = [p for p in possible_x if p[1] in filtered.columns]
        possible_y = [p for p in possible_y if p[1] in filtered.columns]

        x_col1, x_col2 = st.columns(2)
        with x_col1:
            x_choice = st.selectbox(
                "Horizontal axis",
                options=possible_x,
                format_func=lambda item: item[0],
                key="relationship_x",
            )
        with x_col2:
            y_choice = st.selectbox(
                "Vertical axis",
                options=possible_y,
                format_func=lambda item: item[0],
                key="relationship_y",
            )

        plot_data = filtered.dropna(subset=[x_choice[1], y_choice[1]])
        fig = px.scatter(
            plot_data,
            x=x_choice[1],
            y=y_choice[1],
            color="Segment_Label",
            color_discrete_map=SEGMENT_COLORS,
            opacity=0.65,
            hover_data=[
                c for c in ["Customer_ID", "Membership_Tier", "Region"]
                if c in plot_data.columns
            ],
            title=f"{x_choice[0]} vs. {y_choice[0]}",
        )
        fig.update_layout(
            xaxis_title=x_choice[0],
            yaxis_title=y_choice[0],
            legend_title="Segment",
        )
        st.plotly_chart(style_fig(fig, 390), use_container_width=True)

    with st.expander("View or download filtered customer records"):
        st.caption(
            "Customer-level data is hidden unless requested. The CSV download contains "
            "only records matching the active filters."
        )
        show_records = st.checkbox("Show a sample of customer records", value=False)
        columns = [
            "Customer_ID", "Segment_Label", "Age", "Annual_Income_000",
            "Annual_Spend_000", "Avg_Basket_Value", "Satisfaction_Score",
            "Complaints_Year", "Online_Purchase_Pct", "Promo_Purchase_Pct",
            "Membership_Tier", "Region", "Preferred_Category",
        ]
        columns = [col for col in columns if col in filtered.columns]
        if show_records:
            st.dataframe(
                filtered[columns].head(500),
                use_container_width=True,
                hide_index=True,
            )
        st.download_button(
            "Download filtered records as CSV",
            data=filtered[columns].to_csv(index=False).encode("utf-8"),
            file_name="omniRetail_filtered_customers.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ============================ BUSINESS PLAYBOOK ============================
with playbook_tab:
    st.subheader("Turn an insight into a sensible next step")
    st.markdown(
        '<div class="omni-section-caption">These are ideas to test—not promises about results.</div>',
        unsafe_allow_html=True,
    )

    for segment_id in sorted(available_segments):
        if segment_id not in set(filtered["Customer_Segment"].unique()):
            continue
        label = SEGMENT_LABELS.get(segment_id, f"Segment {segment_id}")
        story = SEGMENT_STORIES.get(segment_id, {})
        segment_count = (
            filtered.loc[
                filtered["Customer_Segment"] == segment_id, "Customer_ID"
            ].nunique()
            if "Customer_ID" in filtered.columns
            else int((filtered["Customer_Segment"] == segment_id).sum())
        )
        with st.expander(
            f"Segment {segment_id} · {label} · {segment_count:,} customers",
            expanded=False,
        ):
            st.markdown(f"**Business objective:** {story.get('objective', '')}")
            st.markdown("**Possible actions**")
            for action in story.get("actions", []):
                st.markdown(f"- {action}")
            st.markdown("**How we could measure it**")
            st.markdown(", ".join(story.get("kpis", [])))
            st.info(f"**Risk to watch:** {story.get('caution', '')}")

    st.markdown("#### Three measurement principles")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**1 · Know the baseline**")
        st.write("Record the current result before launching an intervention.")
    with c2:
        st.markdown("**2 · Test fairly**")
        st.write("Use a comparable control group where feasible to estimate incremental impact.")
    with c3:
        st.markdown("**3 · Follow value**")
        st.write("Track contribution margin—not just revenue or offer redemption.")


# ---------------------------- Methodology ----------------------------
with st.expander("About the data and methods"):
    st.markdown(
        """
        **Source:** `data/OmniRetail_Customer_Segments.xlsx`

        The analysis is based on 5,200 unique customers and the PCA-based three-cluster
        K-Means solution documented in the accompanying notebooks. Twelve standardised
        numerical features were reduced to six principal components, retaining about
        83.99% of variance. The recorded silhouette score for the selected solution is 0.448.

        A comparison with K-Means on the original standardised features returned an
        Adjusted Rand Index of 0.9994, indicating near-identical assignments.

        **Interpretation:** segment averages are descriptive, not causal explanations.
        Retention, campaign uplift and profitability require appropriate follow-up,
        transaction, campaign or cost data.
        """
    )
    st.caption("Variables available in this workbook:")
    st.write(", ".join(map(str, df.columns)))

st.divider()
st.caption(
    "OmniRetail Customer Analytics · Built with Streamlit and Plotly · "
    "Explore the pattern, then test the business idea."
)
