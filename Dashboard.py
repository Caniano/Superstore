import streamlit as st
import pandas as pd
import plotly.express as px
import os
import platform
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Superstore!!!", page_icon=":bar_chart:", layout="wide")
st.title(" :bar_chart: Sample SuperStore EDA")
st.markdown('<style>div.block-container{padding-top:3rem;}</style>', unsafe_allow_html=True)

# File uploader and delimiter selector
st.sidebar.subheader("📁 Upload your file")
fl = st.file_uploader(":file_folder: Upload a file", type=["csv", "txt", "xlsx", "xls"])
delimiter = st.sidebar.selectbox("Delimiter (for CSV/TXT)", [",", ";", "\t", "|"], index=0)

# File handling
if fl is not None:
    filename = fl.name
    ext = filename.split(".")[-1].lower()

    try:
        if ext in ["csv", "txt"]:
            content = fl.getvalue().decode('ISO-8859-1')
            st.write("**Preview file content (first 10 lines):**")
            st.text("\n".join(content.splitlines()[:10]))

            df = pd.read_csv(fl, encoding="ISO-8859-1", sep=delimiter, on_bad_lines='skip', engine='python')
        
        elif ext in ["xlsx", "xls"]:
            df = pd.read_excel(fl)
            st.success("✅ Excel file uploaded successfully.")

        else:
            st.error("❌ Unsupported file type. Please upload a CSV, TXT, or Excel file.")
            st.stop()
    except Exception as e:
        st.error(f"❌ Failed to read uploaded file: {e}")
        st.stop()

else:
    default_path = "/Users/kanishksingh/Desktop/Project_Dashboard/Superstore.csv"
    if os.path.exists(default_path):
        try:
            df = pd.read_csv(default_path, encoding="ISO-8859-1")
            st.info("Using default local file (Superstore.csv)")
        except Exception as e:
            st.error(f"❌ Error reading default file: {e}")
            st.stop()
    else:
        st.warning("⚠️ No file uploaded and default file not found. Please upload a data file.")
        st.stop()

# Data validation
if "Order Date" not in df.columns:
    st.error("❌ 'Order Date' column is missing in the uploaded dataset.")
    st.stop()

df["Order Date"] = pd.to_datetime(df["Order Date"], errors='coerce')
df = df.dropna(subset=["Order Date"])

# Date filter UI
col1, col2 = st.columns((2))
startDate = df["Order Date"].min()
endDate = df["Order Date"].max()

with col1:
    date1 = pd.to_datetime(st.date_input("Start Date", startDate))

with col2:
    date2 = pd.to_datetime(st.date_input("End Date", endDate))

df = df[(df["Order Date"] >= date1) & (df["Order Date"] <= date2)].copy()

# Sidebar filters
st.sidebar.header("Choose your filter:")
region = st.sidebar.multiselect("Pick your Region", df["Region"].unique())
state = st.sidebar.multiselect("Pick the State", df["State"].unique())
city = st.sidebar.multiselect("Pick the City", df["City"].unique())

# Apply filters
filtered_df = df.copy()
if region:
    filtered_df = filtered_df[filtered_df["Region"].isin(region)]
if state:
    filtered_df = filtered_df[filtered_df["State"].isin(state)]
if city:
    filtered_df = filtered_df[filtered_df["City"].isin(city)]

# Category Bar Chart
category_df = filtered_df.groupby("Category", as_index=False)["Sales"].sum()
with col1:
    st.subheader("Category wise Sales")
    fig = px.bar(category_df, x="Category", y="Sales", text=['${:,.2f}'.format(x) for x in category_df["Sales"]],
                 template="seaborn")
    st.plotly_chart(fig, use_container_width=True)

# Region Pie Chart
with col2:
    st.subheader("Region wise Sales")
    fig = px.pie(filtered_df, values="Sales", names="Region", hole=0.5)
    st.plotly_chart(fig, use_container_width=True)

# Data download for Category and Region
cl1, cl2 = st.columns((2))
with cl1:
    with st.expander("Category View Data"):
        st.write(category_df.style.background_gradient(cmap="Blues"))
        st.download_button("Download Category Data", category_df.to_csv(index=False), "Category.csv", "text/csv")

with cl2:
    with st.expander("Region View Data"):
        region_df = filtered_df.groupby("Region", as_index=False)["Sales"].sum()
        st.write(region_df.style.background_gradient(cmap="Oranges"))
        st.download_button("Download Region Data", region_df.to_csv(index=False), "Region.csv", "text/csv")

# Time Series
filtered_df["month_year"] = filtered_df["Order Date"].dt.to_period("M")
linechart = pd.DataFrame(filtered_df.groupby(filtered_df["month_year"].dt.strftime("%Y-%b"))["Sales"].sum()).reset_index()

st.subheader("📈 Time Series Analysis")
fig2 = px.line(linechart, x="month_year", y="Sales", labels={"Sales": "Amount"}, template="gridon")
st.plotly_chart(fig2, use_container_width=True)

with st.expander("View Time Series Data"):
    st.write(linechart.style.background_gradient(cmap="Blues"))
    st.download_button("Download Time Series Data", linechart.to_csv(index=False), "TimeSeries.csv", "text/csv")

# TreeMap
st.subheader("🗂 Hierarchical view of Sales using TreeMap")
fig3 = px.treemap(filtered_df, path=["Region", "Category", "Sub-Category"], values="Sales", color="Sub-Category")
fig3.update_layout(margin=dict(t=50, l=25, r=25, b=25))
st.plotly_chart(fig3, use_container_width=True)

# Segment and Category Pie Charts
chart1, chart2 = st.columns((2))
with chart1:
    st.subheader("Segment wise Sales")
    fig = px.pie(filtered_df, values="Sales", names="Segment", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with chart2:
    st.subheader("Category wise Sales")
    fig = px.pie(filtered_df, values="Sales", names="Category", template="gridon")
    st.plotly_chart(fig, use_container_width=True)

# Summary Table
import plotly.figure_factory as ff
st.subheader(":point_right: Month wise Sub-Category Sales Summary")
with st.expander("Summary Table"):
    df_sample = df[["Region", "State", "City", "Category", "Sales", "Profit", "Quantity"]].head(5)
    fig = ff.create_table(df_sample, colorscale="Cividis")
    st.plotly_chart(fig, use_container_width=True)

    filtered_df["month"] = filtered_df["Order Date"].dt.month_name()
    pivot_table = pd.pivot_table(filtered_df, values="Sales", index="Sub-Category", columns="month")
    st.write(pivot_table.style.background_gradient(cmap="Blues"))

# Scatter Plot
scatter_fig = px.scatter(filtered_df, x="Sales", y="Profit", size="Quantity",
                         title="Relationship between Sales and Profits using Scatter Plot")
st.plotly_chart(scatter_fig, use_container_width=True)

with st.expander("View Data"):
    st.write(filtered_df.iloc[:500, 1:20:2].style.background_gradient(cmap="Oranges"))

# Full dataset download
st.download_button("Download Full Dataset", df.to_csv(index=False), "FullData.csv", "text/csv")