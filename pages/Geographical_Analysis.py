import streamlit as st
import pandas as pd
import io
import msoffcrypto
from dbclean import clean_data
import folium
import json
import matplotlib.pyplot as plt
import seaborn as sns
from streamlit_option_menu import option_menu
from streamlit_folium import folium_static
from branca.colormap import linear
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import numpy as np
from msoffcrypto.exceptions import DecryptionError

# Create a connection object.
conn_postcodes = st.connection("gsheets_postcodes", type=GSheetsConnection)
df_postcodes = conn_postcodes.read(spreadsheet = 'https://docs.google.com/spreadsheets/d/1fJ-SJPjldp8-LuaT9wdp_FoS518gSNlkN5wN849EUlo/edit?usp=sharing')
conn_wards = st.connection("gsheets_wards", type=GSheetsConnection)
df_wards = conn_wards.read(spreadsheet = 'https://docs.google.com/spreadsheets/d/1tmk5cTIc3TNScbSeJgVMKcsCieVLtiY8YjS1Ma3rRLo/edit?usp=sharing')


age_groups = {'0-4': range(0, 5), '5-11': range(5, 12), '12-16': range(12, 17), '17-24': range(17, 25),
              '25-34': range(25, 35), '35-44': range(35, 45), '45-64': range(45, 65), '65+': range(65, 91)}


if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

if 'filter_foodbank' not in st.session_state:
    st.session_state.filter_foodbank = []

if 'filter_household_size' not in st.session_state:
    st.session_state.filter_household_size = (0, 0)

if 'filter_age_group' not in st.session_state:
    st.session_state.filter_age_group = []

if 'filter_repeat_addresses' not in st.session_state:
    st.session_state.filter_repeat_addresses = True

if 'filter_crisis_type' not in st.session_state:
    st.session_state.filter_crisis_type = []

if 'filter_voucher_status' not in st.session_state:
    st.session_state.filter_voucher_status = 'Both'

if 'filter_delivery' not in st.session_state:
    st.session_state.filter_delivery = 'Both'

if 'expander_title' not in st.session_state:
    st.session_state.expander_title = 'Upload Excel file'


