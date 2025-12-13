
import pandas as pd
import json
from io import StringIO

def process_orders_csv(content_bytes):
    try:
        csv_text = content_bytes.decode('utf-8')
        df = pd.read_csv(StringIO(csv_text))
        
        # Calculate total sales per customer
        # Check column names
        if 'amount' in df.columns:
            total_col = 'amount'
        elif 'total' in df.columns:
            total_col = 'total'
        else:
             # Fallback to looking for numeric column
            total_col = df.select_dtypes(include=['number']).columns[0]
            
        res = df.groupby('customer_id')[total_col].sum().reset_index()
        res.rename(columns={total_col: 'total'}, inplace=True)
        
        # Sort by total desc and take top 3
        res = res.sort_values(by='total', ascending=False).head(3)
        
        return json.dumps(res.to_dict(orient='records'))
    except Exception as e:
        print(f"❌ Error processing orders: {str(e)}")
        return json.dumps([])
