import streamlit as st
import json
import pandas as pd
import numpy as np
from utils.api_tester import APITester
from utils.report_generator import ReportGenerator
import plotly.graph_objects as go
import plotly.express as px
import base64
from datetime import datetime
import re
from urllib.parse import urlparse
import time  # Import time for simulating the test duration
from faq import display_faq  # Import the FAQ display function
from footer import display_footer  # Import the footer display function
from streamlit import session_state as st_session  # Import session state for managing modal visibility

from streamlit_sortables import sort_items

# Function to format dataframes with consistent decimal places
def format_dataframe(df):
    """Format a dataframe to ensure all numeric values have consistent decimal places."""
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    
    # Create a copy of the dataframe
    formatted_df = df.copy()
    
    # Process all columns
    for col in formatted_df.columns:
        # Skip non-numeric columns
        if formatted_df[col].dtype.kind not in 'ifc':
            continue
        
        # Format floating point numbers to 1 decimal place
        if formatted_df[col].dtype.kind == 'f':
            formatted_df[col] = formatted_df[col].round(1)
    
    return formatted_df

st.set_page_config(page_title="API Performance Tester", layout="wide")

# Custom CSS for the clear button positioning and loading animation
st.markdown("""
<style>
    .clear-button {
        position: fixed;
        right: 80px;
        top: 0.5rem;
        z-index: 999;
    }
    
    /* Hide default streamlit button styling */
    .clear-button button {
        color: #ff4b4b !important;
        border: 1px solid #ff4b4b !important;
    }
    
    .clear-button button:hover {
        color: white !important;
        background-color: #ff4b4b !important;
    }

    /* Styling for the clear imported APIs button */
    div[data-testid="stButton"] button[kind="secondary"][data-testid="baseButton-secondary"]:contains("Clear Imported APIs") {
        color: #ff4b4b !important;
        border: 1px solid #ff4b4b !important;
    }
    
    div[data-testid="stButton"] button[kind="secondary"][data-testid="baseButton-secondary"]:contains("Clear Imported APIs"):hover {
        color: white !important;
        background-color: #ff4b4b !important;
    }

    /* Styling for the clear imported APIs button with icon */
    div[data-testid="stButton"] button[data-testid="baseButton-secondary"][key="clear_imported_apis_btn"] {
        color: #888 !important;
        border: 1px solid #444 !important;
        background-color: rgba(50, 50, 50, 0.2) !important;
        margin-left: -10px !important;
    }
    
    div[data-testid="stButton"] button[data-testid="baseButton-secondary"][key="clear_imported_apis_btn"]::before {
        content: "🗑️ ";
        margin-right: 5px;
    }
    
    div[data-testid="stButton"] button[data-testid="baseButton-secondary"][key="clear_imported_apis_btn"]:hover {
        background-color: rgba(80, 80, 80, 0.4) !important;
    }

    /* Adjust column widths for import/clear buttons */
    .import-button-container {
        display: flex;
        align-items: center;
        gap: 5px;
    }
    
    .import-col {
        flex: 0.6;
    }
    
    .clear-col {
        flex: 0.4;
        padding-left: 0;
    }

    .loading-animation {
        display: none;
        justify-content: center;
        align-items: center;
        height: 100vh;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(255, 255, 255, 0.8);
        z-index: 1000;
    }

    .loading-animation img {
        width: 100px; /* Adjust size as needed */
        animation: spin 1s infinite linear;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .modal {
        display: block;
        position: fixed;
        z-index: 1001;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        overflow: auto;
        background-color: rgba(14, 17, 23, 0.9); /* Updated background color */
        padding-top: 60px;
    }

    .modal-content {
        background-color: rgb(14, 17, 23); /* Dark background for modal content */
        color: white; /* White text for better readability */
        margin: 5% auto;
        padding: 20px;
        border: 1px solid #888;
        width: 80%;
        max-width: 600px;
        border-radius: 8px;
    }

    .close {
        color: #aaa;
        float: right;
        font-size: 28px;
        font-weight: bold;
    }

    .close:hover,
    .close:focus {
        color: white !important; /* Change to white on hover for better visibility */
        text-decoration: none;
        cursor: pointer;
    }

    .move-button {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 32px;
        margin-top: 0px;
    }

    .move-button button {
        padding: 0 !important;
        width: 32px !important;
        min-height: 0 !important;
        height: 32px !important;
        line-height: 1 !important;
        background-color: transparent !important;
        border: none !important;
        color: #4d96ff !important; /* Blue color for the move icon */
        font-size: 20px !important; /* Larger icon size */
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    .move-button button:hover {
        background-color: rgba(77, 150, 255, 0.1) !important; /* Light blue background on hover */
        color: #4d96ff !important;
    }
    
    /* Custom styling for the edit button */
    div[data-testid="stButton"] button[data-testid="baseButton-secondary"][key^="edit_btn_"] {
        padding: 0px 8px !important;
        min-width: 30px !important;
        height: 28px !important;
        line-height: 1 !important;
        font-size: 14px !important;
        margin: 0 !important;
        border: none !important;
        background-color: transparent !important;
    }
    
    div[data-testid="stButton"] button[data-testid="baseButton-secondary"][key^="edit_btn_"]:hover {
        background-color: rgba(70, 70, 70, 0.2) !important;
    }

    /* Ensure the number input and button are aligned */
    .stNumberInput {
        margin-bottom: 0 !important;
    }

    /* Custom CSS for the move button */
    div[data-testid="stButton"] > button[kind="secondary"].move-btn {
        padding: 0 !important;
        width: 32px !important;
        height: 32px !important;
        border: none !important;
        background-color: transparent !important;
        color: #4d96ff !important; /* Blue color for the move icon */
        font-size: 18px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin-top: 0 !important;
    }

    div[data-testid="stButton"] > button[kind="secondary"].move-btn:hover {
        background-color: rgba(77, 150, 255, 0.1) !important; /* Light blue background on hover */
        color: #4d96ff !important;
    }
    
    /* Basic styling for move button with key starting with move_btn_ */
    div[data-testid="stButton"] button[data-testid="baseButton-secondary"][key^="move_btn_"] {
        padding: 0px 6px !important;
        min-width: 32px !important;
        width: 32px !important;
        height: 28px !important;
        line-height: 1 !important;
        font-size: 16px !important;
        margin: 0 !important;
        border: 1px solid rgba(70, 70, 70, 0.2) !important;
        border-radius: 4px !important;
        background-color: rgba(50, 50, 50, 0.1) !important;
        color: #4d96ff !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    div[data-testid="stButton"] button[data-testid="baseButton-secondary"][key^="move_btn_"]:hover {
        background-color: rgba(70, 70, 70, 0.3) !important;
        border-color: rgba(77, 150, 255, 0.3) !important;
    }

    /* Remove margin from number input */
    div[data-testid="stNumberInput"] > div {
        margin-bottom: 0 !important;
    }

    /* Adjust column gap for import/clear buttons */
    .row-widget.stButton {
        width: 95%;
    }
    
    /* Remove default column gaps in streamlit */
    .css-ocqkz7.e1tzin5v3, .css-12w0qpk.e1tzin5v2 {
        gap: 0.5rem !important;
    }

    /* Button container styling */
    .button-container {
        display: flex;
        align-items: center;
    }
    
    .import-button {
        margin-right: 10px;
    }
    
    .clear-button-container {
        margin-left: auto;
    }

    /* Make columns tighter and remove padding/margins */
    [data-testid="column"] {
        padding: 0 !important;
        gap: 0 !important;
    }
    
    /* Remove gap between columns */
    div.row-widget.stHorizontal {
        gap: 0 !important;
    }
    
    /* Specifically target the button row */
    .button-row [data-testid="column"] {
        padding: 0 !important;
    }
    
    .button-row div.row-widget.stHorizontal {
        gap: 0 !important;
    }
    
    /* First column in button row */
    .button-row [data-testid="column"]:nth-of-type(1) {
        padding-right: 10px !important;
        width: auto !important;
    }
    
    /* Second column in button row */
    .button-row [data-testid="column"]:nth-of-type(2) {
        width: auto !important;
    }
    
    /* Ensure proper alignment of move button and input columns - moved higher */
    div[data-testid="column"] > div:has(button[key^="move_btn_"]) {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        padding-left: 5px !important;
        margin-top: -4px !important;
    }

    /* Reduce gap between columns */
    div[data-testid="column"] {
        padding: 0 !important;
        margin: 0 !important;
    }
    
    div[data-testid="column"]:first-child {
        padding-right: 5px !important;
    }
    
    /* Align the edit and delete buttons at the same level as View Details */
    div[data-testid="stExpander"] {
        margin-bottom: 0 !important;
    }
    
    /* Style for the edit/delete button container */
    div[data-testid="column"]:nth-child(3) {
        display: flex !important;
        align-items: flex-start !important;
        justify-content: flex-end !important;
        padding-right: 0 !important;
    }
    
    /* Make edit and delete buttons more compact */
    div[data-testid="column"]:nth-child(3) button {
        padding: 0 !important;
        min-width: 35px !important;
    }
    
    /* Ensure buttons align with the View Details expander */
    .stExpander {
        margin-right: 0 !important;
        width: 100% !important;
    }
    
    /* Adjust the right column to align buttons with View Details expander */
    [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child {
        margin-right: 5px !important;
        padding-right: 0 !important;
    }
    
    /* Fix spacing in the position column */
    [data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child {
        padding-right: 0 !important;
        padding-left: 5px !important;
    }
    
    /* Make number input more compact */
    div[data-testid="stNumberInput"] > div {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize modal visibility in session state
if 'show_faq' not in st_session:
    st_session.show_faq = False
if 'show_about' not in st_session:
    st_session.show_about = False

def toggle_faq():
    """Toggle the visibility of the FAQ modal."""
    st_session.show_faq = not st_session.show_faq

def toggle_about():
    """Toggle the visibility of the About modal."""
    st_session.show_about = not st_session.show_about

def get_endpoint_name(url):
    """Extract endpoint name from full URL"""
    parsed = urlparse(url)
    path = parsed.path
    # Get the last part of the path
    endpoint = path.split('/')[-1]
    # If empty, use the last non-empty part
    if not endpoint and len(path.split('/')) > 1:
        endpoint = path.split('/')[-2]
    return endpoint or url


def clear_form():
    """Clear form inputs by updating the session state defaults"""
    if 'form_defaults' not in st.session_state:
        st.session_state.form_defaults = {
            "method": "GET",
            "url": "",
            "headers": "{}",
            "body": "{}"
        }


def reset_all_data():
    """Clear all test results and API configurations"""
    if 'test_results' in st.session_state:
        del st.session_state.test_results
    if 'test_config' in st.session_state:
        del st.session_state.test_config

    # Reset APIs list
    st.session_state.apis = []

    # Reset form
    st.session_state.form_key = 0
    clear_form()

    # Force a rerun to update the UI
    st.rerun()


# Add helper function to extract endpoint name from URL for use as default naming
def extract_endpoint_name(url, fallback_index=None):
    """Extract the last meaningful part from URL path for API name"""
    # If fallback_index is provided, create a sequential name
    if fallback_index is not None:
        return f"API {fallback_index + 1}"
    
    parsed = urlparse(url)
    path = parsed.path.rstrip('/')
    
    # If path is empty, check query params or use hostname
    if not path or path == '/':
        # Check if there are query parameters that can be used
        if parsed.query:
            query_parts = parsed.query.split('&')
            for part in query_parts:
                if '=' in part:
                    key = part.split('=', 1)[0].strip()
                    # Return the first parameter name
                    return key
        
        # If no query params, use hostname or a fallback name
        hostname = parsed.netloc.split('.')[0] if parsed.netloc else ''
        if not hostname:
            return "API"
        return hostname
    
    # Get the last path segment (after the last slash, before any query params)
    parts = path.split('/')
    last_segment = parts[-1] if parts else ""
    
    # If the last segment is empty (URL ends with /), get the previous segment
    if not last_segment and len(parts) > 1:
        last_segment = parts[-2]
    
    # Remove any query parameters if present
    if '?' in last_segment:
        last_segment = last_segment.split('?')[0]
    
    # In case of PostLCUSystemCap endpoints, special handling
    if last_segment.lower() == "postlcusystemcap":
        return "PostLCUSystemCap"
    
    # For UserPreference endpoint
    if last_segment.lower() == "userpreference":
        return "UserPreference"
    
    # If the segment is too long or empty, use a fallback
    if len(last_segment) > 50 or not last_segment:
        return "API"
    
    return last_segment


# Function to parse BlazMeter JSON format
def parse_blazmeter_json(blazmeter_data):
    """
    Parse BlazMeter JSON format and extract API details.
    Returns a list of APIs in the format expected by the app.
    """
    apis = []
    
    # Check if the JSON has the expected structure
    if not isinstance(blazmeter_data, dict) or 'traffic' not in blazmeter_data:
        st.error("Invalid BlazMeter JSON format. The 'traffic' key is missing.")
        return []
    
    # Process each traffic item
    for i, item in enumerate(blazmeter_data.get('traffic', [])):
        method = item.get('method', 'GET')
        url = item.get('url', '')
        
        # Always use sequential naming for BlazMeter imports
        name = f"API {i + 1}"
        
        # Extract headers
        headers = {}
        for header in item.get('headers', []):
            name_h = header.get('name', '')
            value = header.get('value', '')
            if name_h and name_h not in ['User-Agent', 'sec-ch-ua', 'sec-ch-ua-mobile', 'sec-ch-ua-platform']:
                headers[name_h] = value
        
        # Extract body if it exists
        body = {}
        if 'body' in item and item['body']:
            try:
                # BlazMeter stores body as an array of strings
                body_str = item['body'][0] if isinstance(item['body'], list) and item['body'] else item.get('body', '{}')
                if isinstance(body_str, str):
                    body = json.loads(body_str)
            except json.JSONDecodeError:
                # If body isn't valid JSON, store it as a string
                body = {"raw": item['body'][0] if isinstance(item['body'], list) and item['body'] else str(item.get('body', ''))}
        
        # Limit name to 30 characters
        name = name[:30]
            
        # Create API object
        api = {
            "name": name,
            "method": method,
            "url": url,
            "headers": headers,
            "body": body
        }
        apis.append(api)
    
    return apis


def get_successful_apis(df):
    """
    Filter a dataframe to include only APIs that were successful (status code < 400) for all requests.
    
    Args:
        df (pandas.DataFrame): DataFrame containing API test results
        
    Returns:
        pandas.DataFrame: Filtered DataFrame containing only successful API results
    """
    # Get URLs where all requests were successful (status code < 400)
    successful_urls = df.groupby("url")["status_code"].apply(lambda x: all(x < 400))
    successful_urls = successful_urls[successful_urls].index.tolist()
    
    # Return filtered dataframe with only successful APIs
    return df[df["url"].isin(successful_urls)]


def main():
    # Simple title without a clear button next to it
    st.title("Performance Testing Tool")

    # Initialize session state for storing APIs
    if 'apis' not in st.session_state:
        st.session_state.apis = []

    # Form key for resetting the form completely
    if 'form_key' not in st.session_state:
        st.session_state.form_key = 0

    # Track if APIs have been successfully imported
    if 'has_imported_apis' not in st.session_state:
        st.session_state.has_imported_apis = False

    # Initialize form defaults
    clear_form()

    with st.sidebar:
        st.header("Test Configuration")
        test_mode = st.radio("Test Input Mode",
                             ["Manual Entry", "File Upload"])

        # Test configuration
        virtual_users = st.number_input("Virtual Users", min_value=1, value=10)
        ramp_up_time = st.number_input("Ramp-up Time (seconds)",
                                       min_value=1,
                                       value=5)

        # Authentication section in sidebar
        st.header("Authorization")
        auth_type = st.selectbox("Auth Type",
                                 ["No Auth", "Bearer Token", "Basic Auth"])
        auth_details = {}

        if auth_type == "Bearer Token":
            auth_token = st.text_input("Bearer Token", type="password")
            if auth_token:
                auth_details = {"Authorization": f"Bearer {auth_token}"}
        elif auth_type == "Basic Auth":
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if username and password:
                credentials = base64.b64encode(
                    f"{username}:{password}".encode()).decode()
                auth_details = {"Authorization": f"Basic {credentials}"}

    if test_mode == "Manual Entry":
        st.subheader("Add API")
        # Use dynamic form key to force reset
        with st.form(f"api_form_{st.session_state.form_key}"):
            method = st.selectbox("HTTP Method",
                                  ["GET", "POST", "PUT", "DELETE"])
            url = st.text_input("API URL")
            api_name = st.text_input("API Name (Optional)", 
                            help="If left empty, a name will be generated from the URL. Maximum 30 characters.",
                            max_chars=30)

            headers = st.text_area(
                "Headers (JSON format)",
                value=st.session_state.form_defaults["headers"])
            body = st.text_area("Request Body (JSON format)",
                                value=st.session_state.form_defaults["body"])

            submitted = st.form_submit_button("Add API")
            if submitted:
                # Validate URL field is not empty
                if not url.strip():
                    st.error("Please enter an API URL")
                else:
                    try:
                        headers_dict = json.loads(headers)
                        headers_dict.update(auth_details)
                        body_dict = json.loads(body)

                        # If API name is empty, generate one from URL or use a sequential name
                        if not api_name:
                            api_name = extract_endpoint_name(url, fallback_index=len(st.session_state.apis))
                        
                        # Limit API name to 30 characters
                        api_name = api_name[:30]
                        
                        # Check for duplicate names and append a suffix if needed
                        original_name = api_name
                        counter = 1
                        while any(api.get('name') == api_name for api in st.session_state.apis):
                            api_name = f"{original_name} ({counter})"
                            if len(api_name) > 30:
                                api_name = f"{original_name[:26]} ({counter})"
                            counter += 1

                        api = {
                            "name": api_name,
                            "method": method,
                            "url": url,
                            "headers": headers_dict,
                            "body": body_dict
                        }
                        st.session_state.apis.append(api)

                        # Reset form defaults
                        st.session_state.form_defaults = {
                            "method": "GET",
                            "url": "",
                            "headers": "{}",
                            "body": "{}"
                        }

                        # Increment form key to force complete reset
                        st.session_state.form_key += 1

                        st.rerun()
                    except json.JSONDecodeError:
                        st.error("Invalid JSON format in headers or body")

        # Display success message outside the form if an API was just added
        if 'apis' in st.session_state and len(st.session_state.apis) > 0:
            if not submitted:  # Only show after rerun to avoid double messages
                st.success(
                    f"API added successfully! Total APIs: {len(st.session_state.apis)}"
                )

    else:  # File Upload
        st.subheader("Upload API Collection")
        collection_format = st.radio(
            "Collection Format",
            ["Postman Collection", "BlazMeter JSON"],
            horizontal=True
        )
        
        uploaded_file = st.file_uploader(
            f"Upload {'Postman Collection' if collection_format == 'Postman Collection' else 'BlazMeter JSON'}", 
            type=["json"]
        )
        
        # Reset imported flag when a new file is uploaded
        if uploaded_file and 'last_uploaded_file' in st.session_state and st.session_state.last_uploaded_file != uploaded_file.name:
            st.session_state.has_imported_apis = False
        
        # Store current uploaded file name
        if uploaded_file:
            st.session_state.last_uploaded_file = uploaded_file.name
            
            try:
                collection = json.load(uploaded_file)
                imported_apis = []
                
                if collection_format == "Postman Collection":
                    # Existing Postman collection processing
                    for i, item in enumerate(collection.get("item", [])):
                        request = item.get("request", {})
                        headers_dict = {
                            h["key"]: h["value"]
                            for h in request.get("header", [])
                        }
                        headers_dict.update(auth_details)  # Add auth headers
                        body_raw = request.get("body", {}).get("raw", "{}")

                        # Check if body_raw is a string with double quotes and parse it
                        if isinstance(body_raw, str):
                            # Remove outer quotes if they exist
                            body_raw = body_raw.strip('"')
                            try:
                                body_dict = json.loads(body_raw)  # Parse the cleaned string
                            except json.JSONDecodeError:
                                body_dict = body_raw  # Keep as is if parsing fails
                        else:
                            body_dict = body_raw  # If not a string, use as is

                        # Use the name from Postman collection if available
                        api_name = item.get("name") if item.get("name") else f"API {i + 1}"
                        url = request.get("url", {}).get("raw", "")

                        api = {
                            "name": api_name,
                            "method": request.get("method", "GET"),
                            "url": url,
                            "headers": headers_dict,
                            "body": body_dict
                        }
                        imported_apis.append(api)
                else:  # BlazMeter JSON
                    # Parse BlazMeter JSON format
                    imported_apis = parse_blazmeter_json(collection)
                
                # Create a container for buttons
                buttons_container = st.container()
                
                # Use a horizontal layout with minimal spacing
                with buttons_container:
                    # Use custom HTML to place buttons close together
                    st.markdown('<div style="display: flex; align-items: center; gap: 10px;">', unsafe_allow_html=True)
                    
                    # First column for Import button
                    col1, col2 = st.columns([0.1, 0.9])
                    
                    with col1:
                        if st.button("Import APIs", type="primary"):
                            if imported_apis:
                                # Ensure unique names and limit length for all imported APIs
                                existing_names = [api.get('name', '') for api in st.session_state.apis]
                                
                                for api in imported_apis:
                                    # Limit name to 30 characters
                                    api['name'] = api['name'][:30]
                                    
                                    # Ensure uniqueness
                                    original_name = api['name']
                                    counter = 1
                                    while api['name'] in existing_names:
                                        api['name'] = f"{original_name} ({counter})"
                                        if len(api['name']) > 30:
                                            api['name'] = f"{original_name[:26]} ({counter})"
                                        counter += 1
                                    
                                    existing_names.append(api['name'])
                                
                                st.session_state.apis.extend(imported_apis)
                                st.session_state.has_imported_apis = True
                                #st.success(f"Successfully imported {len(imported_apis)} APIs")
                            else:
                                st.error("No valid APIs found to import.")
                    
                    with col2:
                        # Positioned immediately after Import button with minimal space
                        clear_btn = st.button("Clear APIs", 
                                    disabled=not st.session_state.has_imported_apis,
                                    help="Clear all imported APIs",
                                    key="clear_imported_apis_btn",
                                    type="secondary")
                        
                        if clear_btn:
                            st.session_state.apis = []
                            st.session_state.has_imported_apis = False
                            st.success("All imported APIs have been cleared")
                            st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error importing file: {str(e)}")
                st.exception(e)

    # Display configured APIs with elegant reordering capabilities
    if st.session_state.apis:
        st.subheader("Configured APIs")
        
        # Create a visually appealing container for all APIs
        api_list_container = st.container()
        
        # Display each API with position control and expandable details
        for idx, api in enumerate(st.session_state.apis):
            # Create a cleaner container for each API with subtle border
            with st.container():
                # Add subtle separator between APIs
                if idx > 0:
                    st.markdown('<hr style="margin: 5px 0; border: 0; height: 1px; background: #555; opacity: 0.2;">', unsafe_allow_html=True)
                
                cols = st.columns([0.1, 0.8, 0.1])
                
                # Position number input in the left column
                with cols[0]:
                    # Current position (1-based index)
                    current_pos = idx + 1
                    
                    # Create custom label with tooltip using HTML and CSS - positioned to align with method badge
                    st.markdown(f"""
                    <div class="position-label" style="display: flex; align-items: center; margin-bottom: 0px; margin-top: 0px;">
                        <span style="margin-right: 2px; font-size: 17px; color: #aaaaaa;">Position</span>
                        <div class="tooltip" style="position: relative; display: inline-block; margin-left: 3px; cursor: help;">
                            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" fill="#9E9E9E" viewBox="0 0 16 16">
                                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                                <path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
                            </svg>
                            <span class="tooltiptext" style="visibility: hidden; width: 240px; background-color: #333; color: #fff; text-align: center; border-radius: 6px; padding: 5px; position: absolute; z-index: 1; bottom: 125%; left: 50%; margin-left: -120px; opacity: 0; transition: opacity 0.3s; font-size: 12px;">
                                Change the position number to rearrange APIs. Enter a new position and press Enter to move an API.
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Add CSS for tooltip via a separate markdown call to avoid Python variable interpretation
                    st.markdown("""
                    <style>
                    .tooltip:hover .tooltiptext {
                        visibility: visible !important;
                        opacity: 1 !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Add vertical position adjustment to parent columns
                    st.markdown("""
                    <style>
                    /* Target the button's parent column specifically */
                    div.row-widget.stHorizontal > div:nth-child(2) > div {
                    position: relative;
                    top: -12px;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Better aligned position input and move button with tighter spacing
                    pos_col1, pos_col2 = st.columns([2.8, 1.2])
                    
                    with pos_col1:
                        # Position number input without label - with custom CSS to align with API URL
                        st.markdown(f"""
                        <style>
                        /* Align this specific number input with the API URL */
                        [data-testid="stNumberInput"][key="pos_{idx}"] {{
                            margin-top: -30px !important; /* Negative margin to pull the input field up */
                            margin-bottom: 0px !important;
                            padding-bottom: 0px !important;
                        }}
                        /* Adjust input field style to align with URL */
                        [data-testid="stNumberInput"][key="pos_{idx}"] input {{
                            height: 28px !important;
                            padding-top: 0px !important;
                            padding-bottom: 0px !important;
                            margin-top: 0px !important;
                        }}
                        /* Remove extra padding from the label div */
                        [data-testid="stNumberInput"][key="pos_{idx}"] > div {{
                            padding-bottom: 0px !important;
                            margin-bottom: 0px !important;
                            padding-top: 0px !important;
                        }}
                        </style>
                        """, unsafe_allow_html=True)
                        
                        new_pos = st.number_input(
                            label="Position Number", 
                            min_value=1,
                            max_value=len(st.session_state.apis),
                            value=int(current_pos),
                            step=1,
                            key=f"pos_{idx}",
                            label_visibility="collapsed"
                        )
                    
                    with pos_col2:
                        # Track if this API was just moved to prevent showing the button after a successful move
                        just_moved_key = f"just_moved_{idx}"
                        if just_moved_key not in st.session_state:
                            st.session_state[just_moved_key] = False
                        
                        # Only show Move icon if position has changed AND this API wasn't just moved
                        if new_pos != current_pos and not st.session_state[just_moved_key]:
                            # Direct HTML wrapper with a precise negative margin for alignment
                            st.markdown("""
                            <div style="margin-top: -30px; position: relative; z-index: 100;">
                            """, unsafe_allow_html=True)
                            
                            # Simple button without extra styling
                            move_button = st.button("🔄", 
                                          key=f"move_btn_{idx}", 
                                          help="Move API to new position",
                                          use_container_width=False)
                                
                            if move_button:
                                # Move the API
                                api_to_move = st.session_state.apis[idx]
                                new_apis = [api for i, api in enumerate(st.session_state.apis) if i != idx]
                                target_idx = new_pos - 1  # Convert to 0-based index
                                new_apis.insert(target_idx, api_to_move)
                                st.session_state.apis = new_apis
                                
                                # Mark this API as just moved to hide the button
                                st.session_state[just_moved_key] = True
                                
                                st.rerun()
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            # Reset the "just moved" state if position is back to current
                            if new_pos == current_pos and st.session_state[just_moved_key]:
                                st.session_state[just_moved_key] = False
                            
                            # Add a placeholder div with the same height
                            st.markdown("""
                            <div style="height:32px;"></div>
                            """, unsafe_allow_html=True)

                # API details in center column with cleaner styling
                with cols[1]:
                    # Create a cleaner heading for each API with method badge, name, and URL
                    method_colors = {
                        "GET": "#4CAF50",
                        "POST": "#2196F3",
                        "PUT": "#FF9800",
                        "DELETE": "#F44336",
                        "PATCH": "#9C27B0"
                    }
                    
                    # Get color for method badge (default to gray if not in our mapping)
                    method_color = method_colors.get(api['method'], "#607D8B")
                    
                    # State variable for editing API name
                    edit_name_key = f"edit_name_{idx}"
                    if edit_name_key not in st.session_state:
                        st.session_state[edit_name_key] = False
                    
                    # Get API name or generate it if missing
                    api_name = api.get('name', '')
                    if not api_name:
                        api_name = extract_endpoint_name(api['url'])
                        # Update the API object with the extracted name
                        api['name'] = api_name
                    
                    # Check if we should show the edit field
                    if st.session_state[edit_name_key]:
                        # Display input field for editing name
                        new_name = st.text_input(
                            "API Name", 
                            value=api_name,
                            key=f"name_input_{idx}",
                            max_chars=30,
                            help="Maximum 30 characters"
                        )
                        
                        # Add save and cancel buttons right next to each other with minimal spacing
                        btn_col1, btn_col2, spacer = st.columns([0.15, 0.15, 0.7])
                        with btn_col1:
                            save_clicked = st.button("Save", key=f"save_name_{idx}", use_container_width=True)
                            if save_clicked and new_name:
                                # Limit name to 30 characters
                                new_name = new_name[:30]
                                
                                # Check for duplicate names excluding this API
                                original_name = new_name
                                counter = 1
                                other_apis = [a for i, a in enumerate(st.session_state.apis) if i != idx]
                                while any(api.get('name') == new_name for api in other_apis):
                                    new_name = f"{original_name} ({counter})"
                                    if len(new_name) > 30:
                                        new_name = f"{original_name[:26]} ({counter})"
                                    counter += 1
                                
                                st.session_state.apis[idx]['name'] = new_name
                                st.session_state[edit_name_key] = False
                                st.rerun()
                                
                        with btn_col2:
                            cancel_clicked = st.button("Cancel", key=f"cancel_name_{idx}", use_container_width=True)
                            if cancel_clicked:
                                st.session_state[edit_name_key] = False
                                st.rerun()
                    else:
                        # Method badge and API name without edit button
                        name_row = st.container()
                        
                        with name_row:
                            # Use columns for layout - method badge and API name only 
                            # Removed edit button from here and will place it at the end
                            mcol1, mcol2 = st.columns([0.15, 0.85])
                            
                            with mcol1:
                                # Method badge - better styling with bigger text
                                st.markdown(f"""
                                <div style="background-color:{method_color}; color:white; 
                                    padding:2px 8px; border-radius:4px; 
                                    font-size:14px; margin-top:3px; text-align:center;">
                                    {api['method']}
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with mcol2:
                                # API name with proper wrapping and larger font
                                st.markdown(f"""
                                <div style="font-size:17px; color:#E0E0E0; font-weight:600; 
                                    word-wrap:break-word; overflow-wrap:break-word; 
                                    word-break:break-word; margin-top:3px;">
                                    {api_name}
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # URL display with proper wrapping and increased top margin to avoid overlap
                        st.markdown(f"""
                        <div style="font-size:15px; color:rgb(224, 224, 224); 
                            overflow-wrap:break-word; word-break:break-word; 
                            width:100%; margin-top:20px; padding-right:10px;">
                            {api['url']}
                        </div>
                        """, unsafe_allow_html=True)

                # Expandable details section
                with st.expander("View Details", expanded=False):
                    st.json(api)
                
                # Move both edit and delete buttons to the right column aligned with the View Details box
                with cols[2]:
                    # Custom styling to match buttons with "View Details" expander position
                    st.markdown(f"""
                    <style>
                    /* Target buttons specifically for this API row */
                    [data-testid="stHorizontalBlock"] button[key="edit_btn_{idx}"],
                    [data-testid="stHorizontalBlock"] button[key="delete_{idx}"] {{
                        margin-top: 4px !important;
                    }}
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Container with precise alignment to match the View Details box
                    st.markdown("""
                    <div style="display: flex; justify-content: flex-end; gap: 4px; margin-top: -1px; margin-bottom: 5px;">
                    """, unsafe_allow_html=True)
                    
                    # Edit button first (left)
                    edit_col, delete_col = st.columns([1, 1])
                    with edit_col:
                        edit_clicked = st.button("✏️", 
                                        key=f"edit_btn_{idx}", 
                                        help="Edit API Name",
                                        use_container_width=True)
                    
                    # Delete button second (right)
                    with delete_col:
                        delete_clicked = st.button("🗑️", 
                                          key=f"delete_{idx}", 
                                          help="Delete API",
                                          use_container_width=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Handle button clicks
                    if edit_clicked:
                        st.session_state[edit_name_key] = True
                        st.rerun()
                        
                    if delete_clicked:
                        # Get current APIs list
                        updated_apis = [api for i, api in enumerate(st.session_state.apis) if i != idx]
                        # Update session state
                        st.session_state.apis = updated_apis
                        # Refresh the page
                        st.rerun()

    # Add a button to start the performance test
    if st.button("Start Performance Test",
                 type="primary",
                 disabled=len(st.session_state.apis) == 0):
        # Show loading animation
        loading_html = """
        <div class="loading-animation">
            <img src="https://example.com/loading-icon.gif" alt="Loading...">
        </div>
        """
        st.markdown(loading_html, unsafe_allow_html=True)

        with st.spinner("Running performance test..."):
            # Simulate a long-running process (replace this with your actual test logic)
            time.sleep(5)  # Simulate a delay for the performance test
            
            # Store test results in session state
            tester = APITester(st.session_state.apis, virtual_users, ramp_up_time)
            st.session_state.test_results = tester.run_test()
            st.session_state.test_config = {
                'virtual_users': virtual_users,
                'ramp_up_time': ramp_up_time
            }
            st.success("Performance test completed!")

        # Hide loading animation
        st.markdown("<style>.loading-animation { display: none; }</style>", unsafe_allow_html=True)

    # Display results if available
    if 'test_results' in st.session_state:
        results = st.session_state.test_results
        virtual_users = st.session_state.test_config['virtual_users']
        ramp_up_time = st.session_state.test_config['ramp_up_time']

        # Convert status_code to integer if it's string
        df = pd.DataFrame(results)
        df['status_code'] = pd.to_numeric(df['status_code'], errors='coerce')

        # Calculate overall metrics and round to 1 decimal place
        total_requests = len(results)
        avg_response_time = round(sum(r["response_time"]
                                for r in results) / total_requests, 1)
        error_rate = round(sum(1 for r in results
                         if r["status_code"] >= 400) / total_requests * 100, 1)

        # Calculate percentiles and round to 1 decimal place
        p90 = round(df["response_time"].quantile(0.9), 1)
        p95 = round(df["response_time"].quantile(0.95), 1)
        p99 = round(df["response_time"].quantile(0.99), 1)

        st.header("Test Results")

        # Add endpoint names for better display
        df['endpoint'] = df['url'].apply(get_endpoint_name)

        # Summary metrics in boxes
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.metric("Virtual Users", virtual_users)
        with col2:
            st.metric("Ramp-up Time", f"{ramp_up_time}s")
        with col3:
            st.metric("Total APIs Tested", len(st.session_state.apis))
        with col4:
            st.metric("Avg Response Time", f"{avg_response_time:.2f}ms")
        with col5:
            st.metric("Total Requests", total_requests)
        with col6:
            st.metric("Error Rate", f"{error_rate:.2f}%")

        # Response time distribution
        st.subheader("Response Time Distribution")
        fig_dist = px.histogram(df,
                                x="response_time",
                                nbins=50,
                                labels={
                                    "response_time": "Response Time (ms)",
                                    "count": "Frequency"
                                },
                                title="Response Time Distribution")
        fig_dist.update_layout(showlegend=False, bargap=0.05)
        st.plotly_chart(fig_dist, use_container_width=True)

        # Error rates analysis - only show if errors exist
        has_errors = (df["status_code"] >= 400).any()
        if has_errors:
            st.subheader("Error Rates Analysis")
            # Add 'name' to the groupby if it exists in the dataframe
            if 'name' in df.columns:
                error_rates = df[df["status_code"] >= 400].groupby(["name", "endpoint"]).size() / df.groupby(["name", "endpoint"]).size()
                error_rates = error_rates.sort_values(ascending=False).head()
                # For display, we'll use the API name with endpoint
                error_labels = [f"{name} - {endpoint}" for (name, endpoint) in error_rates.index]
            else:
                error_rates = df[df["status_code"] >= 400].groupby("endpoint").size() / df.groupby("endpoint").size()
                error_rates = error_rates.sort_values(ascending=False).head()
                error_labels = error_rates.index
            
            fig_errors = px.bar(
                x=error_labels,
                y=error_rates.values * 100,  # Convert to percentage
                labels={
                    "y": "Error Rate (%)",
                    "x": "API Endpoint"
                },
                title="Error Rates by API")
            fig_errors.update_layout(yaxis_tickformat=',.1f',
                                     yaxis_title="Error Rate (%)",
                                     xaxis_title="API Endpoint",
                                     showlegend=False,
                                     xaxis_tickangle=0)
            st.plotly_chart(fig_errors, use_container_width=True)

        # Slowest APIs analysis (excluding failed APIs)
        st.subheader("Slowest APIs Analysis")
        
        # Filter dataframe to only include successful APIs
        df_successful = get_successful_apis(df)
        
        # If we have any successful APIs, show the bar chart
        if len(df_successful) > 0:
            # Create a dataframe with method, name, and endpoint for better display
            method_endpoint_df = df_successful.copy()
            if 'name' in df_successful.columns:
                method_endpoint_df['display_name'] = method_endpoint_df.apply(
                    lambda row: f"{row['name']} - {row['method']}", axis=1)
            else:
                method_endpoint_df['display_name'] = method_endpoint_df.apply(
                    lambda row: f"{row['method']} - {row['endpoint']}", axis=1)

            # Group by the display name instead of just endpoint
            # Round all values to 1 decimal place
            avg_times_with_method = method_endpoint_df.groupby("display_name")["response_time"].mean().round(1).sort_values(
                ascending=False).head()
            
            fig_slow = px.bar(x=avg_times_with_method.index,
                            y=avg_times_with_method.values,
                            labels={
                                "y": "Average Response Time (ms)",
                                "x": "API Endpoint"
                            },
                            title="Top 5 Slowest APIs (Excluding Failed APIs)")
            fig_slow.update_layout(yaxis_title="Average Response Time (ms)",
                                xaxis_title="API Endpoint",
                                showlegend=False,
                                xaxis_tickangle=0,
                                bargap=0.2)
            # Improve x-axis labels display
            fig_slow.update_xaxes(tickmode='array', 
                                tickvals=list(range(len(avg_times_with_method))),
                                ticktext=avg_times_with_method.index,
                                tickangle=15,
                                tickfont=dict(size=10))
            st.plotly_chart(fig_slow, use_container_width=True)
        else:
            # No successful APIs to display
            st.info("No successful APIs to display in the slowest APIs analysis. All APIs have errors.")

        # Add styling to error messages in dataframes
        st.markdown("""
        <style>
        .error-message {
            color: #E74C3C;
        }
        </style>
        """,
                    unsafe_allow_html=True)

        # Comprehensive API metrics
        st.subheader("Comprehensive API Metrics")
        # Get the method for each URL (taking the first method if multiple)
        method_by_url = df.groupby("url")["method"].first()
        
        # Get the name for each URL if available
        if 'name' in df.columns:
            name_by_url = df.groupby("url")["name"].first()
        
        # Group metrics and round to 1 decimal place for all time-based metrics
        # Round all numeric values to 1 decimal place consistently throughout the app
        api_metrics = df.groupby("url").agg({
            "response_time": ["mean", "min", "max", "count"],
            "status_code":
            lambda x: (x >= 400).mean() * 100
        })
        
        # Apply rounding to all float columns manually
        for col in api_metrics.select_dtypes(include=['float64']).columns:
            api_metrics[col] = api_metrics[col].round(1)
        api_metrics.columns = [
            "Avg Response Time", "Min Time", "Max Time", "Request Count",
            "Error Rate"
        ]

        # Add percentiles and round them to 1 decimal place
        api_metrics["p90%"] = df.groupby("url")["response_time"].quantile(0.9).round(1)
        api_metrics["p95%"] = df.groupby("url")["response_time"].quantile(0.95).round(1)
        api_metrics["p99%"] = df.groupby("url")["response_time"].quantile(0.99).round(1)

        # Add throughput (requests per second) and round to 1 decimal place
        api_metrics["Throughput"] = (api_metrics["Request Count"] / (
            virtual_users * ramp_up_time)).round(1)
            
        # Add method column and reorder
        api_metrics_display = format_dataframe(api_metrics.reset_index())
        api_metrics_display["method"] = api_metrics_display["url"].map(method_by_url)
        
        # Add name column if available
        if 'name' in df.columns:
            api_metrics_display["name"] = api_metrics_display["url"].map(name_by_url)
            
            # Reorder columns to put method first, then name, then URL
            cols = list(api_metrics_display.columns)
            cols.remove("method")
            cols.remove("url")
            cols.remove("name")
            cols = ["method", "name", "url"] + cols
        else:
            # Reorder columns to put method before URL
            cols = list(api_metrics_display.columns)
            cols.remove("method")
            cols.remove("url")
            cols = ["method", "url"] + cols

        # Apply final column ordering
        api_metrics_display = api_metrics_display[cols]
        
        # Create a styling function to highlight response times > 10 seconds (10000ms) in red
        # and format all time values to 1 decimal place
        def highlight_high_response_times(val):
            attr = 'color: red; font-weight: bold' 
            is_high = pd.Series(False, index=val.index)
            
            # Apply red color ONLY to Avg Response Time > 10000ms (10 seconds)
            if 'Avg Response Time' in val.index:
                is_high['Avg Response Time'] = val['Avg Response Time'] > 10000
                
            # Also highlight error messages in red
            if 'Error Message' in val.index:
                error_msg = val['Error Message']
                if isinstance(error_msg, str):
                    is_high['Error Message'] = error_msg != ''
                else:
                    is_high['Error Message'] = False
                
            return [attr if v else '' for v in is_high]
            
        # Apply custom styling function and force float formatting
        styled_df = api_metrics_display[cols].style.apply(highlight_high_response_times, axis=1)
        
        # Force 1 decimal place formatting for all float columns
        float_cols = api_metrics_display[cols].select_dtypes(include=['float']).columns
        if not float_cols.empty:
            styled_df = styled_df.format({col: '{:.1f}' for col in float_cols})
            
        # Display dataframe with styling
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Add styling for dataframes
        st.markdown("""
        <style>
        /* Styling for error messages */
        .error-message {
            color: #E74C3C !important;
            font-weight: bold;
        }
        
        /* Make sure the style applies to Streamlit elements */
        .stDataFrame td.error-message {
            color: #E74C3C !important;
            font-weight: bold;
        }
        
        /* Consistent URL styling across all tables */
        .stDataFrame td:nth-child(3), 
        table.dataframe td:nth-child(3),
        div.dataframe-container table td:nth-child(3),
        div[data-testid="stTable"] table td:nth-child(3) {
            font-size: 15px !important;
            color: rgb(224, 224, 224) !important;
            overflow-wrap: break-word !important;
            word-break: break-word !important;
            max-width: 400px !important;
            white-space: normal !important;
        }
        
        /* Ensure all dataframe containers have consistent styling */
        div.dataframe-container {
            width: 100%;
        }
        
        div.dataframe-container table {
            width: 100%;
            border-collapse: collapse;
        }
        
        /* Ensure all table cells have consistent padding */
        div.dataframe-container table td,
        div[data-testid="stTable"] table td,
        .stDataFrame td {
            padding: 8px !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Top 5 APIs with highest error rates - only show if errors exist
        if has_errors:
            st.subheader("Top 5 APIs with Highest Error Rates")
                        # Get the method for each URL for error analysis
            method_by_url = df.groupby("url")["method"].first()
            
            # Get the name for each URL if available
            if 'name' in df.columns:
                name_by_url = df.groupby("url")["name"].first()
            
            error_analysis = df[df["status_code"] >= 400].groupby("url").agg({
                "status_code": "count",
                "response_time": "mean",
                "error_message": lambda x: x.iloc[0]  # Take first error message
            }).sort_values("status_code", ascending=False).head()
            
            # Round response times to 1 decimal place
            error_analysis["response_time"] = error_analysis["response_time"].round(1)
            
            error_analysis.columns = [
                "Total Requests", "Avg Response Time", "Error Message"
            ]
            
            # Add method column and reorder
            error_analysis_display = format_dataframe(error_analysis.reset_index())
            error_analysis_display["method"] = error_analysis_display["url"].map(method_by_url)
            
            # Add name column if available
            if 'name' in df.columns:
                error_analysis_display["name"] = error_analysis_display["url"].map(name_by_url)
                
                # Reorder columns to put method first, then name, then URL
                cols = list(error_analysis_display.columns)
                cols.remove("method")
                cols.remove("url")
                cols.remove("name")
                cols = ["method", "name", "url"] + cols
            else:
                # Reorder columns to put method before URL
                cols = list(error_analysis_display.columns)
                cols.remove("method")
                cols.remove("url")
                cols = ["method", "url"] + cols
            
            # Apply final column ordering
            error_analysis_display = error_analysis_display[cols]
            
            # Create a styling function to highlight error messages in red and high response times
            def highlight_errors_and_times(val):
                attr = 'color: red; font-weight: bold'
                is_highlighted = pd.Series(False, index=val.index)
                
                # Highlight error messages - check if it's a string and not empty
                if 'Error Message' in val.index:
                    # Handle error message column - check if it's a non-empty string
                    error_msg = val['Error Message']
                    if isinstance(error_msg, str):
                        is_highlighted['Error Message'] = error_msg != ''
                    else:
                        is_highlighted['Error Message'] = False
                
                # Highlight only Avg Response Time if > 10 seconds
                if 'Avg Response Time' in val.index:
                    is_highlighted['Avg Response Time'] = val['Avg Response Time'] > 10000
                
                return [attr if v else '' for v in is_highlighted]
            
            # Apply custom styling function and force float formatting
            styled_df = error_analysis_display.style.apply(highlight_errors_and_times, axis=1)
            
            # Force 1 decimal place formatting for all float columns
            float_cols = error_analysis_display.select_dtypes(include=['float']).columns
            if not float_cols.empty:
                styled_df = styled_df.format({col: '{:.1f}' for col in float_cols})
                
            # Display interactive dataframe with the same features as Comprehensive API Metrics
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True
            )

        # Top 5 slowest APIs with details (excluding failed APIs)
        st.subheader("Top 5 Slowest APIs (Excluding Failed APIs)")
        
        # Get the method for each URL for slowest APIs
        method_by_url = df.groupby("url")["method"].first()
        
        # Get the name for each URL if available
        if 'name' in df.columns:
            name_by_url = df.groupby("url")["name"].first()

        # Filter dataframe to only include successful APIs
        df_successful = get_successful_apis(df)
        
                # If we have any successful APIs, show them, otherwise display a message
        if len(df_successful) > 0:
            slowest_apis = df_successful.groupby("url").agg({
                "response_time": ["mean", "min", "max", "count"]
            }).sort_values(("response_time", "mean"), ascending=False).head()
            
            # Round all time-based metrics to 1 decimal place
            for col in [("response_time", "mean"), ("response_time", "min"), ("response_time", "max")]:
                slowest_apis[col] = slowest_apis[col].round(1)
                
            # Flatten columns
            slowest_apis.columns = [
                "Avg Response Time", "Min Response Time", "Max Response Time", 
                "Request Count"
            ]
            
            # No need to reorder here - we'll do it after adding other columns
            
            # Add method column and reorder
            slowest_apis_display = format_dataframe(slowest_apis.reset_index())
            slowest_apis_display["method"] = slowest_apis_display["url"].map(method_by_url)
            
            # Add name column if available
            if 'name' in df.columns:
                slowest_apis_display["name"] = slowest_apis_display["url"].map(name_by_url)
                
                # Reorder columns to put method first, then name, then URL, then Request Count
                cols = list(slowest_apis_display.columns)
                cols.remove("method")
                cols.remove("url")
                cols.remove("name")
                cols.remove("Request Count")
                cols = ["method", "name", "url", "Request Count"] + [c for c in cols if c != "Request Count"]
            else:
                # Reorder columns to put method before URL, followed by Request Count
                cols = list(slowest_apis_display.columns)
                cols.remove("method")
                cols.remove("url")
                cols.remove("Request Count")
                cols = ["method", "url", "Request Count"] + [c for c in cols if c != "Request Count"]

            # Apply final column ordering
            slowest_apis_display = slowest_apis_display[cols]
            
            # Create a styling function to highlight high response times
            def highlight_response_times(val):
                attr = 'color: red; font-weight: bold'
                is_highlighted = pd.Series(False, index=val.index)
                
                # Highlight only Avg Response Time if > 10 seconds (10000ms)
                if 'Avg Response Time' in val.index:
                    is_highlighted['Avg Response Time'] = val['Avg Response Time'] > 10000
                
                return [attr if v else '' for v in is_highlighted]
            
            # Apply custom styling function and force float formatting
            styled_df = slowest_apis_display.style.apply(highlight_response_times, axis=1)
            
            # Force 1 decimal place formatting for all float columns
            float_cols = slowest_apis_display.select_dtypes(include=['float']).columns
            if not float_cols.empty:
                styled_df = styled_df.format({col: '{:.1f}' for col in float_cols})
                
            # Display interactive dataframe with the same features as Comprehensive API Metrics
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            # No successful APIs to display
            st.info("No successful APIs to display in the slowest APIs section. All APIs have errors.")

        # Generate Report section at the end
        st.markdown("---")  # Add a separator
        st.header("Generate Report")

        st.markdown(
            "Interactive web-based report with detailed metrics and charts")

        # Create a row for buttons at the bottom
        report_col1, report_col2 = st.columns(2)

        # Download report button in first column
        with report_col1:
            report_gen = ReportGenerator(results,
                                         virtual_users=virtual_users,
                                         ramp_up_time=ramp_up_time)
            report_html = report_gen.generate_html_report()
            st.download_button(
                label="Generate Report",
                data=report_html,
                file_name=
                f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                help="Download detailed performance report",
                type="primary",  # Use primary button type like Start Test button
                use_container_width=True  # Make button full width of column
            )

        # Clear All button in second column
        with report_col2:
            if st.button(
                    "🗑️ Clear All",
                    key="clear_all_btn",
                    help="Clear all results and start a new test",
                    type="secondary",  # Use secondary button type for contrast
                    use_container_width=True
            ):  # Make button full width of column
                reset_all_data()

    # Display the footer
#display_footer()

def update_api_name(idx):
    """Update the API name when changed in the text input"""
    if f"name_input_{idx}" in st.session_state:
        new_name = st.session_state[f"name_input_{idx}"]
        if new_name:  # Don't allow empty names
            st.session_state.apis[idx]['name'] = new_name
        st.session_state[f"edit_name_{idx}"] = False

if __name__ == "__main__":
    main()
