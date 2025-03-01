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

st.set_page_config(page_title="API Performance Tester", layout="wide")

# Custom CSS for the clear button positioning
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
</style>
""", unsafe_allow_html=True)


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

def main():
    st.title("API Performance Testing Tool")

    # Initialize session state for storing APIs
    if 'apis' not in st.session_state:
        st.session_state.apis = []
    
    # Form key for resetting the form completely
    if 'form_key' not in st.session_state:
        st.session_state.form_key = 0

    # Initialize form defaults
    clear_form()
    
    # Add clear button in header, only show when results exist
    if 'test_results' in st.session_state:
        # Place the actual button directly in the layout
        col1, col2 = st.columns([0.9, 0.1])
        with col2:
            if st.button("🗑️ Clear All", key="clear_all_btn", help="Clear all results and start a new test"):
                reset_all_data()

    with st.sidebar:
        st.header("Test Configuration")
        test_mode = st.radio("Test Input Mode",
                             ["Manual Entry", "Postman Collection"])

        # Test configuration
        virtual_users = st.number_input("Virtual Users", min_value=1, value=10)
        ramp_up_time = st.number_input("Ramp-up Time (seconds)",
                                       min_value=1,
                                       value=5)

        # Authentication section in sidebar
        st.header("Authentication")
        auth_type = st.selectbox("Authentication Type",
                                 ["None", "Bearer Token", "Basic Auth"])
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
                st.success(f"API added successfully! Total APIs: {len(st.session_state.apis)}")

    else:  # Postman Collection
        uploaded_file = st.file_uploader("Upload Postman Collection",
                                         type=["json"])
        if uploaded_file:
            collection = json.load(uploaded_file)
            imported_apis = []
            for item in collection.get("item", []):
                request = item.get("request", {})
                headers_dict = {
                    h["key"]: h["value"]
                    for h in request.get("header", [])
                }
                headers_dict.update(auth_details)  # Add auth headers
                api = {
                    "method": request.get("method", "GET"),
                    "url": request.get("url", {}).get("raw", ""),
                    "headers": headers_dict,
                    "body": request.get("body", {}).get("raw", "{}")
                }
                imported_apis.append(api)

            if st.button("Import APIs"):
                st.session_state.apis.extend(imported_apis)
                st.success(f"Successfully imported {len(imported_apis)} APIs")

    # Display configured APIs (common for both modes)
    if st.session_state.apis:
        st.subheader("Configured APIs")
        for idx, api in enumerate(st.session_state.apis):
            # Create a container for each API
            api_container = st.container()
            with api_container:
                expander = st.expander(f"{api['method']} - {api['url']}",
                                    expanded=False)
                
                # Add custom CSS to position the delete button inside the expander
                st.markdown(f"""
                <style>
                /* Style for delete button */
                .delete-btn-{idx} {{
                    font-size: 12px;
                    color: #E74C3C;
                    cursor: pointer;
                    margin-left: 10px;
                    vertical-align: middle;
                }}
                </style>
                """, unsafe_allow_html=True)
                
                # Display API details inside the expander
                with expander:
                    # Add the delete button at the top inside expander
                    col1, col2 = st.columns([0.97, 0.03])
                    with col2:
                        if st.button("🗑️", key=f"delete_{idx}", help="Delete API", 
                                    use_container_width=True):
                            st.session_state.apis.pop(idx)
                            st.rerun()
                    # Show API JSON
                    st.json(api)

    if st.button("Start Performance Test",
                 type="primary",
                 disabled=len(st.session_state.apis) == 0):
        # Store test results in session state
        tester = APITester(st.session_state.apis, virtual_users, ramp_up_time)
        st.session_state.test_results = tester.run_test()
        st.session_state.test_config = {
            'virtual_users': virtual_users,
            'ramp_up_time': ramp_up_time
        }

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
        fig_dist.update_layout(showlegend=False)
        st.plotly_chart(fig_dist, use_container_width=True)

        # Error rates analysis
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
        avg_times = df.groupby("endpoint")["response_time"].mean().sort_values(
            ascending=False).head()
        fig_slow = px.bar(x=avg_times.index,
                          y=avg_times.values,
                          labels={
                              "y": "Average Response Time (ms)",
                              "x": "API Endpoint"
                          },
                          title="Top 5 Slowest APIs")
        fig_slow.update_layout(yaxis_title="Average Response Time (ms)",
                               xaxis_title="API Endpoint",
                               showlegend=False,
                               xaxis_tickangle=0)
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

        st.dataframe(api_metrics)

        # Top 5 APIs with highest error rates
        st.subheader("Top 5 APIs with Highest Error Rates")
        error_analysis = df[df["status_code"] >= 400].groupby("url").agg({
            "status_code":
            "count",
            "response_time":
            "mean",
            "error_message":
            lambda x: x.iloc[0]  # Take first error message
        }).sort_values("status_code", ascending=False).head()
        error_analysis.columns = [
            "total_requests", "avg_response_time", "error_message"
        ]
        st.dataframe(error_analysis)

        # Top 5 slowest APIs with details
        st.subheader("Top 5 Slowest APIs")
        slowest_apis = df.groupby("url").agg({
            "response_time": ["mean", "min", "max", "count"],
            "status_code":
            lambda x: sum(x >= 400),  # Count errors instead of mean
            "error_message":
            lambda x: next((msg for msg in x
                            if msg), "")  # Get first non-empty error message
        }).sort_values(("response_time", "mean"), ascending=False).head()
        st.dataframe(slowest_apis)

        # Generate Report section at the end
        st.markdown("---")  # Add a separator
        st.header("Generate Report")

        st.markdown(
            "Interactive web-based report with detailed metrics and charts")

        # Download report button with primary button styling (same as Start Test)
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
            type="primary"  # Use primary button type like Start Test button
        )


if __name__ == "__main__":
    main()
