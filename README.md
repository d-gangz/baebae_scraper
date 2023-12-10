#Chinese website webscraper

#Description

#Features

#How to use

#Technologies

#Collaborators

#License

#Key Learnings

##Thinking steps
1. Find the correct webpages with the news. It is too difficult to scrape from the homepage. Probably the results page is better
2. From the results page, filter out today's articles (using the date)

##Dealing with JavaScript-Loaded Content
Some web pages dynamically load content using JavaScript. Traditional scraping methods might not work here. Tools like Selenium or requests-html can render JavaScript and then scrape the content.

##4Dec - Shift in approach
If we consider the user goals, their main goal is to find relevant information about their list of clients. Perhaps, connecting to a google search (Serper.dev) might be better.

###Approach
Note that in webdev, it is important to break things down the smaller steps to work on. So now just work based on one company first.
- User serper to find relevant links about the company
- From the links, get the text from the html content using browserless. It is able to get javascript loaded content so I don't need to do the selenium stuff. Not bad.
- Pass in to the LLM (OpenAI) to summarise it

##7 Dec - Got my first scraping result
Did the approach of breaking up the html content into manageable bits so that the LLM can summarise the chunks and then combined the summarised chunks into a bigger text for it to summarise. The code worked but the results are not great. Need to figure out a better way. I've learnt that the REPR method for the OpenAI API returns a class instance. To get access to the content, need to do a variable.content to access it.

Oh yes! Got the summarise scraping to work. The key is to extract mainly the P,H1 and H2 and css selectors which is where the main content lie. The others are not important information like headers footers etc.

##9 Dec - using companies provided to find information
Now we are one step closer. Now is to try using real companies to find information and scrape

##10 Dec - successfully summarise 5 links from one company
Managed to get 3 companies, obtain top 5 search results of each and then scrape the article links and summarise them. The output was title, summary and links. Not bad as it worked.