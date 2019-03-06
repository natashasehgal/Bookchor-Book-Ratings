import re
import sys
import pandas as pd

import requests, urllib.parse
from requests_html import HTMLSession
from bs4 import BeautifulSoup

bookChorLink = "http://www.bookchor.com/Featured-Books"
goodReadsLink = "https://www.goodreads.com/search?{}"
dfFile = "./BCFeaturedBooks.pkl"

columns = ['Title','Author','AvgRating','NumberOfRatings','BCTitle','BCLink','GRLink']
pd.set_option('display.max_columns', 500)
df = pd.DataFrame(columns=columns)

def getRatings(ratings):
    ratings = ratings.split(' ')
    avgRatingFound, ratingFound = False,False
    avgRating, rating = 0,0
    for r in ratings:
        r  = r.replace(",","")
        try:
            if avgRatingFound==False and float(r):
                avgRatingFound = True
                avgRating = float(r)
            elif ratingFound==False and int(r):
                ratingFound = True
                rating = int(r)
        except ValueError:
            continue
        if avgRatingFound==True and ratingFound==True:
            break
    return avgRating, rating

def getTitle(link):
    titleLink = link[link.rfind('/')+1:] #get title for query
    title = ' '.join(titleLink.split('-'))
    title = rx.sub(' ',title)
    title = re.sub(' {2,}', ' ', title)
    return title

if __name__== "__main__":
    r = requests.get(bookChorLink)
    soup = BeautifulSoup(r.text, "lxml") #get request data

    rx = re.compile('\@|\,|\.|\!|\?|\:|\;|\-|\]|\(|\)|\[|\]|\{|\}')

    bcLinks = soup.select('div.product-item > h3 > a')
    bcLinks = [link['href'] for link in bcLinks]

    for link in bcLinks:
        session = HTMLSession()
        bcTitle = getTitle(link)
        query = {'q':bcTitle}
        bookLink = goodReadsLink.format(urllib.parse.urlencode(query))
        r = session.get(bookLink)
        r.html.render()
        soup = BeautifulSoup(r.content,"lxml")
        book = soup.find('a',{'class':'bookTitle'}) #get first book title
        if book is None:
            print("Not Found! Book: ", bcTitle)
            continue
        print("Processing Book: ", bcTitle)
        author = soup.find('a',{'class':'authorName'}) #get first book author
        ratingData = soup.find('span',{'class':'minirating'})
        bookName = book.find('span').string
        authorName = author.find('span').string
        ratings = ratingData.text # get book rating
        avgRating, rating = getRatings(ratings)

        row = [bookName,authorName,avgRating,rating,bcTitle,link,bookLink]
        df.loc[len(df)] = row

    print(df.shape[0])
    df.sort_values(['AvgRating','NumberOfRatings'],inplace=True,ascending=False)
    print(df[['Title','Author','AvgRating','NumberOfRatings']].head(20))

df.to_csv('BookChorFeaturedRatings.csv')
