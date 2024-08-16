import requests
from bs4 import BeautifulSoup
import pandas as pd
# Base URL without the suffix
base_url = 'https://bitinfocharts.com/top-100-richest-bitcoin-addresses'

# Number of pages to loop through (including the one without a suffix)
num_pages = 1

# Class prefix to target
class_prefix = 'table table-striped'

# List to hold all Bitcoin addresses and balances from all tables across all pages
all_bitcoin_data = []

# Loop through the pages
for i in range(1, num_pages + 1):

    print(f"Extracting data from Page {i}...")
    # Construct the URL for each page
    if i == 1:
        url = f'{base_url}.html'
    else:
        url = f'{base_url}-{i}.html'
    
    # Send a GET request to the website
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all tables with classes that start with the specified prefix
        tables = soup.find_all('table', class_=lambda x: x and x.startswith(class_prefix))

        # Loop through each table that matches the class prefix
        for table_index, table in enumerate(tables, start=1):
            # Extract all rows from the table
            rows = table.find_all('tr')

            # Loop through the rows and extract Bitcoin addresses and balances
            for row in rows[1:]:  # Skip the header row
                cols = row.find_all('td')
                if len(cols) > 1:  # Ensure the row has the expected number of columns
                    # Try to extract the full Bitcoin address
                    address_tag = cols[1].find('a')
                    address = address_tag['href'].split('/')[-1].strip()  # Extract from href if needed

                    # Alternatively, get the full text from title attribute if available
                    if 'title' in address_tag.attrs:
                        address = address_tag['title'].strip()
                    else:
                        address = address_tag.text.strip()

                    # Manually strip unwanted characters if they appear
                    if address.endswith('..'):
                        address = address[:-2]  # Remove the last two dots
                    elif '..' in address:
                        address = address.replace('..', '')  # Remove any instances of two dots in the middle

                    balance_text = cols[2].text.strip()  # Assuming the third column contains the balance
                    Ins = cols[6].text.strip()
                    Outs = cols[9].text.strip()
                    # Extract just the BTC amount from the balance_text
                    btc_amount = float(balance_text.split(' ')[0].replace(',', ''))

                    all_bitcoin_data.append((address, btc_amount, Ins, Outs))
    else:
        print(f"Failed to retrieve the page: {url}. Status code: {response.status_code}")

# Now 'all_bitcoin_data' contains the full addresses without the '..' issue.

# Convert the list of tuples to a pandas DataFrame
df = pd.DataFrame(all_bitcoin_data, columns=['Address', 'Balance (BTC)','Ins','Outs'])
df['Outs'] = df['Outs'].replace("", 0)
df['Outs'] = pd.to_numeric(df['Outs'], errors='coerce')
df['Ins'] = pd.to_numeric(df['Ins'], errors='coerce')
df['Transactions'] = df['Ins'] + df['Outs']
df_filtered = df[df['Transactions'] >= 20]
# Display the DataFrame
print(df)
# Optionally, save the DataFrame to a CSV file
df_filtered.to_csv('bitcoin_addresses.csv', index=False)

# print(f"\nData saved to 'bitcoin_addresses.csv'. Total records extracted: {len(df)}")
