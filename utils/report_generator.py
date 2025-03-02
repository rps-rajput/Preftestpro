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
        # Add endpoint names for better display
        self.df['endpoint'] = self.df['url'].apply(lambda x: x.split('/')[-1])

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
            bargap=0.05  # Add gap between bars
        )
        return fig.to_html(full_html=False)

    def _create_error_rate_plot(self):
        """Creates a bar chart of error rates by API"""
        error_rates = (self.df[self.df["status_code"] >= 400]
                      .groupby("endpoint")
                      .size()
                      .divide(self.df.groupby("endpoint").size())
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
            texttemplate='%{text:.1f}%',
            textposition='outside'
        )
        fig.update_layout(
            yaxis_tickformat=',.1f',
            yaxis_title="Error Rate (%)",
            xaxis_title="API Endpoint",
            showlegend=False,
            xaxis_tickangle=0
        )
        return fig.to_html(full_html=False)

    def _create_slowest_apis_plot(self):
        """Creates a bar chart of slowest APIs"""
        avg_times = (self.df.groupby("endpoint")["response_time"]
                    .mean()
                    .sort_values(ascending=False)
                    .head(5))  # Show top 5 slowest APIs

        fig = px.bar(
            x=avg_times.index,
            y=avg_times.values,
            title="Top 5 Slowest APIs",
            labels={"y": "Average Response Time (ms)", "x": "API Endpoint"},
            text=avg_times.values
        )
        fig.update_traces(
            marker_color="#2E86C1",
            marker_line_color="#2874A6",
            texttemplate='%{text:.0f} ms',
            textposition='outside'
        )
        fig.update_layout(
            yaxis_title="Average Response Time (ms)",
            xaxis_title="API Endpoint",
            showlegend=False,
            xaxis_tickangle=0,
            bargap=0.2  # Add gap between bars
        )
        return fig.to_html(full_html=False)

    def _calculate_api_metrics(self):
        """Calculates comprehensive metrics for each API"""
        # First, get the method for each URL (taking the first method if multiple)
        method_by_url = self.df.groupby("url")["method"].first()
        
        metrics = self.df.groupby("url").agg({
            "response_time": ["mean", "min", "max", "count"],
            "status_code": lambda x: (x >= 400).mean() * 100
        }).round(2)

        # Calculate percentiles
        p90 = self.df.groupby("url")["response_time"].quantile(0.9)
        p95 = self.df.groupby("url")["response_time"].quantile(0.95)
        p99 = self.df.groupby("url")["response_time"].quantile(0.99)

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
        metrics.columns = ["avg_response_time", "min_time", "max_time", "request_count", 
                         "error_rate", "p90", "p95", "p99", "throughput"]
        
        # Add method column and reorder
        result = metrics.reset_index()
        result["method"] = result["url"].map(method_by_url)
        
        # Reorder columns to put method after URL
        cols = list(result.columns)
        cols.remove("method")
        cols.insert(1, "method")  # Insert method after url
        
        return result[cols]

    def _analyze_errors(self):
        """Analyzes top 5 APIs with highest error rates"""
        error_df = self.df[self.df["status_code"] >= 400]
        error_analysis = error_df.groupby("url").agg({
            "status_code": "count",
            "response_time": "mean",
            "error_message": lambda x: x.iloc[0] if len(x) > 0 else ""
        }).sort_values("status_code", ascending=False).head()

        error_analysis.columns = ["total_errors", "avg_response_time", "error_message"]
        error_analysis["error_rate"] = (error_analysis["total_errors"] / 
                                      self.df.groupby("url").size() * 100)

        return error_analysis.reset_index()

    def _analyze_slowest_apis(self):
        """Analyzes top 5 slowest APIs with details"""
        result = (self.df.groupby("url").agg({
            "response_time": ["mean", "min", "max"],
            "status_code": lambda x: sum(x >= 400),
            "error_message": lambda x: x.iloc[0] if any(x.notna()) else ""
        }).sort_values(("response_time", "mean"), ascending=False)
        .head())

        # Flatten multi-level columns
        result.columns = ['mean_response_time', 'min_response_time', 'max_response_time', 
                         'error_count', 'error_message']
        return result.reset_index()

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
        
        # Only analyze errors if they exist
        error_analysis = self._analyze_errors() if has_errors else pd.DataFrame()

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
            api_metrics=metrics,
            error_analysis=error_analysis,
            slowest_apis=slowest_apis,
            has_errors=has_errors  # Pass flag to template
        )