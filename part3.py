import json, ast
import pandas as pd
from django.utils.encoding import smart_str, smart_unicode
import requests_cache
import requests
import re
from bs4 import BeautifulSoup
from IPython.display import display
from ipywidgets import widgets
import sqlite3 as sql


requests_cache.install_cache("cache")

def modify(city):
    """
    modify the input
    
    Argument: city
    
    Return: soup from the url link
    """
    # capitalize the first letter of each word in a string
    city = city.title()
    # replace the empty space with the _
    city = city.strip().replace(' ', '_')
    url = "https://en.wikipedia.org/wiki/" + str(city) +",_California"
    info = requests.get(url).content
    wikisoup = BeautifulSoup(info, 'lxml')
    return wikisoup

def extract_overview(city):
    """
    extract a brief overview from the wikipedia page
    
    Argument: city
    
    Return: print the overview description
    """
    wikisoup = modify(city)
    content = wikisoup.findAll("p")
    if content[0].text == "California":
        brief = content[1].text
    else:
        brief = content[0].text
    print brief


def extract_info(city):
	wikisoup = modify(city)
	data1 = wikisoup.findAll("tr", {"class": "mergedrow"})
	data = [dat.text for dat in data1]
	split = [dat.strip("\n") for dat in data]
	pd_info = pd.DataFrame(split)
	pd_info.rename(columns = {list(pd_info)[0]: 'info'}, inplace = True)
	pd_info['info'] = pd_info['info'].map(lambda x: re.sub("(\[).*?([\]])", "", x))
	pd_info['info'] = pd_info['info'].map(lambda x: re.sub(ur'[\•]', ' ', x))
	pd_info['info'] = pd_info['info'].str.strip("\n")
	pd_info['info'] = pd_info['info'].str.strip()
	pd_info['info'] = pd_info['info'].str.replace("\n", " : ")
	pd_info['info'] = pd_info['info'].str.replace(" [: ]+", " : ")
	return pd_info

def recommend_res(city, res_cat, res_rating):
	city = city.title()
	visit_city = city + ", CA"
	res_cat = res_cat.title()
	rat_1 = res_rating[0]
	rat_2 = res_rating[-1]
	print "You enter City: %s, Restaurant Category: %s, Lower_bound Rating: %s, Upper_bound Rating: %s\n" %(visit_city, res_cat, rat_1, rat_2)
	conn = sql.connect("accommodation.sqlite")
	res_sql = '''SELECT categories, city, name, rating, review_count, snippet_text,url FROM Best_Restaurants WHERE city = '%s' 
				AND categories = '%s' AND rating BETWEEN '%s' AND '%s' ''' %(visit_city, res_cat, rat_1, rat_2)
	restaurants = pd.read_sql(res_sql, conn)

	res_sql_alternative = '''SELECT categories, city, name, rating, review_count, snippet_text,url FROM Best_Restaurants WHERE city = '%s' AND rating BETWEEN '%s' AND '%s' LIMIT 5''' %(visit_city, rat_1, rat_2)
	restaurants_alternative = pd.read_sql(res_sql_alternative, conn)

	if restaurants.empty:
		print("We are sorry. We can not find a restaurant that meets your criterias in our database. Please try a different kinds of food or rating. But first, let's look at the TOP 5 alternatives that we find.")
		return restaurants_alternative
	else:
		return restaurants
	conn.close()

def recommend_hotel_land(city, cat, rating, accommodation):
    city = city.title()
    visit_city = city + ", CA"
    cat = cat.title()
    if cat[-1] == 's':
        cat = cat[:-1]
    rat_1 = rating[0]
    rat_2 = rating[-1]
    print "You enter City: %s, Category: %s, Lower_bound rating: %s, Upper_bound rating: %s\n" %(visit_city, cat, rat_1, rat_2)
    conn = sql.connect("accommodation.sqlite")
    if 'hotels' in accommodation.lower():
        hotel_land_sql = '''SELECT categories, city, name, rating, review_count, snippet_text,url FROM Best_''' + accommodation + ''' WHERE city = '%s' 
                    AND name LIKE '%%%s%%' AND rating BETWEEN '%s' AND '%s' ''' %(visit_city, cat, rat_1, rat_2)
    
    else:
        hotel_land_sql = '''SELECT categories, city, name, rating, review_count, snippet_text,url FROM Best_''' + accommodation + ''' WHERE city = '%s' 
                    AND categories LIKE '%%%s%%' AND rating BETWEEN '%s' AND '%s' ''' %(visit_city, cat, rat_1, rat_2)
        
    hotel_land = pd.read_sql(hotel_land_sql, conn)
    
    hotel_land_sql_alternative = '''SELECT categories, city, name, rating, review_count, snippet_text,url FROM Best_''' + accommodation + ''' WHERE city = '%s' 
                    AND categories LIKE '%%%s%%' AND rating BETWEEN '%s' AND '%s' ''' %(visit_city, accommodation, rat_1, rat_2)
    
    hotel_land_alternative = pd.read_sql(hotel_land_sql_alternative, conn)
    
    if hotel_land.empty:
        print("We are sorry. We can not find a result that meets your criterias in our database. Please try a different input or rating. But first, let's look at the TOP 5 alternatives that we find.")
        return hotel_land_alternative
    else:
        return hotel_land
    conn.close()

city = raw_input("Please enter the city that you want to visit: ")
print "\nWelcome to the city of", city.title() + "! We are excited to provide you an ideal travel guide to help you explore this wonderful city!\n"
print "Here is some basic info of the city of", city.title() + "!\n"
extract_overview(city)
extract_info(city)

def ask_input():
    """
    get the user input
    
    Argument: None
    
    Return: recommended content in dataframe format
    """
    print "\nPlease answer the following questions so that we can recommend the best restaurants, hotels and landmarks to you.\n"
    
    accommodation = raw_input("Which accommondation do you want us to recommend? For example, restaurants, hotels or landmarks\n")
    
    if accommodation.title() in "Restaurants":
        res_cat = raw_input("What is your favorite kinds of food? \n")
        res_rating = raw_input("What is your preferred range of rating for restaurants? \n")
        output = recommend_res(city, res_cat, res_rating)
    elif accommodation.title() in "Hotels":
        hotel_cat = raw_input("What kind of hotel do you prefer to stay in? For example, inns, hotels or resorts? \n")
        hotel_rating = raw_input("What is your preferred range of rating for hotels? \n")
        output = recommend_hotel_land(city, hotel_cat, hotel_rating, 'Hotels')
    else:
        land_cat = raw_input("What kind of landmarks are you looking for? \n")
        land_rating = raw_input("What is your preferred range of rating for landmarks? \n")
        output = recommend_hotel_land(city, land_cat, land_rating, 'Landmarks')
    return output

def verify_satisfaction():
	satisfied = raw_input("Are you satisfied with the results? \n")

	if satisfied.title() in "Yes":
		print ("Thanks for using our system. We wish you have a wonderful trip.\n")
	else:
		print("Ok, let's try again.\n")
		return ask_input()

ask_input()

verify_satisfaction()


