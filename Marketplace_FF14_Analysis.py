# IMPORTS
import importlib
import json
from optparse import Values
import time
import calendar
import os
import shutil
import csv
import sys
import asyncio #
import requests #Faire des requetes HTTP
import pandas
from datetime import datetime, timedelta
import random

#Import for Proxies Cycle; 
#pip3 install lxml
from lxml.html import fromstring
from itertools import cycle
import traceback

#Counter Scan Research
start = time.time()

#To know how much item to analyze in analyzeItems() from getItemMarketable() 
iteration = 0

# The modify variables
usWorldID = 97 #(Ragnarok)
coefMargin = 9 #(Coeff de marge souhaité)
minimumSellPrice = 20000
dayDelta = 1
language = "fr"
categoryWanted = "none" # (furniture, collectables)
verifySalePotential = True

# WORLDS
# EU
worldsList = {
	"39" : "Omega", # CHAOS
	"71" : "Moogle",# CHAOS
	"80" : "Cerberus",# CHAOS
	"83" : "Louisoix",# CHAOS
	"85" : "Spriggan",# CHAOS
	"97" : "Ragnarok",# CHAOS
	"400" : "Sagittarius",# CHAOS
	"401" : "Phantom",# CHAOS
	"33" : "Twintania",# LIGHT
	"36" : "Lich",# LIGHT
	"42" : "Zordiak",# LIGHT
	"56" : "Phoenix",# LIGHT
	"66" : "Odin",# LIGHT
	"67" : "Shiva",# LIGHT
	"402" : "Alpha",# LIGHT
	"403" : "Raiden",# LIGHT
}

#Get proxy list to speed up the scan. (8 requests simulatenous / IP)
def get_proxies():
	urlProxies = 'https://free-proxy-list.net/'
	response = requests.get(urlProxies)
	parser = fromstring(response.text) #Script HTML de la page complet
	proxies = set()
	for i in parser.xpath('//tbody/tr')[:20]:
		if i.xpath('.//td[7][contains(text(),"yes")]'): #If HTTPS is "yes"
		#Grabbing IP and corresponding PORT
			proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
			proxies.add(proxy)
	return proxies

#Initialisation Proxy
proxies = get_proxies()
proxy_pool = cycle(proxies)

# JSON Item ID with name on different languages, par TeamCraft
# To give name of object with ID in files.
# A REPARER - Sert à donner le véritable nom au items, grâce à leur ID
itemsID = requests.get("https://raw.githubusercontent.com/ffxiv-teamcraft/ffxiv-teamcraft/master/libs/data/src/lib/json/items.json", verify=True).json()

#API
universalisAPI = "https://universalis.app/api/v2/"
allItemsMarketable = requests.get(universalisAPI + "marketable").json()

#Convert usWorldID to usWorldName
usWorldName = ""
for worldID, worldName in worldsList.items():
	if worldID == str(usWorldID):
		usWorldName = str(worldName)
		break

#If the folder 'items' doesn't exist, we create it, and go in
def itemsFolderVerification():
	filepathItems = './items/'
	if os.path.exists(filepathItems) == False:
		os.makedirs(filepathItems, mode = 511, exist_ok= False)
	else:
		shutil.rmtree(filepathItems)
		os.makedirs(filepathItems, mode = 511, exist_ok= False)
	os.chdir(filepathItems)

#Get all item data
def getServerItemData(itemToData):
	
	dataItem = []
	try:
		dataItem = requests.get(universalisAPI + str(usWorldID) + "/" + str(itemToData)).json() #proxies={"http": proxy, "https": proxy}
	#Different Except possible
	except requests.exceptions.Timeout:
		print("Timeout - itemID:" + str(itemToData) + " World: " + str(usWorldName))
	except requests.exceptions.TooManyRedirects:
		print("TooManyRedirects - itemID:" + str(itemToData) + " World: " + str(usWorldName))
	except requests.exceptions.RequestException as e:
		print("RequestException ERROR - itemID:" + str(itemToData) + " World: " + str(usWorldName))
	return dataItem


