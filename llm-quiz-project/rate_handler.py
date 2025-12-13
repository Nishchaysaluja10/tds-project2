
import json
import math

def calculate_rate_limit_answer(json_content, email):
    """
    Calculate minimal whole minutes to fetch all pages respecting limits.
    Formula: respecting per_minute and per_hour.
    Then add offset = len(email) % 3.
    """
    try:
        data = json.loads(json_content)
        pages = data.get('pages', 0)
        per_minute = data.get('per_minute', 1)
        per_hour = data.get('per_hour', 1)
        
        # Logic:
        # We want to fetch 'pages'.
        # Constraint 1: per_minute.
        # Constraint 2: per_hour.
        
        # Check if hourly limit is the bottleneck
        # Max capacity in 1 hour if limited only by per_minute:
        capacity_1h_minObj = per_minute * 60
        
        total_time_minutes = 0.0
        
        remaining = pages
        
        # Iterate hours? Or do calculated approach.
        # Optimization:
        # If per_hour < capacity_1h_minObj, we are throttled by hour.
        
        # We fill the 'hourly bucket' first.
        # In first hour (T=0 to T=60), we can do min(per_hour, capacity_1h_minObj).
        # Actually, let's simulate or calculate.
        
        # First hour:
        # Can we do all 'remaining'?
        if remaining <= per_hour:
             # We can do all in this hour (assuming min limit allows)
             # Time taken = remaining / per_minute
             total_time_minutes += remaining / per_minute
             remaining = 0
        else:
             # We do 'per_hour' requests (capped by hourly limit)
             # Time taken is 60 minutes (we must wait for the hour to clear)
             # Wait, does it take 60 minutes of WORK? No.
             # It takes `per_hour / per_minute` to SEND them.
             # Then we IDLE until T=60.
             # So effective time cost is 60 minutes if we adhere to "minimal whole minutes" duration?
             # Yes. If we cross the hour boundary, T > 60.
             
             # Calculate full hours needed
             full_hours = 0
             while remaining > per_hour:
                 remaining -= per_hour
                 full_hours += 1
            
             # For each full hour, we define time as 60 minutes?
             # Yes, because we can't start the next batch until hour resets.
             total_time_minutes += full_hours * 60
             
             # Now process the remaining (which is <= per_hour)
             # Time = remaining / per_minute
             total_time_minutes += remaining / per_minute
             
        # Ceiling to whole minutes
        final_minutes = math.ceil(total_time_minutes)
        
        # Offset
        offset = len(email) % 3
        
        result = final_minutes + offset
        
        print(f"⏱️ Rate Calc: {pages} pages. Limits: {per_minute}/min, {per_hour}/hr. Time: {total_time_minutes:.2f} -> {final_minutes}. Offset: {offset}. Ans: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Error parsing rate limit: {e}")
        return 0
