import streamlit as st
import json
import pandas as pd
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

    /* Reduce gap between columns */
    div[data-testid="column"] {
        padding: 0 !important;
        margin: 0 !important;
    }
    
    div[data-testid="column"]:first-child {
        padding-right: 5px !important;
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
    for item in blazmeter_data.get('traffic', []):
        method = item.get('method', 'GET')
        url = item.get('url', '')
        
        # Extract headers
        headers = {}
        for header in item.get('headers', []):
            name = header.get('name', '')
            value = header.get('value', '')
            if name and name not in ['User-Agent', 'sec-ch-ua', 'sec-ch-ua-mobile', 'sec-ch-ua-platform']:
                headers[name] = value
        
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
        
        # Create API object
        api = {
            "method": method,
            "url": url,
            "headers": headers,
            "body": body
        }
        apis.append(api)
    
    return apis


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

                        api = {
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
                    for item in collection.get("item", []):
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

                        api = {
                            "method": request.get("method", "GET"),
                            "url": request.get("url", {}).get("raw", ""),
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
                    
                    # Create custom label with tooltip using HTML and CSS
                    st.markdown(f"""
                    <div class="position-label" style="display: flex; align-items: center; margin-bottom: 5px;">
                        <span>Position</span>
                        <div class="tooltip" style="position: relative; display: inline-block; margin-left: 5px; cursor: help;">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#9E9E9E" viewBox="0 0 16 16">
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
                    
                    # Position number input with a compact move icon
                    position_col1, position_col2 = st.columns([4, 1])

                    with position_col1:
                        # Position number input without label (since we added custom label above)
                        new_pos = st.number_input(
                            label="Position Number", 
                            min_value=1,
                            max_value=len(st.session_state.apis),
                            value=int(current_pos),
                            step=1,
                            key=f"pos_{idx}",
                            label_visibility="collapsed"  # Fixed: Use string "collapsed" instead of a variable reference
                        )

                    with position_col2:
                        # Track if this API was just moved to prevent showing the button after a successful move
                        just_moved_key = f"just_moved_{idx}"
                        if just_moved_key not in st.session_state:
                            st.session_state[just_moved_key] = False
                        
                        # Add vertical spacing for perfect alignment with the number input box
                        st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
                        
                        # Only show Move icon if position has changed AND this API wasn't just moved
                        if new_pos != current_pos and not st.session_state[just_moved_key]:
                            # Use a better swap icon that looks more like the provided image
                            # Using "🔄" (Unicode U+1F504, ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS)
                            if st.button("🔄", key=f"move_btn_{idx}", help="Move API to new position", type="secondary"):
                                # Move the API
                                api_to_move = st.session_state.apis[idx]
                                new_apis = [api for i, api in enumerate(st.session_state.apis) if i != idx]
                                target_idx = new_pos - 1  # Convert to 0-based index
                                new_apis.insert(target_idx, api_to_move)
                                st.session_state.apis = new_apis
                                
                                # Mark this API as just moved to hide the button
                                st.session_state[just_moved_key] = True
                                
                                st.rerun()
                            
                            # Add custom class to button for styling
                            st.markdown(f"""
                            <script>
                                (function() {{
                                    const buttons = parent.document.querySelectorAll('[key="move_btn_{idx}"]');
                                    for (const button of buttons) {{
                                        button.classList.add('move-btn');
                                    }}
                                }})()
                            </script>
                            """, unsafe_allow_html=True)
                        else:
                            # Reset the "just moved" state if position is back to current
                            if new_pos == current_pos and st.session_state[just_moved_key]:
                                st.session_state[just_moved_key] = False
                                
                            # Add placeholder with same height to maintain alignment
                            st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)

                # API details in center column with cleaner styling
                with cols[1]:
                    # Create a cleaner heading for each API with method badge and URL
                    method_colors = {
                        "GET": "#4CAF50",
                        "POST": "#2196F3",
                        "PUT": "#FF9800",
                        "DELETE": "#F44336",
                        "PATCH": "#9C27B0"
                    }
                    
                    # Get color for method badge (default to gray if not in our mapping)
                    method_color = method_colors.get(api['method'], "#607D8B")
                    
                    # Create a styled method badge and URL display
                    st.markdown(f"""
                    <div style="display:flex; align-items:center; margin-bottom:5px;">
                        <span style="background-color:{method_color}; color:white; padding:2px 8px; border-radius:4px; font-size:14px; margin-right:10px;">
                            {api['method']}
                        </span>
                        <span style="font-size:15px; color:#E0E0E0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                            {api['url']}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Expandable details section
                    with st.expander("View Details", expanded=False):
                        st.json(api)
                
                # Delete button in right column
                with cols[2]:
                    st.write("")  # Add some spacing
                    if st.button("🗑️", key=f"delete_{idx}", help="Delete API"):
                        # Get current APIs list
                        updated_apis = [api for i, api in enumerate(st.session_state.apis) if i != idx]
                        # Update session state
                        st.session_state.apis = updated_apis
                        # Refresh the page
                        st.rerun()

    #Initialize containers for modals
    faq_modal = st.empty()
    about_modal = st.empty()

    # Sidebar for navigation
    st.sidebar.title("Navigation")
    if st.sidebar.button("FAQ"):
        toggle_faq()  # Toggle FAQ modal visibility

    if st.sidebar.button("About"):
        toggle_about()  # Toggle About modal visibility

    # FAQ Modal
    if st_session.show_faq:
        faq_modal.markdown(f"""
        <div class="modal">
            <div class="modal-content">
                <svg class="close" width="10" height="10" viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg" style="stroke: currentcolor;">
                    <path d="M9 1L5 5M1 9L5 5M5 5L1 1M5 5L9 9" stroke-width="2" stroke-linecap="round"></path>
                </svg>
                <h2>Frequently Asked Questions</h2>
                <div>
                    <p>Question 1 - What is this application?</p>
                    <p> Answer - This application is designed to test the performance of APIs.</p>
                    <p>Question 2 - How do I use it?</p>
                    <p> Answer - You can input your API details and click on 'Start Performance Test'.</p>
                    <p>Question 3 - What metrics are displayed?</p>
                    <p> Answer - The application shows response times, error rates, and more.</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # About Modal
    if st_session.show_about:
        about_modal.markdown(f"""
        <div class="modal">
            <div class="modal-content">
                <svg class="close" width="10" height="10" viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg" style="stroke: currentcolor;">
                    <path d="M9 1L5 5M1 9L5 5M5 5L1 1M5 5L9 9" stroke-width="2" stroke-linecap="round"></path>
                </svg>
                <h2>About</h2>
                <p>For any queries, please send an email to <strong>rps.rajputt@gmail.com</strong>.</p>
                <p>You can also reach out to us at <strong>rps.rajputt@gmail.com</strong> for further assistance.</p>
                <p>Copyright 2025 Snowflake Inc. All rights reserved.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)


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

        # Calculate overall metrics
        total_requests = len(results)
        avg_response_time = sum(r["response_time"]
                                for r in results) / total_requests
        error_rate = sum(1 for r in results
                         if r["status_code"] >= 400) / total_requests * 100

        # Calculate percentiles
        p90 = df["response_time"].quantile(0.9)
        p95 = df["response_time"].quantile(0.95)
        p99 = df["response_time"].quantile(0.99)

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
            error_rates = df[df["status_code"] >= 400].groupby(
                "endpoint").size() / df.groupby("endpoint").size()
            error_rates = error_rates.sort_values(ascending=False).head()
            fig_errors = px.bar(
                x=error_rates.index,
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

        # Slowest APIs analysis
        st.subheader("Slowest APIs Analysis")
        # Create a dataframe with method and endpoint for better display
        method_endpoint_df = df.copy()
        method_endpoint_df['display_name'] = method_endpoint_df.apply(
            lambda row: f"{row['method']} - {row['endpoint']}", axis=1)
        
        # Group by the display name instead of just endpoint
        avg_times_with_method = method_endpoint_df.groupby("display_name")["response_time"].mean().sort_values(
            ascending=False).head()
        
        fig_slow = px.bar(x=avg_times_with_method.index,
                          y=avg_times_with_method.values,
                          labels={
                              "y": "Average Response Time (ms)",
                              "x": "API Endpoint"
                          },
                          title="Top 5 Slowest APIs")
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
        
        api_metrics = df.groupby("url").agg({
            "response_time": ["mean", "min", "max", "count"],
            "status_code":
            lambda x: (x >= 400).mean() * 100
        }).round(2)
        api_metrics.columns = [
            "avg_response_time", "min_time", "max_time", "request_count",
            "error_rate"
        ]

        # Add percentiles
        api_metrics["p90"] = df.groupby("url")["response_time"].quantile(0.9)
        api_metrics["p95"] = df.groupby("url")["response_time"].quantile(0.95)
        api_metrics["p99"] = df.groupby("url")["response_time"].quantile(0.99)

        # Add throughput (requests per second)
        api_metrics["throughput"] = api_metrics["request_count"] / (
            virtual_users * ramp_up_time)
            
        # Add method column and reorder
        api_metrics_display = api_metrics.reset_index()
        api_metrics_display["method"] = api_metrics_display["url"].map(method_by_url)
        
        # Reorder columns to put method before URL
        cols = list(api_metrics_display.columns)
        cols.remove("method")
        cols.remove("url")
        cols = ["method", "url"] + cols
        
        st.dataframe(api_metrics_display[cols])

        # Add styling for error messages in dataframes
        st.markdown("""
        <style>
        .error-message {
            color: #E74C3C !important;
            font-weight: bold;
        }
        
        /* Make sure the style applies to Streamlit elements */
        .stDataFrame td.error-message {
            color: #E74C3C !important;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Top 5 APIs with highest error rates - only show if errors exist
        if has_errors:
            st.subheader("Top 5 APIs with Highest Error Rates")
            # Get the method for each URL for error analysis
            method_by_url = df.groupby("url")["method"].first()
            
            error_analysis = df[df["status_code"] >= 400].groupby("url").agg({
                "status_code": "count",
                "response_time": "mean",
                "error_message": lambda x: x.iloc[0]  # Take first error message
            }).sort_values("status_code", ascending=False).head()
            
            error_analysis.columns = [
                "total_requests", "avg_response_time", "error_message"
            ]
            
            # Add method column and reorder
            error_analysis_display = error_analysis.reset_index()
            error_analysis_display["method"] = error_analysis_display["url"].map(method_by_url)
            
            # Reorder columns to put method before URL
            cols = list(error_analysis_display.columns)
            cols.remove("method")
            cols.remove("url")
            cols = ["method", "url"] + cols
            error_analysis_display = error_analysis_display[cols]
            
            # Apply styling to error messages
            error_analysis_styled = error_analysis_display.copy()
            error_analysis_styled["error_message"] = error_analysis_styled["error_message"].apply(
                lambda x: f'<span class="error-message">{x}</span>')
            
            st.write(error_analysis_styled.to_html(escape=False, index=False), unsafe_allow_html=True)

        # Top 5 slowest APIs with details
        st.subheader("Top 5 Slowest APIs")
        # Get the method for each URL for slowest APIs
        method_by_url = df.groupby("url")["method"].first()
        
        slowest_apis = df.groupby("url").agg({
            "response_time": ["mean", "min", "max", "count"],
            "status_code": lambda x: sum(x >= 400),  # Count errors instead of mean
            "error_message": lambda x: next((msg for msg in x if msg), "")  # Get first non-empty error message
        }).sort_values(("response_time", "mean"), ascending=False).head()
        
        # Flatten columns
        slowest_apis.columns = [
            "mean_response_time", "min_response_time", "max_response_time", 
            "request_count", "error_count", "error_message"
        ]
        
        # Add method column and reorder
        slowest_apis_display = slowest_apis.reset_index()
        slowest_apis_display["method"] = slowest_apis_display["url"].map(method_by_url)
        
        # Reorder columns to put method before URL
        cols = list(slowest_apis_display.columns)
        cols.remove("method")
        cols.remove("url")
        cols = ["method", "url"] + cols
        slowest_apis_display = slowest_apis_display[cols]
        
        # Apply styling to error messages if present
        slowest_apis_styled = slowest_apis_display.copy()
        slowest_apis_styled["error_message"] = slowest_apis_styled["error_message"].apply(
            lambda x: f'<span class="error-message">{x}</span>' if x else x)
        
        st.write(slowest_apis_styled.to_html(escape=False, index=False), unsafe_allow_html=True)

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


if __name__ == "__main__":
    main()
