import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from jinja2 import Template
import numpy as np

class ReportGenerator:
    def __init__(self, results):
        self.results = results
        self.df = pd.DataFrame(results)
        
    def generate_html_report(self):
        # Calculate metrics
        total_requests = len(self.results)
        avg_response_time = self.df["response_time"].mean()
        error_rate = (self.df["status_code"] >= 400).mean() * 100
        
        # Generate plots
        response_time_plot = self._create_response_time_plot()
        error_rate_plot = self._create_error_rate_plot()
        slowest_apis_plot = self._create_slowest_apis_plot()
        
        # Prepare detailed tables
        api_metrics = self._calculate_api_metrics()
        error_analysis = self._analyze_errors()
        slowest_apis = self._analyze_slowest_apis()
        
        # Load and render template
        template = Template('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Performance Test Report</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    padding: 20px;
                }
                .report-title {
                    color: #2C3E50;
                    text-align: center;
                    padding: 20px 0;
                    border-bottom: 2px solid #3498DB;
                    margin-bottom: 30px;
                }
                .test-config {
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }
                .metric-container {
                    display: flex;
                    justify-content: space-between;
                    margin: 20px 0;
                    flex-wrap: wrap;
                }
                .metric-box {
                    background: #f5f5f5;
                    padding: 15px;
                    border-radius: 5px;
                    text-align: center;
                    flex: 1;
                    margin: 5px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }
                th, td {
                    padding: 8px;
                    text-align: left;
                    border: 1px solid #ddd;
                }
                th {
                    background-color: #f8f9fa;
                }
            </style>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        </head>
        <body>
            <h1 class="report-title">Performance Test Report</h1>
            
            <div class="test-config">
                <h2>Test Configuration</h2>
                <p>Virtual Users: {{ virtual_users }}</p>
                <p>Total Requests: {{ total_requests }}</p>
            </div>
            
            <div class="metric-container">
                <div class="metric-box">
                    <h3>Average Response Time</h3>
                    <p>{{ "%.2f"|format(avg_response_time) }} ms</p>
                </div>
                <div class="metric-box">
                    <h3>Error Rate</h3>
                    <p>{{ "%.2f"|format(error_rate) }}%</p>
                </div>
            </div>
            
            {{ response_time_plot | safe }}
            {{ error_rate_plot | safe }}
            {{ slowest_apis_plot | safe }}
            
            <h2>API Metrics</h2>
            {{ api_metrics.to_html() | safe }}
            
            <h2>Error Analysis</h2>
            {{ error_analysis.to_html() | safe }}
            
            <h2>Slowest APIs</h2>
            {{ slowest_apis.to_html() | safe }}
            
        </body>
        </html>
        ''')
        
        return template.render(
            virtual_users=len(set(self.df.index)),
            total_requests=total_requests,
            avg_response_time=avg_response_time,
            error_rate=error_rate,
            response_time_plot=response_time_plot,
            error_rate_plot=error_rate_plot,
            slowest_apis_plot=slowest_apis_plot,
            api_metrics=api_metrics,
            error_analysis=error_analysis,
            slowest_apis=slowest_apis
        )
    
    def _create_response_time_plot(self):
        fig = px.histogram(
            self.df,
            x="response_time",
            nbins=50,
            title="Response Time Distribution"
        )
        return fig.to_html(full_html=False)
    
    def _create_error_rate_plot(self):
        error_rates = (self.df[self.df["status_code"] >= 400]
                      .groupby("url")
                      .size()
                      .divide(self.df.groupby("url").size()))
        
        fig = px.bar(
            x=error_rates.index,
            y=error_rates.values,
            title="Error Rates by API"
        )
        return fig.to_html(full_html=False)
    
    def _create_slowest_apis_plot(self):
        avg_times = self.df.groupby("url")["response_time"].mean().sort_values(ascending=False).head(5)
        
        fig = px.bar(
            x=avg_times.index,
            y=avg_times.values,
            title="Top 5 Slowest APIs"
        )
        return fig.to_html(full_html=False)
    
    def _calculate_api_metrics(self):
        metrics = self.df.groupby("url").agg({
            "response_time": ["mean", "min", "max", "count"],
            "status_code": lambda x: (x >= 400).mean() * 100
        }).round(2)
        
        metrics.columns = ["Avg Response Time", "Min Time", "Max Time", "Request Count", "Error Rate %"]
        return metrics.reset_index()
    
    def _analyze_errors(self):
        return self.df[self.df["status_code"] >= 400][["url", "status_code", "error_message"]]
    
    def _analyze_slowest_apis(self):
        return (self.df.groupby("url")["response_time"]
                .mean()
                .sort_values(ascending=False)
                .head(5)
                .reset_index())
