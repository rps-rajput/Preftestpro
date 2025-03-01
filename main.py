import streamlit as st
import json
import pandas as pd
from utils.api_tester import APITester
from utils.report_generator import ReportGenerator
import plotly.graph_objects as go
import plotly.express as px
import base64
from datetime import datetime

st.set_page_config(page_title="API Performance Tester", layout="wide")

def main():
    st.title("API Performance Testing Tool")

    # Initialize session state for storing APIs
    if 'apis' not in st.session_state:
        st.session_state.apis = []

    with st.sidebar:
        st.header("Test Configuration")
        test_mode = st.radio("Test Input Mode", ["Manual Entry", "Postman Collection"])

        # Test configuration
        virtual_users = st.number_input("Virtual Users", min_value=1, value=10)
        ramp_up_time = st.number_input("Ramp-up Time (seconds)", min_value=1, value=5)

        # Authentication section in sidebar
        st.header("Authentication")
        auth_type = st.selectbox("Authentication Type", ["None", "Bearer Token", "Basic Auth"])
        auth_details = {}

        if auth_type == "Bearer Token":
            auth_token = st.text_input("Bearer Token", type="password")
            if auth_token:
                auth_details = {"Authorization": f"Bearer {auth_token}"}
        elif auth_type == "Basic Auth":
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if username and password:
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                auth_details = {"Authorization": f"Basic {credentials}"}

    if test_mode == "Manual Entry":
        st.subheader("Add API")
        with st.form("api_form"):
            col1, col2 = st.columns(2)
            with col1:
                method = st.selectbox("HTTP Method", ["GET", "POST", "PUT", "DELETE"])
                url = st.text_input("API URL")

            headers = st.text_area("Headers (JSON format)", "{}")
            body = st.text_area("Request Body (JSON format)", "{}")

            submitted = st.form_submit_button("Add API")
            if submitted:
                try:
                    headers_dict = json.loads(headers)
                    headers_dict.update(auth_details)  # Add auth headers
                    body_dict = json.loads(body)

                    api = {
                        "method": method,
                        "url": url,
                        "headers": headers_dict,
                        "body": body_dict
                    }
                    st.session_state.apis.append(api)
                    st.success("API added successfully!")
                except json.JSONDecodeError:
                    st.error("Invalid JSON format in headers or body")

        # Display configured APIs
        if st.session_state.apis:
            st.subheader("Configured APIs")
            for idx, api in enumerate(st.session_state.apis):
                with st.expander(f"{api['method']} - {api['url']}", expanded=False):
                    st.json(api)
                    if st.button(f"Delete API {idx + 1}"):
                        st.session_state.apis.pop(idx)
                        st.rerun()

    else:  # Postman Collection
        uploaded_file = st.file_uploader("Upload Postman Collection", type=["json"])
        if uploaded_file:
            collection = json.load(uploaded_file)
            st.session_state.apis = []
            for item in collection.get("item", []):
                request = item.get("request", {})
                headers_dict = {h["key"]: h["value"] for h in request.get("header", [])}
                headers_dict.update(auth_details)  # Add auth headers
                api = {
                    "method": request.get("method", "GET"),
                    "url": request.get("url", {}).get("raw", ""),
                    "headers": headers_dict,
                    "body": request.get("body", {}).get("raw", "{}")
                }
                st.session_state.apis.append(api)

            # Display imported APIs
            st.subheader("Imported APIs")
            for idx, api in enumerate(st.session_state.apis):
                with st.expander(f"{api['method']} - {api['url']}", expanded=False):
                    st.json(api)
                    if st.button(f"Delete API {idx + 1}"):
                        st.session_state.apis.pop(idx)
                        st.rerun()

    if st.button("Start Test", type="primary", disabled=len(st.session_state.apis) == 0):
        with st.spinner("Running performance test..."):
            tester = APITester(st.session_state.apis, virtual_users, ramp_up_time)
            results = tester.run_test()

            report_gen = ReportGenerator(results)
            html_report = report_gen.generate_html_report()

            # Display results
            st.header("Test Results")

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Requests", len(results))
            with col2:
                avg_time = sum(r["response_time"] for r in results) / len(results)
                st.metric("Avg Response Time", f"{avg_time:.2f}ms")
            with col3:
                error_rate = sum(1 for r in results if r["status_code"] >= 400) / len(results) * 100
                st.metric("Error Rate", f"{error_rate:.2f}%")
            with col4:
                st.metric("Virtual Users", virtual_users)

            # Response time distribution
            st.subheader("Response Time Distribution")
            fig = px.histogram(
                [r["response_time"] for r in results],
                nbins=50,
                labels={"value": "Response Time (ms)"},
                opacity=0.8
            )
            st.plotly_chart(fig, use_container_width=True)

            # Error analysis
            st.subheader("Error Analysis")
            errors_df = pd.DataFrame([r for r in results if r["status_code"] >= 400])
            if not errors_df.empty:
                st.dataframe(errors_df[["url", "status_code", "error_message"]])

            # Download report
            report_html = report_gen.generate_html_report()
            b64 = base64.b64encode(report_html.encode()).decode()
            href = f'<a href="data:text/html;base64,{b64}" download="performance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html">Download HTML Report</a>'
            st.markdown(href, unsafe_allow_html=True)

if __name__ == "__main__":
    main()