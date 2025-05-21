import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from jinja2 import Template
import numpy as np

class ReportGenerator:
    def __init__(self, results, virtual_users=None, ramp_up_time=None):
        self.results = results
        self.virtual_users = virtual_users
        self.ramp_up_time = ramp_up_time
        self.df = pd.DataFrame(results)
        # Convert status_code to numeric type
        self.df['status_code'] = pd.to_numeric(self.df['status_code'], errors='coerce')
        # Add endpoint names for better display if not already present
        if 'name' not in self.df.columns or self.df['name'].isna().all() or (self.df['name'] == '').all():
            self.df['name'] = self.df['url'].apply(self._get_shortened_endpoint)
        
    def _create_response_time_plot(self):
        """Creates a histogram of response times"""
        fig = px.histogram(
            self.df,
            x="response_time",
            nbins=50,
            title="Response Time Distribution",
            labels={"response_time": "Response Time (ms)", "count": "Frequency"},
            opacity=0.8
        )
        fig.update_layout(
            showlegend=False,
            plot_bgcolor="white",
            paper_bgcolor="white",
            bargap=0.05,  # Add gap between bars
            xaxis_tickformat=',.1f'  # Format x-axis to 1 decimal place
        )
        return fig.to_html(full_html=False)

    def _get_shortened_endpoint(self, endpoint):
        """Returns a shortened version of the endpoint for display in charts"""
        # Find the last segment of the URL after /, = or other separators
        separators = ['/', '=', '?', '&', '-', '_']
        for sep in separators:
            if sep in endpoint:
                parts = endpoint.split(sep)
                endpoint = parts[-1]  # Take the last part
        # Limit to 15 characters max
        if len(endpoint) > 15:
            endpoint = endpoint[:12] + "..."
        return endpoint
        
    def _create_error_rate_plot(self):
        """Creates a bar chart of error rates by API"""
        # Use name field instead of endpoint
        if 'name' not in self.df.columns:
            self.df['name'] = self.df['url'].apply(self._get_shortened_endpoint)
            
        # Group by name directly since it's already shortened
        error_rates = (self.df[self.df["status_code"] >= 400]
                      .groupby("name")
                      .size()
                      .divide(self.df.groupby("name").size())
                      .sort_values(ascending=False)
                      .head(5))  # Show top 5 APIs with highest error rates

        fig = px.bar(
            x=error_rates.index,
            y=error_rates.values * 100,  # Convert to percentage
            title="Error Rates by API",
            labels={"y": "Error Rate (%)", "x": "API Endpoint"},
            text=error_rates.values * 100  # Show percentage on bars
        )
        fig.update_traces(
            marker_color="#FF6B6B",
            marker_line_color="#E74C3C",
            texttemplate='%{text:.1f}%',  # Ensure only 1 decimal place
            textposition='outside'
        )
        fig.update_layout(
            yaxis_tickformat=',.1f',  # Ensure only 1 decimal place
            yaxis_title="Error Rate (%)",
            xaxis_title="API Endpoint",
            showlegend=False,
            xaxis_tickangle=0
        )
        return fig.to_html(full_html=False)

    def _create_slowest_apis_plot(self):
        """Creates a bar chart of slowest APIs (excluding failed APIs)"""
        # Filter out URLs that have any failed requests
        successful_urls = self.df.groupby("url")["status_code"].apply(lambda x: all(x < 400))
        successful_urls = successful_urls[successful_urls].index.tolist()
        
        # Filter dataframe to only include successful APIs
        df_successful = self.df[self.df["url"].isin(successful_urls)]
        
        # If no successful APIs, return an empty plot
        if len(df_successful) == 0:
            # Create an empty figure
            fig = go.Figure()
            fig.update_layout(
                title="Top 5 Slowest APIs (No Successful APIs to Display)",
                xaxis_title="API Endpoint",
                yaxis_title="Average Response Time (ms)",
                showlegend=False
            )
            return fig.to_html(full_html=False)
            
        # Use name field which is already available
        if 'name' not in df_successful.columns:
            df_successful['name'] = df_successful['url'].apply(self._get_shortened_endpoint)
            
        # Create a display name that includes method and name
        df_successful['display_name'] = df_successful.apply(
            lambda row: f"{row['method']} - {row['name']}", axis=1)
            
        avg_times = (df_successful.groupby("display_name")["response_time"]
                    .mean()
                    .round(1)  # Round to 1 decimal place
                    .sort_values(ascending=False)
                    .head(5))  # Show top 5 slowest APIs

        fig = px.bar(
            x=avg_times.index,
            y=avg_times.values,
            title="Top 5 Slowest APIs (Excluding Failed APIs)",
            labels={"y": "Average Response Time (ms)", "x": "API Endpoint"},
            text=avg_times.values
        )
        fig.update_traces(
            marker_color="#2E86C1",
            marker_line_color="#2874A6",
            texttemplate='%{text:.1f} ms',  # Ensure only 1 decimal place
            textposition='outside'
        )
        fig.update_layout(
            yaxis_tickformat=',.1f',  # Format y-axis to 1 decimal place
            yaxis_title="Average Response Time (ms)",
            xaxis_title="API Endpoint",
            showlegend=False,
            xaxis_tickangle=15,  # Angle the labels slightly for better readability
            bargap=0.2  # Add gap between bars
        )
        # Improve x-axis labels display
        fig.update_xaxes(
            tickmode='array',
            tickvals=list(range(len(avg_times))),
            ticktext=avg_times.index,
            tickfont=dict(size=10)
        )
        return fig.to_html(full_html=False)

    def _calculate_api_metrics(self):
        """Calculates comprehensive metrics for each API"""
        # First, get the method for each URL (taking the first method if multiple)
        method_by_url = self.df.groupby("url")["method"].first()
        
        # Get name for each URL
        name_by_url = self.df.groupby("url")["name"].first()
        
        metrics = self.df.groupby("url").agg({
            "response_time": ["mean", "min", "max", "count"],
            "status_code": lambda x: (x >= 400).mean() * 100
        }).round(1)  # Round to 1 decimal place instead of 2

        # Calculate percentiles and round to 1 decimal place
        p90 = self.df.groupby("url")["response_time"].quantile(0.9).round(1)
        p95 = self.df.groupby("url")["response_time"].quantile(0.95).round(1)
        p99 = self.df.groupby("url")["response_time"].quantile(0.99).round(1)

        # Combine all metrics
        metrics = pd.concat([
            metrics,
            p90.rename("p90"),
            p95.rename("p95"),
            p99.rename("p99")
        ], axis=1)

        # Calculate throughput
        metrics["throughput"] = metrics[("response_time", "count")] / (
            (self.virtual_users or len(set(self.df.index))) * (self.ramp_up_time or 5)
        )

        # Flatten column names
        metrics.columns = ["Avg Response Time", "Min Time", "Max Time", "Request Count", 
                         "Error Rate", "p90%", "p95%", "p99%", "Throughput"]
        
        # Add method and name columns and reorder
        result = metrics.reset_index()
        result["method"] = result["url"].map(method_by_url)
        result["name"] = result["url"].map(name_by_url)
        
        # Reorder columns to put method first, then name, then URL, then Request Count
        cols = list(result.columns)
        cols.remove("method")
        cols.remove("url")
        cols.remove("name")
        cols.remove("Request Count")
        # Then add all other columns except Request Count
        remaining_cols = [c for c in cols if c != "Request Count"]
        cols = ["method", "name", "url", "Request Count"] + remaining_cols
        
        return result[cols]

    def _analyze_errors(self):
        """Analyzes top 5 APIs with highest error rates"""
        error_df = self.df[self.df["status_code"] >= 400]
        error_analysis = error_df.groupby("url").agg({
            "status_code": "count",
            "response_time": "mean",
            "error_message": lambda x: x.iloc[0] if len(x) > 0 else "",
            "method": lambda x: x.iloc[0]  # Get the method for each URL
        }).sort_values("status_code", ascending=False).head()

        # Round response time to 1 decimal place
        error_analysis["response_time"] = error_analysis["response_time"].round(1)

        error_analysis.columns = ["Total Errors", "Avg Response Time", "Error Message", "method"]
        error_analysis["Error Rate"] = (error_analysis["Total Errors"] / 
                                      self.df.groupby("url").size() * 100).round(1)  # Round error rate to 1 decimal

        result = error_analysis.reset_index()
        
        # Add name column if available
        if 'name' in self.df.columns:
            name_by_url = self.df.groupby("url")["name"].first()
            result["name"] = result["url"].map(name_by_url)
            
            # Reorder columns to put method first, then name, then URL
            cols = list(result.columns)
            cols.remove("method")
            cols.remove("url")
            cols.remove("name")
            cols = ["method", "name", "url"] + cols
        else:
            # Reorder columns to put method before URL
            cols = list(result.columns)
            cols.remove("method")
            cols.remove("url")
            cols = ["method", "url"] + cols
        
        return result[cols]

    def _analyze_slowest_apis(self):
        """Analyzes top 5 slowest APIs with details (excluding failed APIs)"""
        # Filter out URLs that have any failed requests
        successful_urls = self.df.groupby("url")["status_code"].apply(lambda x: all(x < 400))
        successful_urls = successful_urls[successful_urls].index.tolist()
        
        # Filter dataframe to only include successful APIs
        df_successful = self.df[self.df["url"].isin(successful_urls)]
        
        # If we have any successful APIs, analyze them
        if len(df_successful) > 0:
            result = (df_successful.groupby("url").agg({
                "response_time": ["mean", "min", "max", "count"],  # Added count for Request Count
                "method": lambda x: x.iloc[0]  # Get the method for each URL
            }).sort_values(("response_time", "mean"), ascending=False)
            .head())
            
            # Round response times to 1 decimal place
            for col in [("response_time", "mean"), ("response_time", "min"), ("response_time", "max")]:
                result[col] = result[col].round(1)
                
            # Flatten multi-level columns
            result.columns = ['Avg Response Time', 'Min Response Time', 'Max Response Time', 'Request Count', 'method']
            
            result = result.reset_index()
            
            # Add name column if available
            if 'name' in self.df.columns:
                name_by_url = self.df.groupby("url")["name"].first()
                result["name"] = result["url"].map(name_by_url)
                
                # Reorder columns to put method first, then name, then URL, then Request Count
                cols = list(result.columns)
                cols.remove("method")
                cols.remove("url")
                cols.remove("name")
                cols.remove("Request Count")
                cols = ["method", "name", "url", "Request Count"] + [c for c in cols if c != "Request Count"]
            else:
                # Reorder columns to put method before URL, followed by Request Count
                cols = list(result.columns)
                cols.remove("method")
                cols.remove("url")
                cols.remove("Request Count")
                cols = ["method", "url", "Request Count"] + [c for c in cols if c != "Request Count"]
            
            return result[cols]
        else:
            # Return empty DataFrame with the correct columns if no successful APIs
            columns = ['method', 'url', 'Request Count', 'Avg Response Time', 'Min Response Time', 'Max Response Time']
            if 'name' in self.df.columns:
                columns.insert(1, 'name')
            return pd.DataFrame(columns=columns)

    def generate_html_report(self):
        # Calculate metrics
        metrics = self._calculate_api_metrics()
        slowest_apis = self._analyze_slowest_apis()

        # Calculate overall metrics
        total_requests = len(self.results)
        avg_response_time = self.df["response_time"].mean()
        error_rate = (self.df["status_code"] >= 400).mean() * 100
        total_apis = len(self.df["url"].unique())
        
        # Check if there are any errors
        has_errors = (self.df["status_code"] >= 400).any()
        
        # Generate plots - error plot only if errors exist
        response_time_plot = self._create_response_time_plot()
        error_rate_plot = self._create_error_rate_plot() if has_errors else ""
        slowest_apis_plot = self._create_slowest_apis_plot()
        
        # Round avg_response_time to 1 decimal place for metrics display
        avg_response_time = round(avg_response_time, 1)
        error_rate = round(error_rate, 1)
        
        # Only analyze errors if they exist
        error_analysis = self._analyze_errors() if has_errors else pd.DataFrame()
        
        # Configure pandas to display only 1 decimal place for floats in HTML tables
        pd.set_option('display.float_format', '{:.1f}'.format)

        # Ensure Request Count is formatted as integer for better display
        if 'Request Count' in slowest_apis.columns:
            slowest_apis['Request Count'] = slowest_apis['Request Count'].astype(int)

        # Format dataframes to use 1 decimal place for floats
        def format_df_for_html(df):
            # Apply custom formatting to each numeric column
            formatted_df = df.copy()
            
            # Check if 'Avg Response Time' column exists
            if 'Avg Response Time' in formatted_df.columns:
                # Create a formatter for Avg Response Time that adds red styling for values > 10000
                def format_avg_response_time(value):
                    if pd.notnull(value):
                        if value > 10000:
                            return f'<span style="color:#E74C3C; font-weight:bold;">{value:.1f}</span>'
                        else:
                            return f"{value:.1f}"
                    return value
                
                # Apply the formatter to the Avg Response Time column
                formatted_df['Avg Response Time'] = formatted_df['Avg Response Time'].map(format_avg_response_time)
            
            # Check if 'Error Message' column exists and format it
            if 'Error Message' in formatted_df.columns:
                def format_error_message(value):
                    if pd.notnull(value) and value != '':
                        return f'<span style="color:#E74C3C; font-weight:bold;">{value}</span>'
                    return value
                
                # Apply the formatter to error messages
                formatted_df['Error Message'] = formatted_df['Error Message'].map(format_error_message)
            
            # Format remaining numeric columns without any special styling
            for col in formatted_df.columns:
                # Skip the already formatted columns
                if col in ['Avg Response Time', 'Error Message']:
                    continue
                
                # Skip non-numeric columns
                if formatted_df[col].dtype.kind not in 'ifc':
                    continue
                
                # For Min Time, Max Time, p90%, p95%, p99% - Add the ms suffix but don't highlight high values
                if col in ['Min Time', 'Min Response Time', 'Max Time', 'Max Response Time', 'p90%', 'p95%', 'p99%']:
                    formatted_df[col] = formatted_df[col].map(lambda x: f"{x:.1f}" if pd.notnull(x) else x)
                # For all other numeric floating point values, just format to one decimal
                elif formatted_df[col].dtype.kind == 'f':
                    formatted_df[col] = formatted_df[col].map(lambda x: f"{x:.1f}" if pd.notnull(x) else x)
                    
            # Add a class to the dataframe for easier JavaScript targeting
            result_html = formatted_df.to_html(classes="dataframe", escape=False)
            return result_html
            
        # Format dataframes before rendering
        metrics_html = format_df_for_html(metrics)
        error_analysis_html = format_df_for_html(error_analysis) if has_errors else ""
        slowest_apis_html = format_df_for_html(slowest_apis)

        # Load template from file and render
        with open("templates/report_template.html", "r") as f:
            template = Template(f.read())
            
        return template.render(
            virtual_users=self.virtual_users or len(set(self.df.index)),
            ramp_up_time=self.ramp_up_time or 5,
            total_apis=total_apis,
            avg_response_time=avg_response_time,
            total_requests=total_requests,
            error_rate=error_rate,
            response_time_plot=response_time_plot,
            error_rate_plot=error_rate_plot,
            slowest_apis_plot=slowest_apis_plot,
            api_metrics=metrics_html,
            error_analysis=error_analysis_html,
            slowest_apis=slowest_apis_html,
            has_errors=has_errors  # Pass flag to template
        )