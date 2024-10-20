from flask import Flask, render_template, request
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64
from twilio.rest import Client  # Twilio import

# Create Flask app
app = Flask(__name__)

# Load the Excel file
df = pd.read_excel('updata12.xlsx')  # Make sure the file path is correct

# Convert 'Expiry_date' column to datetime
df['Expiry_date'] = pd.to_datetime(df['Expiry_date'], format='%d-%m-%Y', errors='coerce')

# Calculate 'days_to_expiry' as the difference between today's date and the expiry date
today = datetime.now()
df['days_to_expiry'] = (df['Expiry_date'] - today).dt.days

# Twilio credentials
account_sid = 'AC851e4b1637354c252e5b65ec515c5e93'
auth_token = 'ea06e18f3a6dc24302b160bb508ff3ff'

client = Client(account_sid, auth_token)

# Function to send SMS
def send_sms(to_number, message_body):
    message = client.messages.create(
        body=message_body,
        from_='+19143686830',  # Twilio phone number
        to=to_number  # Recipient phone number
    )
    return message.sid

# Function to plot stock levels and return image
def plot_stock_levels():
    items = df['Item']
    quantities = df['Quantity']
    thresholds = df['Threshold']
    
    fig, ax = plt.subplots()
    ax.set_ylim(0, max(quantities) + 10)
    ax.set_title("Item Quantities with Threshold Alert")
    ax.set_xlabel("Items")
    ax.set_ylabel("Quantity")

    # Plot quantities and threshold
    ax.plot(items, quantities, color='blue', marker='o', linestyle='-', label='Quantity', markersize=10)
    ax.plot(items, thresholds, color='red', linestyle='--', label='Threshold')

    # Highlight low stock items
    for i, (quantity, threshold) in enumerate(zip(quantities, thresholds)):
        if quantity < threshold:
            ax.scatter(items[i], quantity, color='red', s=100, zorder=5)
        else:
            ax.scatter(items[i], quantity, color='blue', s=100, zorder=5)

    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    
    # Save the plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# Function to check stock and return items below threshold
def check_stock():
    low_stock_items = df[df['Quantity'] < df['Threshold']]
    return low_stock_items[['Item', 'Quantity', 'Threshold', 'Supplier']]

# Function to plot expiry dates and return image
def plot_expiry():
    expiring_soon = df[df['days_to_expiry'] < 9]

    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['days_to_expiry'], marker='o', linestyle='-', color='blue', label='Days to Expiry')

    # Highlight expiring soon items
    plt.scatter(expiring_soon.index, expiring_soon['days_to_expiry'], color='red', label='Expiring Soon (within 8 days)', zorder=5)

    # Add a threshold line at 8 days
    plt.axhline(y=8, color='green', linestyle='--', label='8 Days Threshold')

    plt.title('Products Days to Expiry', fontsize=16)
    plt.xlabel('Product Index', fontsize=8)
    plt.ylabel('Days to Expiry', fontsize=8)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    
    # Save the plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# Function to check expiring items
def check_expiry():
    expiring_soon = df[df['days_to_expiry'] < 9]
    return expiring_soon[['Item', 'Expiry_date', 'days_to_expiry']]

# Function to check stock and notify via SMS
def check_stock_and_notify(df):
    low_stock_items = df[df['Quantity'] < df['Threshold']]
    notifications = []

    # Prepare notifications
    if not low_stock_items.empty:
        for index, row in low_stock_items.iterrows():
            notification = {
                'Item': row['Item'],
                'Supplier': row['Supplier'],
            }
            message_body = f"Low stock alert: {row['Item']} is below the threshold. Please restock!"
            send_sms('+918838404033', message_body)  # Replace with recipient's number
            notifications.append(notification)
    return notifications

# Function to check for expiring items and notify via SMS
def check_expiry_and_notify():
    expiring_soon = df[df['days_to_expiry'] < 9]
    notifications = []
    for index, row in expiring_soon.iterrows():
        notification = {
            'Item': row['Item'],
            'Expiry_date': row['Expiry_date'].strftime('%d-%m-%Y %H:%M'),  # Format date
            'Days_to_Expiry': row['days_to_expiry'],
        }
        message_body = f"Expiry alert: {row['Item']} will expire in {row['days_to_expiry']} days!"
        send_sms('+918838404033', message_body)  # Replace with recipient's number
        notifications.append(notification)
    return notifications

# Routes for each index page
@app.route('/')
def home():
    return render_template('index1.html')  # Home page

@app.route('/index2')
def index2():
    return render_template('index2.html')

@app.route('/index3')
def index3():
    return render_template('index3.html')

@app.route('/index4')
def index4():
    stock_data = check_stock()
    stock_plot = plot_stock_levels()
    return render_template('index4.html', stock_data=stock_data.to_html(), stock_plot=stock_plot)

@app.route('/index5')
def index5():
    expiry_data = check_expiry()
    expiry_plot = plot_expiry()
    return render_template('index5.html', expiry_data=expiry_data.to_html(), expiry_plot=expiry_plot)

@app.route('/index6')
def index6():
    return render_template('index6.html')

@app.route('/index7')
def index7():
    notifications = check_stock_and_notify(df)  # Pass df directly to the function
    return render_template('index7.html', notifications=notifications)

@app.route('/index8')
def index8():
    # Get spoilage notifications
    expiry_notifications = check_expiry_and_notify()
    return render_template('index8.html', notifications=expiry_notifications)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
