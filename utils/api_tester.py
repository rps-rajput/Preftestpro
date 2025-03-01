import requests
import time
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import numpy as np

class APITester:
    def __init__(self, apis, virtual_users, ramp_up_time):
        self.apis = apis
        self.virtual_users = virtual_users
        self.ramp_up_time = ramp_up_time
        
    def make_request(self, api):
        start_time = time.time()
        try:
            response = requests.request(
                method=api["method"],
                url=api["url"],
                headers=api["headers"],
                json=api.get("body", None),
                timeout=30
            )
            
            return {
                "url": api["url"],
                "method": api["method"],
                "status_code": response.status_code,
                "response_time": (time.time() - start_time) * 1000,  # Convert to ms
                "error_message": response.text if response.status_code >= 400 else None
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "url": api["url"],
                "method": api["method"],
                "status_code": 500,
                "response_time": (time.time() - start_time) * 1000,
                "error_message": str(e)
            }
    
    def run_test(self):
        results = []
        delay_between_users = self.ramp_up_time / self.virtual_users
        
        def user_session(user_id):
            time.sleep(delay_between_users * user_id)
            user_results = []
            for api in self.apis:
                result = self.make_request(api)
                user_results.append(result)
            return user_results
        
        # Use ThreadPoolExecutor for concurrent requests
        with ThreadPoolExecutor(max_workers=self.virtual_users) as executor:
            all_results = executor.map(user_session, range(self.virtual_users))
            
        # Flatten results
        for user_results in all_results:
            results.extend(user_results)
            
        return results
