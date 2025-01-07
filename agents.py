import os
import requests
from pprint import pprint
from autogen import GroupChat
from autogen import GroupChatManager
from autogen import ConversableAgent
from dotenv import load_dotenv
from autogen.agentchat.contrib.web_surfer import WebSurferAgent
from autogen.browser_utils import RequestsMarkdownBrowser
import sys

load_dotenv()

class CustomAgent(ConversableAgent):
    def search_the_web(self, query):
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

def initiate_chat(self, group_chat_manager, message, summary_method, search_web=False):
    if search_web:
        search_results = self.search_the_web(message)
        pprint(search_results)  # Display search results or process further

    # Define the message and silence setting
    msg2send = "Here are the search results."
    silent = False
    
    # Use GroupChatManager to send the message
    group_chat_manager.send_message(msg2send, sender=self, silent=silent)
    
def summarize_messages(messages, llm_client):
    prompt = "Summarize the following messages while retaining important details:\n\n" + "\n".join(messages)
    response = llm_client.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response['choices'][0]['message']['content']

MAX_MESSAGES = 20  # Keep the last 20 messages

def trim_messages(messages):
    if len(messages) > MAX_MESSAGES:
        return messages[-MAX_MESSAGES:]  # Keep only the last 20 messages
    return messages

def extract_relevant_info(search_results):
    extracted = []
    for result in search_results.get('webPages', {}).get('value', []):
        extracted.append(f"{result['name']}: {result['snippet']}")
    return extracted[:5]  # Limit to top 5 results

browser = {"viewport_size": 4096, "bing_api_key": os.environ["BING_API_KEY"]}

human_proxy = ConversableAgent(
    name="Human_Proxy",
    system_message="You are the human proxy, you will be the one to communicate with the user.",
    llm_config=False,
    human_input_mode="ALWAYS",
)    
web_surfer_agent = WebSurferAgent(
    name="Web_Surfer_Agent",
    system_message="You search for the best products based on user preferences, you first search all of the answers on the web.",
    llm_config={"config_list": [{"model": "gpt-4", "api_key": os.environ["OPENAI_API_KEY"]}]},
    browser=browser,
)

user_agent = CustomAgent(
    name="User_Agent",
    system_message="You communicate with user and give him result one at the time.",
    llm_config={"config_list": [{"model": "gpt-4", "api_key": os.environ["OPENAI_API_KEY"]}]},
    human_input_mode="NEVER",
)

recomendation_agent = CustomAgent(
    name="Recomendation_Agent",
    system_message="You search for the best products based on user preferences",
    llm_config={"config_list": [{"model": "gpt-4", "api_key": os.environ["OPENAI_API_KEY"]}]},
    human_input_mode="NEVER",
)

search_agent = CustomAgent(
    name="Search_Agent",
    system_message="You search for products based on user's query",
    llm_config={"config_list": [{"model": "gpt-4", "api_key": os.environ["OPENAI_API_KEY"]}]},
    human_input_mode="NEVER",
)

comparasion_agent = CustomAgent(
    name="Comparasion_Agent",
    system_message="You compare products based on user's query",
    llm_config={"config_list": [{"model": "gpt-4", "api_key": os.environ["OPENAI_API_KEY"]}]},
    human_input_mode="NEVER",
)

user_agent.description = "You communicate with user and give him result one at the time."
web_surfer_agent.description="You search for the best products based on user preferences"
recomendation_agent.description = "Recommend products based on user's preferences and search results"
search_agent.description = "Search for products based on user's query and search results"
comparasion_agent.description = "Compare products based on user's query and search results"

group_chat = GroupChat(
    agents=[user_agent, web_surfer_agent,recomendation_agent, search_agent, comparasion_agent],
    messages=[],
    max_round=6,
)

group_chat_manager = GroupChatManager(
    groupchat=group_chat,
    llm_config={"config_list": [{"model": "gpt-4", "api_key": os.environ["OPENAI_API_KEY"]}]},
)

raw_results = user_agent.search_the_web("best smartphone with good camera and battery life that is under 300 dollars")
search_results = extract_relevant_info(raw_results)

chat_result = user_agent.initiate_chat(
    group_chat_manager,
    message=f"I found these results from the web: {search_results}",
    summary_method="reflection_with_llm"
)