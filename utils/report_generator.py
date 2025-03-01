import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from jinja2 import Template
import numpy as np

class ReportGenerator:
    def __init__(self, results):
        self.results = results
        self.df = pd.DataFrame(results)
        # Convert status_code to numeric type
        self.df['status_code'] = pd.to_numeric(self.df['status_code'], errors='coerce')

    def generate_html_report(self):
        # Calculate metrics
        metrics = self._calculate_api_metrics()
        error_analysis = self._analyze_errors()
        slowest_apis = self._analyze_slowest_apis()

        # Calculate overall metrics
        total_requests = len(self.results)
        avg_response_time = self.df["response_time"].mean()
        error_rate = (self.df["status_code"] >= 400).mean() * 100
        total_apis = len(self.df["url"].unique())

        # Generate plots
        response_time_plot = self._create_response_time_plot()
        error_rate_plot = self._create_error_rate_plot()
        slowest_apis_plot = self._create_slowest_apis_plot()

        # Load template from file and render
        with open("templates/report_template.html", "r") as f:
            template = Template(f.read())

        return template.render(
            virtual_users=len(set(self.df.index)),
            ramp_up_time=5,  # This should be passed to the class
            total_apis=total_apis,
            avg_response_time=avg_response_time,
            total_requests=total_requests,
            error_rate=error_rate,
            response_time_plot=response_time_plot,
            error_rate_plot=error_rate_plot,
            slowest_apis_plot=slowest_apis_plot,
            api_metrics=metrics,
            error_analysis=error_analysis,
            slowest_apis=slowest_apis
        )

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
            paper_bgcolor="white"
        )
        return fig.to_html(full_html=False)

    def _create_error_rate_plot(self):
        """Creates a bar chart of error rates by API"""
        error_rates = (self.df[self.df["status_code"] >= 400]
                      .groupby("url")
                      .size()
                      .divide(self.df.groupby("url").size())
                      .sort_values(ascending=True)
                      .tail(5))  # Show top 5 APIs with highest error rates

        fig = px.bar(
            x=error_rates.values * 100,  # Convert to percentage
            y=error_rates.index,
            orientation="h",
            title="Error Rates by API",
            labels={"x": "Error Rate (%)", "y": "API Endpoint"}
        )
        fig.update_traces(marker_color="#FF6B6B", marker_line_color="#E74C3C")
        return fig.to_html(full_html=False)

    def _create_slowest_apis_plot(self):
        """Creates a bar chart of slowest APIs"""
        avg_times = (self.df.groupby("url")["response_time"]
                    .mean()
                    .sort_values(ascending=True)
                    .tail(5))  # Show top 5 slowest APIs

        fig = px.bar(
            x=avg_times.values,
            y=avg_times.index,
            orientation="h",
            title="Top 5 Slowest APIs",
            labels={"x": "Average Response Time (ms)", "y": "API Endpoint"}
        )
        fig.update_traces(marker_color="#2E86C1", marker_line_color="#2874A6")
        return fig.to_html(full_html=False)

    def _calculate_api_metrics(self):
        """Calculates comprehensive metrics for each API"""
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
        metrics["throughput"] = metrics[("response_time", "count")] / (len(set(self.df.index)) * 5)  # requests per second

        # Flatten column names
        metrics.columns = ["avg_response_time", "min_time", "max_time", "request_count", 
                         "error_rate", "p90", "p95", "p99", "throughput"]
        return metrics.reset_index()

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