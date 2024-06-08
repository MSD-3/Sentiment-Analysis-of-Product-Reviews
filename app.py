from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
import requests
from flask import Flask, render_template, request
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import nltk
from string import punctuation
import re
from nltk.corpus import stopwords
import csv
import math

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('front/main.html')

@app.route('/feedback')
def feedback():
    return render_template('front/feedback.html')

@app.route('/', methods=['POST'])
def submit():
    reviews_url = request.form['product-name']

    # Header to set the requests as a browser requests
    headers = {
        'authority': 'www.amazon.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'en-US,en;q=0.9,bn;q=0.8',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
    }

    # URL of The amazon Review page

    # Define Page No
    len_page = 12

    # <font color="red">Functions</font>

    # Extra Data as Html object from amazon Review page

    def reviewsHtml(url, len_page):

        # Empty List define to store all pages html data
        soups = []

        # Loop for gather all 3000 reviews from 300 pages via range
        for page_no in range(1, len_page + 1):

            # parameter set as page no to the requests body
            params = {
                'ie': 'UTF8',
                'reviewerType': 'all_reviews',
                'filterByStar': 'critical',
                'pageNumber': page_no,
            }

            # Request make for each page
            response = requests.get(url, headers=headers)

            # Save Html object by using BeautifulSoup4 and lxml parser
            soup = BeautifulSoup(response.text, 'lxml')

            # Add single Html page data in master soups list
            soups.append(soup)

        return soups

    # Grab Reviews name, description, date, stars, title from HTML

    def getReviews(html_data):

        # Create Empty list to Hold all data
        data_dicts = []

        # Select all Reviews BOX html using css selector
        boxes = html_data.select('div[data-hook="review"]')

        # Iterate all Reviews BOX
        for box in boxes:

            # Select Name using css selector and cleaning text using strip()
            # If Value is empty define value with 'N/A' for all.
            try:
                name = box.select_one('[class="a-profile-name"]').text.strip()
            except Exception as e:
                name = 'N/A'

            try:
                stars = box.select_one(
                    '[data-hook="review-star-rating"]').text.strip().split(' out')[0]
            except Exception as e:
                stars = 'N/A'

            try:
                title = box.select_one(
                    '[data-hook="review-title"]').text.strip()
            except Exception as e:
                title = 'N/A'

            try:
                # Convert date str to dd/mm/yyy format
                datetime_str = box.select_one(
                    '[data-hook="review-date"]').text.strip().split(' on ')[-1]
                date = datetime.strptime(
                    datetime_str, '%B %d, %Y').strftime("%d/%m/%Y")
            except Exception as e:
                date = 'N/A'

            try:
                description = box.select_one(
                    '[data-hook="review-body"]').text.strip()
            except Exception as e:
                description = 'N/A'

            # create Dictionary with al review data
            data_dict = {
                'Name': name,
                'Stars': stars,
                'Title': title,
                'Date': date,
                'Description': description
            }

            # Add Dictionary in master empty List
            data_dicts.append(data_dict)

        return data_dicts

    # <font color="red">Data Process</font>

    # Grab all HTML
    html_datas = reviewsHtml(reviews_url, len_page)

    # Empty List to Hold all reviews data
    reviews = []

    # Iterate all Html page
    for html_data in html_datas:

        # Grab review data
        review = getReviews(html_data)

        # add review data in reviews empty list
        reviews += review

    # Create a dataframe with reviews Data
    df_reviews = pd.DataFrame(reviews)

    print(df_reviews)

    # Save data
    df_reviews.to_csv('reviews.csv', index=False)

    nltk.download('stopwords')

    set(stopwords.words('english'))
    stop_words = stopwords.words('english')
    compound = 0
    pos = 0
    neg = 0
    neu = 0
    count = 0
    with open('reviews.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)
        for line in csv_reader:
            # convert to lowercase
            text1 = line[4].lower()

            text_final = ''.join(c for c in text1 if not c.isdigit())

            # remove stopwords
            processed_doc1 = ' '.join(
                [word for word in text_final.split() if word not in stop_words])

            sa = SentimentIntensityAnalyzer()
            dd = sa.polarity_scores(text=processed_doc1)
            compound += round((1 + dd['compound'])/2, 2)
            pos += dd['pos']
            neg += dd['neg']
            neu += dd['neu']
            count += 1

        pos /= count
        neg /= count
        neu /= count
        compound /= count
        pos=math.ceil(pos*10000)/100
        neg=math.ceil(neg*10000)/100
        neu=math.ceil(neu*10000)/100
        compound=math.ceil(compound*10000)/100
        print("Positive : ", pos)
        print("Negative : ", neg)
        print("Neutral : ", neu)
        print("Compound", compound)
    return render_template('front/final_page.html', result=compound , pos=pos , neg=neg, neu=neu)
