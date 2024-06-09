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
import os
import chardet

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('front/main.html')

@app.route('/feedback')
def feedback():
    return render_template('front/feedback.html')

@app.route('/', methods=['POST'])
def submit():
    productUrl = request.form['product-name']
    # productUrl = "https://www.amazon.in/Daikin-Inverter-Copper-Filter-MTKM50U/dp/B09R4RYCJ4/ref=sr_1_3?_encoding=UTF8&content-id=amzn1.sym.58c90a12-100b-4a2f-8e15-7c06f1abe2be&dib=eyJ2IjoiMSJ9.LpujZ4uISPUK8sa_6yNGVRpIsC1NZyG20gIuO5aq54qul5ElUvKErFRUzRIoTOUX8mgWV8jIT67WbuR57cU0yUk78UfZ8uIDCYg860J0RX4s0ZN0Tz0x8YRjP_WHDMQoEhr3AnODQ8HpCODpRtthKR7gWrsoKC9ZXljp3LWdLIuELmslvhZA3TJl4b0R1Rk-TT_v6-YWX0I-zdmAhZfjivKMOb4OKe9uz7R3SPxmJxZjFWD2CHgH72KY6AnYXeVHT9qtNWyBplLDBAvIiiNaAdHmB3OrXkVsR7sloJae47A.8QiH1KB8P3uC-AKgd-C6_CAhq7O0UA22KD4uCB_DUfI&dib_tag=se&pd_rd_r=068403fd-9e24-4c2f-9ea1-c30d10ad7535&pd_rd_w=oVdPH&pd_rd_wg=XpbkZ&pf_rd_p=58c90a12-100b-4a2f-8e15-7c06f1abe2be&pf_rd_r=A59X0411PW99V7MSY26J&qid=1717912477&refinements=p_85%3A10440599031&rps=1&s=kitchen&sr=1-3&th=1"
    parts = productUrl.split("/")
    # Join the parts back together with '/' discarding refid of the url
    productUrl = "/".join(parts[:6])
    productUrl= productUrl+"/"
    # print(productUrl)
    reviewlist = []
    headers = {
        'authority': 'www.amazon.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'en-US,en;q=0.9,bn;q=0.8',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
    }
    def extractReviews(reviewUrl, pageNumber):
        resp = requests.get(reviewUrl, headers=headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        reviews = soup.findAll('div', {'data-hook': "review"})

        # Ensure the outputs directory exists
        if not os.path.exists('outputs'):
            os.makedirs('outputs')

        for item in reviews:
            with open(f'outputs/file_{pageNumber}.html', 'w', encoding='utf-8') as f:
                f.write(str(item))
            
            review = {
                'Review Title': item.find('a', {'data-hook': "review-title"}).text.strip(),
                'Rating': item.find('i', {'data-hook': 'review-star-rating'}).text.strip(),
                'Review Body': item.find('span', {'data-hook': 'review-body'}).text.strip(),
            }
            reviewlist.append(review)

    def totalPages(productUrl):
        resp = requests.get(productUrl, headers=headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        reviews = soup.find('div', {'data-hook': "cr-filter-info-review-rating-count"})
        return int(reviews.text.strip().split(', ')[1].split(" ")[0])


    reviewUrl = productUrl.replace("dp", "product-reviews")
    totalPg = totalPages(reviewUrl)

    print(totalPg)

    for i in range(10):     #change back to totalPg using 12 for testing
        print(f"Running for page {i+1}")
        try:
            pageUrl = reviewUrl + f"ref=cm_cr_getr_d_paging_btm_next_{i+1}?pageNumber={i+1}"
            extractReviews(pageUrl, i+1)
        except Exception as e:
            print(e)

    print("Scraping over")
    df = pd.DataFrame(reviewlist)
    df.to_csv('reviews.csv', index = False)

    nltk.download('stopwords')

    set(stopwords.words('english'))
    stop_words = stopwords.words('english')
    compound = 0
    pos = 0
    neg = 0
    neu = 0
    count = 0
    with open('reviews.csv', 'rb') as rawdata:
        result = chardet.detect(rawdata.read(100000))
        encoding = result['encoding']
    print(f"Detected encoding: {encoding}")
    with open('reviews.csv', 'r',encoding=encoding) as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)
        for line in csv_reader:
            # convert to lowercase
            text1 = line[2].lower()

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
