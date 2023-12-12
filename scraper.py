from dotenv import load_dotenv
import os
import requests
import json
from bs4 import BeautifulSoup
from openai import OpenAI
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()  # This loads the .env file

# defaults to getting the key using os.environ.get("OPENAI_API_KEY")
client = OpenAI()

# Access your API keys
serper_api_key = os.getenv('SERPER_API_KEY')
browserless_api_key = os.getenv("BROWSERLESS_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Access my email password for the email service
email_password = os.getenv('EMAIL_PASSWORD')

## 1. Tool for search using Serper and returns top 3 results

def search(query):

    url = "https://google.serper.dev/search"

    # this config only returns the 1st page of google results (10 results)
    payload = json.dumps({
    "q": query
    })
    headers = {
    'X-API-KEY': serper_api_key,
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    # Convert results into a JSON string
    response_results = response.text
    
    # Converts JSON to a dictionary to access the values using appropriate keys
    parsed_json = json.loads(response_results)

    # Access the organic search results
    organic_results = parsed_json['organic']

    # The values in the "organic" key is a list of dictionaries. So this can obtain the top 5
    top_5_results = organic_results[:5]

    return top_5_results

'''
## Testing out to get the links etc

# Note to use this format for the queries to get the organic results
bullish_crypto = search("bullish crypto company news -site:bullish.com")

#print out the 1st 5 results in proper formatting
for item in bullish_crypto:
    title = item["title"]
    link = item["link"]
    snippet = item["snippet"]
    date = item.get("date", "No date available")
    print(
        f"{title}\n{link}\n{snippet}\n{date}\n"
    )
'''
    
## 2. Tool for scraping using browserless

def scrape_site(url):
    # print("scraping website")
    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json'
    }

    # Define data to be sent in the request. Getting <p>, <h1> and <h2> is sufficient to get most of the article text
    data = {
        'url': url,
        'elements': [
            {'selector': 'h1'},  # Selects all <h1> tags
            {'selector': 'h2'},  # Selects all <h2> tags
            {'selector': 'p'}    # Selects all <p> tags
        ]
    }

    # Convert Python object to JSON string
    data_json = json.dumps(data)

    # Send the POST request
    post_url = f'https://chrome.browserless.io/scrape?token={browserless_api_key}'
    response = requests.post(post_url, headers=headers, data=data_json)

    # Check the response status code
    if response.status_code == 200:
        soup = BeautifulSoup(response.content,'html.parser')
        text = soup.get_text()
        # print('content:', text)

        return text
    else:
        print(f'HTTP request failed with status code {response.status_code}')
        print(f'Response body: {response.text}')

## 3. Using LLM to summarise and extract content

def summarise(text):
    
    completion = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are an expert researcher, skilled in extracting useful key insights for an institutional executive"},
        {"role": "user", "content": f"Read the following HTML content carefully. Identify and summarize only the main article, excluding any headers, footers, navigation menus, advertisements, or sidebar content. Focus on the core message or theme of the article and provide a detailed summary in English:\n{text}"}
    ]
    )

    return completion.choices[0].message

# Argument is the text extracted from html. Break up the main text into manageable chunks and combine them to a single list for the LLM to process
def chunk_string(text_result,chunk_size):
    chunk = []
    index = 0

    while index < len(text_result):
        chunk_text = text_result[index:index + chunk_size]
        chunk.append(chunk_text)

        index+=chunk_size

    return chunk

# Argument is a list of chunks. Parse through the chunks, summarise them and then combine the summary to summarise them all
def single_summary(chunk_list):
    total_summary = ""

    for text in chunk_list:
        summary_chunk = summarise(text) # Loop through text chunks and summarise them
        # Extract the content attribute from the ChatCompletionMessage object
        summary_text = summary_chunk.content
        total_summary += summary_text
    
    main_summary = summarise(total_summary)

    return main_summary

# Get summary of the results for a single search query. Argument is the search query and output is html content
def results_summary(query):
    results = search(query) # Get top 5 results

    #initialising list to hold the respective values
    titles = []
    links = []
    dates = []
    html_content = ""

    # Extract the values to put into above lists
    for item in results:
        title = item["title"]
        titles.append(title)
        link = item["link"]
        links.append(link)
        date = item.get("date", "No date available")
        dates.append(date)

    i = 0 # Iterator used to print out title for each one

    for link in links:
        # This returns you a JSON string of the website content in the html format
        site_content = scrape_site(link)
        if site_content is None:
            continue # Skip this link if scraping failed
        # To convert JSON string into a dictionary
        parsed_content = json.loads(site_content)
        
        # Initialize an empty string to store the combined content
        combined_content = ''

        # Loop through each item in 'data' (there were 3 'data values') and append the 'text' content from 'results'
        for item in parsed_content['data']:
            for result in item['results']:
                combined_content += result['text'] + ' '  # Add a space for readability

        # Breaking up the text result into chunks
        chunk_list = chunk_string(combined_content,3000)

        #Get the main summary
        output_summary = single_summary(chunk_list)

        # Extract the content attribute from the ChatCompletionMessage object
        article_summary = output_summary.content
        
        """
        print(titles[i])
        print(dates[i])
        print(article_summary)
        print(link)
        print("\n")
        """

        html_content += f'<a href="{link}"><h2>{titles[i]}</h2></a>\n<p>{dates[i]}</p>\n<p>{article_summary}</p>\n'
        
        i+=1 #increment by 1 with each loop to print out the titles and dates

    return html_content

# Format the company name and the scrapped content properly in html format in order to output in the email
def html_content(companies):
    html_content = ""
    for company,query in companies.items():
        html_content += f'<h1>{company}</h1>\n'
        html_content += results_summary(query)
    
    html = f'''\
    <html>
        <body>
            {html_content}
        <body>
    <html>
    '''
    return html


companies = {"Bullish":"bullish crypto company news -site:bullish.com",
             "Fore Elite":"Fore Elite company news -site:foreelite.com"} 

# print(html_content(companies))

def send_email():
    sender_email = "gangrdev@gmail.com"
    receiver_email = "limgangrui@gmail.com"
    password = email_password

    message = MIMEMultipart("alternative")
    message["Subject"] = "Latest news about your company"
    message["From"] = sender_email
    message["To"] = receiver_email

    html = html_content(companies)

    # Turn these into plain/html MIMEText objects
    part = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    message.attach(part)

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )
    return

send_email()

'''
companies = {"Bullish":"bullish crypto company news -site:bullish.com", 
             "Fore Elite":"Fore Elite company news -site:foreelite.com", 
             "Hashkey Exchange":"Hashkey Exchange crypto company news -site:hashkey.com"}
             
## Execute the functions to print out the summary of articles of the companies.
for key,value in companies.items():
    print(key)
    print("\n")
    results_summary(value)
'''

'''
## Function calls to get the output of a single summary

# This returns you a JSON string of the website content in the html format
site_content = scrape_site('https://cn.cryptonews.com/news/bitcoin-price-prediction-42k-breach-as-us-defense-eyes-btc.htm')

# To convert JSON string into a dictionary
parsed_content = json.loads(site_content)

# Initialize an empty string to store the combined content
combined_content = ''

# Loop through each item in 'data' (there were 3 'data values') and append the 'text' content from 'results'
for item in parsed_content['data']:
    for result in item['results']:
        combined_content += result['text'] + ' '  # Add a space for readability

# Breaking up the text result into chunks
chunk_list = chunk_string(combined_content,3000)

#Get the main summary
output_summary = webpage_summary(chunk_list)
print(output_summary)
'''