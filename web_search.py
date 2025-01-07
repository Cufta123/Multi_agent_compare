import os
import requests
from dotenv import load_dotenv

load_dotenv()

def search_the_web(query):
    subscription_key = os.environ['BING_API_KEY']
    endpoint = "https://api.bing.microsoft.com/v7.0/search"
    mkt = 'en-US'
    params = {'q': query, 'mkt': mkt}
    headers = {'Ocp-Apim-Subscription-Key': subscription_key}

    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as ex:
        raise ex

def extract_relevant_info(search_results):
    extracted = []
    for result in search_results.get('webPages', {}).get('value', []):
        extracted.append(f"{result['name']}: {result['snippet']}")
    return extracted[:5]  # Limit to top 5 results