#Function To Analyze items, with WorldList

def analyzeItems(itemsToAnalyze, worldsToAnalyze):
	print("Starting of the analyze...")
	iteration = 0
	print("Number of items to analyze: " + str(nbOfItems))

	#For each item
	for item in itemsToAnalyze:
		#Get percentage of progress analyse
		iteration += 1
		if random.random() < 0.04:
			percent = iteration / nbOfItems * 100
			print("Progress.. " + str(int(percent)) + "%")

		#Create dictionnary to stock all prices of items
		pricePerWorld = {}
		priceGoalSuccess = {}

		#Take a new proxy for each world, to speed up the scan
		#proxy = next(proxy_pool)
  

		#Take history of the item in each world
		serverItemData = getServerItemData(item)
  
		#Take last sell timestamp in us world 
		try:
			lastSell = serverItemData['recentHistory'][0]["timestamp"]
		except IndexError:
			lastSell = 'null' #If item has never been sell
			continue #Next Item
		except TypeError:
			lastSell = 'null'
			print("Type error during get timestamp. Analyze resume..")
			continue
		
		#If the item is sell before X days..
		if verifySalePotential is True:
			try:
				lastSecondSellTime = serverItemData['recentHistory'][1]["timestamp"]
			except IndexError:
				lastSecondSellTime = 'null' #The item has not been selling 2 times
				continue #Next ITem

			#Item is selling 2 times or more
   
			#Verify if the item has been selling one time in period and second time in period * 1,5
			if (datetime.fromtimestamp(lastSell) < (datetime.now() - timedelta(days=dayDelta))) and (datetime.fromtimestamp(lastSecondSellTime) < (datetime.now() - timedelta(days=dayDelta * 1.5))): 
				continue #Next Item, because it's not selling 2 times in perdiod that we have define thanks to dayDelta
		
  		#If "verifySalePotential" is False, check that item has been sell since dayDelta
		else:
			if datetime.fromtimestamp(lastSell) < (datetime.now() - timedelta(days=dayDelta)):
				continue #Next Item

		#Convert timestamp
		lastSell = datetime.fromtimestamp(lastSell) #FORMAT 2022-10-05 05:25:18
		
		#Verify pricing in world we want
		try:
			goalPrice = serverItemData['recentHistory'][0]["pricePerUnit"] / coefMargin #Define goal price
		except IndexError: #If item has never been price
			goalPrice = 'null'
			continue #Next Item
		if goalPrice * coefMargin <= minimumSellPrice: #If item is not at minimum price
			continue #Next Item

		#Verify the second item price
		if verifySalePotential is True:
			try:
				lastSecondSellPrice = serverItemData['recentHistory'][1]["pricePerUnit"]
			except IndexError:
				lastSecondSellPrice = 'null' #The item has not been selling 2 times
				continue #Next Item 
			if ((lastSecondSellPrice * 1.2) < (goalPrice * coefMargin)):
				continue #Next Item
				

		#SO, if the item has been already sell, in a delay of - X days and that the price's verification is good, SO...

		#Take name of the item and put it in l'itemID.json
		itemName = itemsID[str(item)][language] 
		priceGoalSuccess["Name"] = itemName 

		#Put price of us world'item in l'itemID.json at first
		priceGoalSuccess[usWorldName] = round(goalPrice * coefMargin)

		#Go in each world
		for worldID, worldName in worldsToAnalyze.items():
			#proxy = next(proxy_pool) #Prendre un nouveau proxy à chaque test, pour augmenter la rapidité
			tempItemData = []

			#Have data item in the world
			try:
				tempItemData = requests.get(universalisAPI + str(worldID) + "/" + str(item)).json()#proxies={"http": proxy, "https": proxy}
			
   			#Manage all exceptions
			except requests.exceptions.Timeout:
				print("Timeout - itemID:" + itemName + " World: " + worldName)
				continue
			except requests.exceptions.TooManyRedirects:
				print("TooManyRedirects - itemID:" + itemName + " World: " + worldName)
				continue
			except requests.exceptions.RequestException as e:
				print("RequestException ERROR - itemID:" + itemName + " World: " + worldName)
				continue
			try:
				price = tempItemData['listings'][0]["pricePerUnit"] #Price of last sell in the world
			except IndexError: #If object has never been sold
				price = 'null'
				continue

			#Price in dictionnary, where all price of all worlds will be save
			pricePerWorld[worldName] = price
		
	#Once price of each world in pricePerWorld[X], we verify if we have the margin
		for world, price in pricePerWorld.items():
			if (price <= goalPrice):
				#Put in a JSON
				priceGoalSuccess[world] = price
		
  		#If no world have interresting price 
		if len(priceGoalSuccess.keys()) <= 2:
			continue #Next item
				
	#Create the itemID.json where put the name, usWorld's price and the multiple world where the name and price associated
		with open(str(item) +'.json', 'a', encoding='UTF-8') as file:
			file.write(json.dumps(priceGoalSuccess, indent=4, ensure_ascii=False))

