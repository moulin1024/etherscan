import requests
from datetime import datetime
import pandas as pd
import numpy as np

def get_bitcoin_balance(address):
    """
    Fetches the balance of a Bitcoin address using the Blockchain.com API.

    Parameters:
    address (str): The Bitcoin address to check.

    Returns:
    float: The balance of the Bitcoin address in BTC.
    """
    try:
        # Make an API request to Blockchain.com to get address balance
        url = f"https://blockchain.info/q/addressbalance/{address}"
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # The API returns the balance in satoshis (1 BTC = 100,000,000 satoshis)
            balance_in_satoshis = int(response.text)
            balance_in_btc = balance_in_satoshis / 1e8  # Convert satoshis to BTC
            return balance_in_btc
        else:
            return f"Error: Unable to fetch balance, status code {response.status_code}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"

def get_block_info(block_identifier):
    """
    Fetches detailed information of a Bitcoin block using Blockchain.com API.

    Parameters:
    block_identifier (str or int): The block hash or block height.

    Returns:
    dict: A dictionary containing block information, or an error message.
    """
    try:
        # Make an API request to Blockchain.com to get block details
        url = f"https://blockchain.info/rawblock/{block_identifier}"
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            block_info = response.json()  # Parse the JSON response
            return block_info
        else:
            return f"Error: Unable to fetch block info, status code {response.status_code}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"


def get_last_transactions(address, limit=10):
    """
    Fetches the last transactions of a Bitcoin address using the Blockchain.com API.

    Parameters:
    address (str): The Bitcoin address to check.
    limit (int): The number of recent transactions to retrieve (default is 10).

    Returns:
    list: A list of dictionaries containing transaction details.
    """
    try:
        # Make an API request to Blockchain.com to get address transactions
        url = f"https://blockchain.info/rawaddr/{address}?limit={limit}"
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            transactions = data.get('txs', [])
            return transactions[:limit]  # Return the last `limit` transactions
        else:
            return f"Error: Unable to fetch transactions, status code {response.status_code}"
    except Exception as e:
        return f"Exception occurred: {str(e)}"


def save_transactions_to_dataframe(transactions):
    """
    Saves a list of transactions into a Pandas DataFrame.

    Parameters:
    transactions (list): A list of transaction dictionaries.

    Returns:
    DataFrame: A Pandas DataFrame containing the transaction details.
    """
    transaction_data = []
    
    for tx in transactions:
        # Extract relevant information from each transaction
        tx_data = {
            # "Hash": tx['hash'],
            "Time (UTC)": datetime.utcfromtimestamp(tx['time']),
            "Inputs": len(tx['inputs']),
            "Outputs": len(tx['out']),
            "Total BTC Transacted": sum(out['value'] for out in tx['out']) / 1e8
        }
        transaction_data.append(tx_data)
    
    # Create a DataFrame from the transaction data
    df = pd.DataFrame(transaction_data)
    return df

def calculate_time_zone_probability(transaction_freq):
    """
    Calculate the posterior probability distribution of the user's time zone
    based on the provided hourly transaction frequency distribution.
    
    Parameters:
    transaction_freq (array-like): A list or array of length 24 representing the transaction frequency for each hour.
    
    Returns:
    np.array: A normalized array of posterior probabilities for each time zone (UTC-12 to UTC+12).
    """
    
    # Normalize the transaction frequency to get a probability distribution
    transaction_prob = np.array(transaction_freq) / np.sum(transaction_freq)

    # Define the expected "nighttime inactivity" distribution (e.g., less activity from 12 AM to 6 AM)
    nighttime_inactivity = np.zeros(24)
    nighttime_inactivity[0:6] = 1  # Assuming inactivity from 12 AM to 6 AM
    nighttime_inactivity /= np.sum(nighttime_inactivity)

    # Define time zones from UTC-12 to UTC+12
    time_zones = np.arange(-12, 13, 1)  # from UTC-12 to UTC+12

    # Initialize an array to store the likelihood for each time zone
    likelihoods = []

    # Compute the likelihood for each time zone
    for tz in time_zones:
        shifted_prob = np.roll(transaction_prob, tz)  # shift the distribution based on the time zone
        likelihood = np.sum(shifted_prob * nighttime_inactivity)  # dot product with assumed nighttime inactivity
        likelihoods.append(likelihood)

    # Convert likelihoods to posterior probabilities assuming uniform priors
    posterior_probabilities = np.array(likelihoods) / np.sum(likelihoods)
    
    return time_zones, posterior_probabilities

def guess_time_zones(address):
    # Example usage
    transactions = get_last_transactions(address, limit=100)
    # Save the transactions into a Pandas DataFrame
    df_transactions = save_transactions_to_dataframe(transactions)

    # Convert the timestamps to datetime objects
    datetimes = df_transactions["Time (UTC)"]

    # Extract the hour component from each datetime
    hours = [dt.hour + dt.minute / 60 for dt in datetimes]

    # Convert hours to a DataFrame
    df_hours = pd.DataFrame(hours, columns=['Hour'])

    transaction_freq, bin_edges = np.histogram(df_hours['Hour'], bins=24, range=(0, 24))

    time_zones, probabilities = calculate_time_zone_probability(transaction_freq)

    guessed_timezone = time_zones[np.argmax(probabilities)]
    return guessed_timezone