def set_custom_styles():
    # Apply app-wide styles
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
        width: 400px !important;
        }
        [data-baseweb="tab"] {
            width: 100% !important;
            flex-grow: 1;
            justify-content: center;
            font-size: 18px;
        }
        .stButton>button {
            background-color: #00AB52;
            color: white;
            font-family: Arial;
        }
        h1 {
            text-align: center;
            color: #00AB52;
            font-family: Arial;
            font-size: 24px;
        }
        </style>
        """, unsafe_allow_html=True
    )

def set_expander_title():
    print(st.session_state.data_loaded)
    if st.session_state.expander_title != 'Upload Excel file' and st.session_state.data_loaded:
        st.session_state.expander_title = 'Upload Excel file'

def load_excel(uploaded_file, password=None) -> tuple[pd.DataFrame, bool]:
    """
    Load the excel file into pd.dataframe

    Parameters:
        uploaded_file: The excel file to be transftered
        password: the password for the excel
    Returns:
        tuple: A tuple containing:
            - pd.DataFrame: The pd.DataFrame loaded
            - bool: True if successfully loaded
    """

    try:    # Try to load the file with a password
        decrypted = io.BytesIO()
        office_file = msoffcrypto.OfficeFile(uploaded_file)
        office_file.load_key(password=password)

        office_file.decrypt(decrypted)
        decrypted.seek(0)
        df = pd.read_excel(decrypted, engine='openpyxl')
        return df, True  # Successfully loaded
    except DecryptionError as e:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        return df, True  # Successfully loaded
    except Exception:
        return None, False  # Failed to load

@st.cache_data(show_spinner=False)
def load_data(file, password=None):
    df, success = load_excel(file, password=password)
    if success:
        cleaned_df = clean_data(df)
        unique_postcodes = cleaned_df['postcode'].unique()

        postcode_coords = {
            row['postcode']: (get_lat_lon(row['postcode']))
            for _, row in df_postcodes[df_postcodes['postcode'].isin(unique_postcodes)].iterrows()
        }

        # Add latitude and longitude to cleaned_df using the postcode_coords dictionary
        cleaned_df['latitude'] = cleaned_df['postcode'].map(lambda x: postcode_coords.get(x, (None, None))[0])
        cleaned_df['longitude'] = cleaned_df['postcode'].map(lambda x: postcode_coords.get(x, (None, None))[1])

        cleaned_df = cleaned_df.dropna(subset=['latitude', 'longitude'])

        return cleaned_df, success
    return None, success

def get_lat_lon(postcode):
    postcode_row = df_postcodes[df_postcodes['postcode'] == postcode]
    if not postcode_row.empty:
        return postcode_row['latitude'].values[0], postcode_row['longitude'].values[0]
    else:
        return None, None

@st.cache_resource(show_spinner=False)
def postcode_map(df):
    if df.shape[0] > 0:
        df['unique_address_pair'] = df[['address1', 'address2']].apply(tuple, axis=1)

        postcode_counts_df = (
            df.groupby('postcode')
            .agg(count=('postcode', 'size'), latitude=('latitude', 'first'), longitude=('longitude', 'first'), unique_count=('unique_address_pair', 'nunique'))
            .reset_index()
        )

        # Define color scale
        colormap = linear.YlOrRd_09.scale(0, postcode_counts_df['count'].max())
        colormap.caption = 'Postcode Voucher Count'

        # Initialize folium map at central coordinates
        map = folium.Map(
            location=[postcode_counts_df['latitude'].mean(), postcode_counts_df['longitude'].mean()],
            zoom_start=10
        )

        # Add circle markers for each postcode
        for _, row in postcode_counts_df.iterrows():
            color = colormap(row['count'])
            folium.CircleMarker(
                location=(row['latitude'], row['longitude']),
                radius=5,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                tooltip=f" Postcode: {row['postcode']}<br>Total vouchers: {row['count']}<br>Distinct household vouchers: {row['unique_count']}"
            ).add_to(map)

        # Display map with color scale
        colormap.add_to(map)
        folium_static(map)
    else:
        st.warning("No vouchers available to plot on the map. Please adjust your filters to ensure valid data for plotting.")


def style_function(feature, colormap):
    population_percentage = feature['properties']['population_percentage']
    fill_color = colormap(population_percentage)

    return {
        'fillColor': fill_color,
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.7,
    }

@st.cache_data(show_spinner=False)
def ward_population(df):
    ward_population_df = df.groupby('ward')[['household_size']+list(age_groups.keys())].sum().reset_index()

    df_wards['population'] = df_wards['All ages '].str.replace(',', '').astype(int)

    # Merge with df_wards to get the 'All ages' column
    ward_population_df = ward_population_df.merge(df_wards,  left_on='ward', right_on='Ward Name', how='left').dropna()

    # Calculate population percentage of 'All ages' for each ward
    ward_population_df['population_percentage'] = round((ward_population_df['household_size'] / ward_population_df['population']) * 100,2)

    ward_population_df['90'] = ward_population_df['90+']
    for age_group, ages in age_groups.items():
        ward_population_df[f"{age_group}_percentage"] = (
            ward_population_df[age_group]/
            ward_population_df[[str(age) for age in ages]].sum(axis=1)
        ) * 100

    # Compute the sum of age group percentages
    ward_population_df["age_group_total_percentage"] = ward_population_df[[f"{age_group}_percentage" for age_group in age_groups]].sum(axis=1)

    # Compute the scaling factor for each row
    ward_population_df["scaling_factor"] = ward_population_df["population_percentage"] / ward_population_df["age_group_total_percentage"]

    # Scale each age group percentage
    for age_group in age_groups:
        ward_population_df[f"{age_group}_scaled_percentage"] = round((
            ward_population_df[f"{age_group}_percentage"] * ward_population_df["scaling_factor"]
        ),2)

    ward_population_df = ward_population_df.drop('Ward Name', axis=1)

    return ward_population_df


@st.cache_resource(show_spinner=False)
def ward_map(df):
    if df.shape[0] > 0:
        ward_population_df = ward_population(df)

        with open('wards_boundaries.geojson', 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        ward_boundaries = {'type': 'FeatureCollection', 'features': []}
        for feature in geojson_data['features']:
            ward_code = feature['properties']['WD24CD']
            # Check if the ward_name exists in the ward_population_df DataFrame
            if ward_code in ward_population_df['Ward Code'].values:
                # Get the population percentage from the DataFrame
                population_percentage = round(ward_population_df[ward_population_df['Ward Code'] == ward_code]['population_percentage'].values[0], 2)
                population = int(ward_population_df[ward_population_df['Ward Code'] == ward_code]['population'].values[0])
                household_size = int(ward_population_df[ward_population_df['Ward Code'] == ward_code]['household_size'].values[0])
                # Add it to the feature properties
                feature['properties']['population_percentage'] = population_percentage
                feature['properties']['population'] = population
                feature['properties']['household_size'] = household_size
                ward_boundaries['features'].append(feature)

        latitudes = [feature["properties"]["LAT"] for feature in ward_boundaries["features"]]
        longitudes = [feature["properties"]["LONG"] for feature in ward_boundaries["features"]]
        average_lat = sum(latitudes) / len(latitudes)
        average_lon = sum(longitudes) / len(longitudes)

        map = folium.Map(location=[average_lat, average_lon], zoom_start=10)
        population_percentages = [feature['properties']['population_percentage'] for feature in ward_boundaries['features']]
        colormap = linear.YlGnBu_09.scale(min(population_percentages), max(population_percentages))
        colormap.caption = 'Voucher usage per capita across wards'

        folium.GeoJson(
            ward_boundaries,
            style_function=lambda feature: style_function(feature, colormap),
            tooltip=folium.GeoJsonTooltip(
                fields=['WD24NM', 'population', 'household_size', 'population_percentage'],
                aliases=['Ward:', 'Ward population:', 'Number of people using vouchers:', 'Voucher usage per capita (%):'],
                localize=True
            )
        ).add_to(map)

        colormap.add_to(map)
        folium_static(map)
    else:
        st.warning(
            "No data available to plot on the map. Please adjust your filters to ensure valid data for plotting.")

#GRAPHS

# Monthly Vouchers Graph
def monthly_voucher_graph(df):
    if df.shape[0] > 0:
        df["created at"] = pd.to_datetime(df["created at"])
        df["month_name"] = df["created at"].dt.strftime('%b')

        months_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        df["month_name"] = pd.Categorical(df["month_name"], categories=months_order, ordered=True)

        # Applying filter for selected foodbanks
        selected_foodbanks = st.session_state.filter_foodbank
        filtered_df = df[df["assigned food bank centre"].isin(selected_foodbanks)]

        # Monthly counts for selected foodbanks
        monthly_counts = filtered_df.groupby(["assigned food bank centre", "month_name"]).size().reset_index(name="voucher_count")

        # Combine df for "All Foodbanks"
        combined_counts = df.groupby("month_name").size().reset_index(name="voucher_count")
        combined_counts["assigned food bank centre"] = "All Foodbanks"

        # Combine data
        monthly_counts = pd.concat([monthly_counts, combined_counts], ignore_index=True)

        # Plotting a line graph
        fig = px.line(
            monthly_counts,
            x="month_name",
            y="voucher_count",
            color="assigned food bank centre",
            title="Monthly Vouchers Issued",
            labels={"month_name": "Month", "voucher_count": "Vouchers Issued", "assigned food bank centre": "Foodbank"},
        )

        fig.update_layout(
            legend_title_text="Foodbanks",
        )
        st.plotly_chart(fig)



#Vouchers Issued Over Time (Historical)
def historical_voucher_graph(df):
    if df.shape[0] > 0:
        df["created at"]= pd.to_datetime(df["created at"])
        df["date"]= df["created at"].dt.date

        #applying foodbank filter
        selected_foodbanks = st.session_state.filter_foodbank
        filtered_df = df[df["assigned food bank centre"].isin(selected_foodbanks)]

        #finding cumulative sum of vouchers by date
        historical_counts = filtered_df.groupby(["assigned food bank centre", "date"]).size().reset_index(name ="voucher_count")
        historical_counts["cumulative_voucher_count"] = historical_counts.groupby("assigned food bank centre")["voucher_count"].cumsum()

        #combined line
        combined_counts = df.groupby("date").size().reset_index(name= "voucher_count")
        combined_counts["cumulative_voucher_count"]= combined_counts["voucher_count"].cumsum()
        combined_counts["assigned food bank centre"] = "All Foodbanks"
        historical_counts = pd.concat([historical_counts, combined_counts], ignore_index=True)

        historical_counts_line = historical_counts.groupby("assigned food bank centre").filter(lambda x: len(x) > 1)

        # Plot with lines for each foodbank and combined
        fig = px.line(
            historical_counts_line,
            x="date",
            y="cumulative_voucher_count",
            color= "assigned food bank centre",
            title= "Vouchers Issued Over Time",
            labels={"date": "Date","cumulative_voucher_count":"Cumulative Vouchers Issued", "assigned food bank centre":"Foodbank"}
        )

        for food_bank in historical_counts["assigned food bank centre"].unique():
            data = historical_counts[historical_counts["assigned food bank centre"] == food_bank]

            # If there is only one data point, add a marker
            if len(data) == 1:
                fig.add_scatter(
                    x=data["date"],
                    y=data["cumulative_voucher_count"],
                    mode="markers",
                    marker=dict(size=8, symbol='circle'),
                    name=f"{food_bank} (single voucher)"
                )

        fig.update_layout(legend_title_text='Foodbanks')  # Add legend title
        st.plotly_chart(fig)

# Per Capita Vouchers Issued Per Age Group
def ward_voucher_graph(df):
    if df.shape[0] > 0:
        df = ward_population(df)

        age_groups = ["0-4_scaled_percentage", "5-11_scaled_percentage", "12-16_scaled_percentage", "17-24_scaled_percentage", "25-34_scaled_percentage", "35-44_scaled_percentage", "45-64_scaled_percentage", "65+_scaled_percentage"]
        # Melt the DataFrame to transform it into a long format
        df_melted = df.melt(id_vars=["ward", "population_percentage"], value_vars=age_groups,
                            var_name="Age group", value_name="Percentage")

        age_group_rename = {
            "0-4_scaled_percentage": "0-4",
            "5-11_scaled_percentage": "5-11",
            "12-16_scaled_percentage": "12-16",
            "17-24_scaled_percentage": "17-24",
            "25-34_scaled_percentage": "25-34",
            "35-44_scaled_percentage": "35-44",
            "45-64_scaled_percentage": "45-64",
            "65+_scaled_percentage": "65+",
        }

        # Apply the renaming to the 'Age Group' column in the melted DataFrame
        df_melted['Age group'] = df_melted['Age group'].map(age_group_rename)

        # Create the bar chart
        fig = px.bar(
            df_melted,
            x="ward",
            y="Percentage",
            color="Age group",
            title="Voucher usage per capita by ward and age group",
            labels={"ward": "Ward", "population_percentage": "Ward voucher usage (%)", "Percentage": "Voucher usage (%)"},
            hover_data={"population_percentage": True}
        )

        fig.update_layout(
            xaxis_tickangle=45,
            legend_title="Age groups",
            height=600
        )

        # Display the chart in Streamlit
        st.plotly_chart(fig)


st.markdown(f"<h1 style='text-align: center; color: #0A3D2E; font-family: Arial; font-size: 24px;'>Cirencester Foodbank Geo Analysis</h1>", unsafe_allow_html=True)
set_custom_styles()

# Create an expander with the dynamic text
with st.expander(st.session_state.expander_title, expanded=True):
    uploaded_file = st.file_uploader("", type=["xlsx"], on_change=set_expander_title)

    if uploaded_file is None:
        st.session_state.data_loaded = False
    else:
        # Load data without a password initially
        cleaned_df, st.session_state.data_loaded = load_data(uploaded_file)
        st.session_state.expander_title = f"Uploaded file: '{uploaded_file.name}"
        if not st.session_state.data_loaded:
            # Prompt for a password if the initial load failed
            password = st.text_input("Enter the password for the Excel file", type="password")
            if password:
                cleaned_df, st.session_state.data_loaded = load_data(uploaded_file, password=password)
                if not st.session_state.data_loaded:
                    st.error("Incorrect password or the file is not accessible.")

if st.session_state.data_loaded:
    # Display cleaned data and generate map
    with st.sidebar:
        selected_tab = option_menu(
            "",
            ["Vouchers", "Per Capita"],
            icons=["nan", "nan"],
            default_index=0,
            orientation="horizontal",
        )
        #voucher_tab, capita_tab = st.tabs(["Vouchers", "Per Capita"])

        if selected_tab == "Vouchers":
            col1, col2 = st.columns([4, 2])
            with col1:
                st.markdown("<h4 style='margin-bottom: -10px;'>Select foodbank centres</h4><h5 style='font-size: 12px; font-weight: 400; color: gray; margin-bottom: -30px;'>Display vouchers assigned to selected foodbank(s)</h5></p>", unsafe_allow_html=True)
            with col2:
                # Define the "Select all" checkbox
                select_all_foodbanks = st.checkbox('Select all', value=True, key="checkbox_foodbanks_voucher")
            filter_foodbank = []
            for option in ['Cirencester', 'Tetbury', 'Fairford']:
                # Set each checkbox's default value based on the "Select all" checkbox
                selected = st.checkbox(option, value=select_all_foodbanks, key=['voucher',option])
                if selected:
                    filter_foodbank.append(option)
            st.session_state.filter_foodbank = filter_foodbank

            st.markdown("<h4 style='margin-bottom: -10px;'>Exclude repeat households</h4><h5 style='font-size: 12px; font-weight: 400; color: gray; margin-bottom: -60px;'>Only display first voucher issued to each household</h5></p>", unsafe_allow_html=True)

            filter_repeat_addresses = st.radio(
                "",
                ["Yes", "No"],
                key="filter_repeat_addresses_voucher"
            )
            st.session_state.filter_repeat_addresses = True if filter_repeat_addresses == "No" else False

            max_household_size = cleaned_df["household_size"].max()
            st.markdown("<h4 style='margin-top: 15px; margin-bottom: -40px;'>Household size</h4>", unsafe_allow_html=True)
            filter_household_size = st.slider("", 1, max_household_size, (1, max_household_size), key="filter_household_size_voucher")
            st.session_state.filter_household_size = filter_household_size

            st.markdown("<h4 style='margin-top: 15px; margin-bottom: -50px;'>Voucher status</h4>", unsafe_allow_html=True)
            filter_voucher_status = st.radio(
                "",
                ["Both", "Fulfilled", "Unfulfilled"],
                key="filter_repeat_delivery_radio"
            )
            st.session_state.filter_voucher_status = filter_voucher_status

            st.markdown("<h4 style='margin-top: 15px; margin-bottom: -50px;'>Delivery required</h4>", unsafe_allow_html=True)
            filter_delivery = st.radio(
                "",
                ["Both", "Yes", "No"]
            )
            st.markdown("<h4 style='margin-top: -10px;'></h4>",
                        unsafe_allow_html=True)
            if filter_delivery == "Both":
                st.session_state.filter_delivery = None
            elif filter_delivery == "Yes":
                st.session_state.filter_delivery = True
            else:
                st.session_state.filter_delivery = False

            col1, col2 = st.columns([4, 2])
            with col1:
                st.markdown("<h4 style='margin-bottom: -50px;'>Crisis type</h4>", unsafe_allow_html=True)
            with col2:
                select_all_crisis_types = st.checkbox('Select all', value=True, key="checkbox_crisis_types_voucher")
            filter_crisis_type = []
            options = sorted(cleaned_df['crisis type'].unique())
            if 'Other' in options: # Move "Other" to the last position
                options.remove('Other')
                options.append('Other')
            for option in options:
                selected = st.checkbox(option, value=select_all_crisis_types, key=['voucher',option])
                if selected:
                    filter_crisis_type.append(option)
            st.session_state.filter_crisis_type = filter_crisis_type


        if selected_tab == "Per Capita":
            col1, col2 = st.columns([4, 2])
            with col1:
                st.markdown("<h4 style='margin-bottom: -10px;'>Select foodbank centres</h4><h5 style='font-size: 12px; font-weight: 400; color: gray; margin-bottom: -30px;'>Display vouchers assigned to selected foodbank(s)</h5></p>", unsafe_allow_html=True)
            with col2:
                # Define the "Select all" checkbox
                select_all_foodbanks = st.checkbox('Select all', value=True, key="checkbox_foodbanks_capita")
            filter_foodbank = []
            for option in ['Cirencester', 'Tetbury', 'Fairford']:
                # Set each checkbox's default value based on the "Select all" checkbox
                selected = st.checkbox(option, value=select_all_foodbanks, key=['capita',option])
                if selected:
                    filter_foodbank.append(option)
            st.session_state.filter_foodbank = filter_foodbank

            st.markdown("<h4 style='margin-bottom: -10px;'>Exclude repeat households</h4><h5 style='font-size: 12px; font-weight: 400; color: gray; margin-bottom: -60px;'>Only display first voucher issued to each household</h5></p>", unsafe_allow_html=True)

            filter_repeat_addresses = st.radio(
                "",
                ["Yes", "No"],
                key="filter_repeat_addresses_voucher"
            )
            st.session_state.filter_repeat_addresses = True if filter_repeat_addresses == "No" else False


            col1, col2 = st.columns([4, 2])
            with col1:
                st.markdown("<h4 style='margin-bottom: -10px';>Age groups</h4><h5 style='font-size: 12px; font-weight: 400; color: gray; margin-bottom: -30px;'>Display vouchers where household contains selected age group(s)</h5></p>", unsafe_allow_html=True)
            with col2:
                select_all_age_groups = st.checkbox('Select all', value=True, key="checkbox_age_groups")
            filter_age_group = []
            for option in age_groups.keys():
                selected = st.checkbox(option, value=select_all_age_groups, key=['age group',option])
                if selected:
                    filter_age_group.append(option)
            st.session_state.filter_age_group = filter_age_group

            st.markdown("<h4 style='margin-top: 15px; margin-bottom: -50px;'>Voucher status</h4>",
                        unsafe_allow_html=True)
            filter_voucher_status = st.radio(
                "",
                ["Both", "Fulfilled", "Unfulfilled"]
            )
            st.session_state.filter_voucher_status = filter_voucher_status

            st.markdown("<h4 style='margin-top: 15px; margin-bottom: -50px;'>Delivery required</h4>",
                        unsafe_allow_html=True)
            filter_delivery = st.radio(
                "",
                ["Both", "Yes", "No"],
                key="filter_repeat_delivery_capita"
            )
            st.markdown("<h4 style='margin-top: -10px;'></h4>",
                        unsafe_allow_html=True)
            if filter_delivery == "Both":
                st.session_state.filter_delivery = None
            elif filter_delivery == "Yes":
                st.session_state.filter_delivery = True
            else:
                st.session_state.filter_delivery = False

            col1, col2 = st.columns([4, 2])
            with col1:
                st.markdown("<h4 style='margin-bottom: -50px;'>Crisis type</h4>", unsafe_allow_html=True)
            with col2:
                select_all_crisis_types = st.checkbox('Select all', value=True, key="checkbox_crisis_types_capita")
            filter_crisis_type = []
            options = sorted(cleaned_df['crisis type'].unique())
            if 'Other' in options: # Move "Other" to the last position
                options.remove('Other')
                options.append('Other')
            for option in options:
                selected = st.checkbox(option, value=select_all_crisis_types, key=['capita',option])
                if selected:
                    filter_crisis_type.append(option)
            st.session_state.filter_crisis_type = filter_crisis_type

    filtered_df = cleaned_df[cleaned_df["crisis type"].isin(st.session_state.filter_crisis_type)]

    if selected_tab == 'Vouchers':
        filtered_df = filtered_df[(cleaned_df["household_size"] >= st.session_state.filter_household_size[0]) &
        (cleaned_df["household_size"] <= st.session_state.filter_household_size[1])]

    if selected_tab == 'Per Capita':
        filtered_df = filtered_df[cleaned_df[st.session_state.filter_age_group].any(axis=1)]

    if not st.session_state.filter_repeat_addresses:
        filtered_df.drop_duplicates(subset=['address1', 'address2'], keep='first', inplace=True)

    if st.session_state.filter_delivery != None:
        filtered_df = filtered_df[filtered_df["delivery required"] == st.session_state.filter_delivery]

    if st.session_state.filter_voucher_status != 'Both':
        filtered_df = filtered_df[filtered_df["voucher status"] == st.session_state.filter_voucher_status]

    filtered_df_foodbanks = filtered_df[cleaned_df["assigned food bank centre"].isin(st.session_state.filter_foodbank)] # filter the selected foodbanks

    if selected_tab == "Vouchers":
        st.subheader("Total vouchers issued across postcodes")
        postcode_search = None
        if filtered_df_foodbanks.shape[0] > 0:
            postcode_search = st.text_input("Postcode search", "")
        if postcode_search:
            filtered_df_foodbanks_postcode = filtered_df_foodbanks[filtered_df_foodbanks['postcode'].str.contains(postcode_search, na=False)]
            postcode_map(filtered_df_foodbanks_postcode)
        else:
            postcode_map(filtered_df_foodbanks)

        # - Monthly line graph: total voucher issued across months
            # - Always plot total vouchers across all foodbanks
            # - Plot separate lines for each foodbank selected in the filter
        monthly_voucher_graph(filtered_df)

        # - Historical graph: total voucher issued across time
            # - Always plot total vouchers across all foodbanks
            # - Plot separate lines for each foodbank selected in the filter

        historical_voucher_graph(filtered_df)

    if selected_tab == "Per Capita":
        #capita_map(filtered_df_foodbanks)
        st.subheader("Voucher usage per capita across wards")
        ward_map(filtered_df_foodbanks)

        # - Bar graph: voucher usage per capita across wards with different opacities for selected age groups
            # - Plot total voucher usage per capita across all wards
            # - Plot separate bars for each ward selected in the filter
        ward_voucher_graph(filtered_df_foodbanks)