def getItemMarketable(category):
	global nbOfItems #Number of item to analyse, after this function
 
    #Create a JSON with all items marketable  ; USELESS FOR SCRIPT, ONLY TO UNDERSTAND
	with open("allItemsMarketable" +'.json', 'a', encoding='UTF-8') as file:
		file.write(json.dumps(allItemsMarketable, indent=4))
    
	#Reading CSV's category file with itemID, only for the columns with ID
	if category == "furniture": #FURNITURE
		print("Category furniture selected")
		url = 'https://github.com/xivapi/ffxiv-datamining/blob/master/csv/FurnitureCatalogItemList.csv?raw=true'
		columns = ["1"]
		indexScan = '1'
		itemsCategory = pandas.read_csv(url, usecols=columns, on_bad_lines='skip').to_dict(orient='list')
		#Create JSON file only with different item for the category ; USELESS FOR SCRIPT, ONLY TO UNDERSTAND
		with open("categoryData" +'.json', 'a', encoding='UTF-8') as file:
			file.write(json.dumps(itemsCategory, indent=4))
   
	elif category == "collectables": #COLLECTABLES
		print("Category Collectable Items Shop selected")
		url = 'https://github.com/xivapi/ffxiv-datamining/blob/master/csv/CollectablesShopItem.csv?raw=true'
		columns = ["0"]
		indexScan = '0'
		itemsCategory = pandas.read_csv(url, usecols=columns, on_bad_lines='skip').to_dict(orient='list')
		#Create JSON file only with different item for the category ; USELESS FOR SCRIPT, ONLY TO UNDERSTAND
		with open("categoryData" +'.json', 'a', encoding='UTF-8') as file:
			file.write(json.dumps(itemsCategory, indent=4))
  
	else: #If any category is define
		print("No category has been selected..")
		print("/!/ Analyse of items marketable of FFXIV")
		print("The duration of the scan will be more longer !")
		nbOfItems = len(allItemsMarketable)
		return allItemsMarketable

    
	#Create list of itemID in category
	itemsMarketableCategory = []

	iteration = 0
	globalItems = 0
	#Counter of iteration
	while 1:
		iteration = iteration + 1
		#Try to have ID
		try:
			currentScanItemID = itemsCategory[indexScan][iteration]
   
			#If itemScan is a real ID and is in the list of all item marketable
			if (currentScanItemID != "Item" or "" or 0) and (int(currentScanItemID) in allItemsMarketable):
				itemsMarketableCategory.append(currentScanItemID)
				globalItems = globalItems + 1
		except:
			print ("End of the category's scan, " + str(iteration) + " items marketable in the category")
			break

	nbOfItems = globalItems
	return itemsMarketableCategory 


#MAIN SCRIPT
def main():
	itemsFolderVerification()
	itemsMarketableToAnalyze = getItemMarketable(categoryWanted)
	analyzeItems(itemsMarketableToAnalyze, worldsList)
main()

#Après que chaque item est été regardé 
 #End of the script
end = time.time()
print("Scan duration: " + str(int(round(end - start) / 60)) + "m")