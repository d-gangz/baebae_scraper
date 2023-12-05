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
1. User serper to find relevant links about the company
2. From the links, get the text from the html content
3. Pass in to the LLM (OpenAI) to summarise it