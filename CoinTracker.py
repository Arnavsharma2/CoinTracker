import io
import os
import base64
from PIL import ImageGrab,Image
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain.schema.runnable import RunnableParallel, RunnableBranch, RunnableLambda
from pydantic import BaseModel, Field    
from typing import Literal
import sys
import google.generativeai as genai
import os
import requests
import csv
from time import sleep

# python3 CoinTracker.py

class CoinTracker:
    def __init__(self): 
        load_dotenv(find_dotenv())
        self.cg_api_key = os.getenv('COINGECKO_API_KEY')
        self.gpt_api_key = os.getenv('OPENAI_API_KEY')
        # generate auth key for profile
        # save profile to database
        self.start_program()
    
    def start_program(self):
        choice = -1
        print("\n\nWhat would you like to do?\n1. Create new crypto portfolio from image\n2. Load portfolio\n3. Exit")
        while(choice != 1 and choice != 2 and choice != 3):
            try:
                choice = int(input())
            except ValueError:
                print("Invalid input. Please enter a valid number.")
                continue
        if choice == 1:
            self.encoded_image = self.analyze_pasted_image() # analyze image and return base64 encoded image
            self.portfolio_dict = self.ai_prompting(self.encoded_image) # convert image to coingecko dictionary of ids
            self.portfolio_prices_dict = self.get_crypto_value(self.portfolio_dict) # get current prices of each item 
            self.amount_spent_dict = self.get_spent(self.portfolio_dict) # get amount money spent
            self.save_portfolio(self.portfolio_dict, self.portfolio_prices_dict, self.amount_spent_dict)
        elif choice == 2:
            self.load_portfolio()
            self.start_program()
        elif choice == 3:
            print("Exiting program.")
            exit()
    
    def analyze_pasted_image(self):
        # analyze pasted image format to base64 for openAi to process
        input("\n\nPress Enter to analyze image copied to clipboard.\n")
        
        while True:
            image = ImageGrab.grabclipboard()
            if isinstance(image, Image.Image):
                print('Successfully grabbed image from clipboard.\n')
                image = ImageGrab.grabclipboard()
                # image.show()
                break
            
            else:
                print('No image in clipboard. Please try again.\n')
                input("Press Enter to analyze image copied to clipboard\n")
                
        tempFile = io.BytesIO()
        image.save(tempFile, format="PNG")
        image_str = base64.b64encode(tempFile.getvalue()).decode("utf-8")
        
        return image_str
        
    def ai_prompting (self, image_encoding):
        parser = JsonOutputParser()
        format_instructions = parser.get_format_instructions()
        
        prompt = PromptTemplate(
            template = """Analyze the user's crypto portfolio from the image, return a dictionary like this example 
            Cosmos: 60, Bitcoin: 0.03 but use the coingecko id name for each, make sure to double check the capitilization
            and spelling to ensure the coingecko id for each crypto is accurate. 
            {format_instructions} Based on the image, what are the user's crypto holdings and their values?""",
            input_variables=[],
            partial_variables= {'format_instructions': format_instructions}            
        )
        
        prompt = prompt.format()
        
        model = ChatGoogleGenerativeAI(model = "gemini-1.5-flash-latest")
        
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    # get text part of prompt
                    "text": prompt.format(),
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/png;base64,{image_encoding}",
                },
            ]
        )
        
        try:
            chain = model | parser
            
            crypto_dict = chain.invoke([message])
            
            return crypto_dict
        
        except Exception as e:
            raise Exception(f"Failed to analyze image, please try again later {e}")
    
    def get_crypto_value(self, crypto_dict):
        coin_ids = []
        
        if 'render' in crypto_dict:
            crypto_dict['render-token'] = crypto_dict.pop('render')
        
        for key in crypto_dict:
            coin_ids.append(key)
            
        prices_dict = {}
            
        ids_str = ",".join(coin_ids)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_str}&vs_currencies=usd"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            price_data = response.json()
            
            if not price_data:
                raise Exception("no data received")
            
            for coin, data in price_data.items():
                temp = coin[0].upper()
                coin = temp + coin[1:]
                prices_dict[coin] = data.get('usd')*crypto_dict[coin.lower()]
                
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch Coin Gecko crypto data, please try again later {e}")

        return prices_dict

    def portfolio_value(self, dict):
        total = 0.0
        for key in dict:
            total += dict[key]
        return total
    
    def get_spent(self, amount_dict):
        spent_dict = {}
        # choice = -1
        # while choice != 1 and choice != 2:
        #     choice = int(input(f'''Enter 1 if you would like to enter the amount spent for each crypto\nEnter 2 
        #                     if you would like to enter only the total amount spent for the entire portfolio\n '''))
        # if choice == 1:
        for key, amount in amount_dict.items():
            price = -1
            while(price < 0):
                try:
                    price = float(input(f"\nHow much money did you spend in order to purchase {amount} shares of {key}: "))
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
                    continue
            spent_dict[key] = price
        # else:
        #     spent_dict['total'] = float(input(f"\nEnter the price spent for your entire portfolio:"))
        return spent_dict#, choice
            
    def save_portfolio(self, amount_dict, price_dict, spent_dict):
        portfolio_name = input(f"\nEnter the name of your portfolio:")
        with open('portfolio.csv', 'w') as file:
            writer = csv.writer(file)
            writer.writerow(['Portfolio', 'Crypto', 'Amount Held', 'Price Paid', 'Total Value'])
            for key in amount_dict:
                temp = key[0].upper() + key[1:]
                writer.writerow([portfolio_name, key, amount_dict[key], spent_dict[key], price_dict[temp]])
        print(f"\nPortfolio {portfolio_name} saved to portfolio.csv")
            
    def load_portfolio(self):
        print("-"*100)
        with open('portfolio.csv', 'r') as file:
            reader = csv.reader(file)
            portfolio_name = ''
            while(portfolio_name == ''):
                try:
                    portfolio_name = input(f"\nEnter the name of the portfolio you would like to view: ")
                except ValueError:
                    print("Enter a valid input.")
            profit_loss = 0.0
            total_value = 0.0
            print()
            print(portfolio_name)
            found = False
            crypto_dict = {}
            for row in reader:
                if row[0] == portfolio_name:
                    crypto_dict[row[1]] = float(row[2])
            crypto_dict = self.get_crypto_value(crypto_dict)
            file.seek(0) # reset file pointer to beginning of file
            for row in reader:
                if row[0] == portfolio_name:
                    found = True
                    newKey  = row[1][0].upper() + row[1][1:]
                    print(f"{row[1]} updated with current price of ${crypto_dict[newKey]}")
                    row[4] = crypto_dict[newKey]
                    print(f"{float(row[2]):.4f} {row[1]} | Total Value Held: ${float(row[4]):.1f} | Price Paid: ${float(row[3]):,.1f} | Profit/Loss: ${float(row[4]) - float(row[3]):,.1f} | Profit/Loss Percentage: {((float(row[4]) - float(row[3]))/float(row[3]))*100:.2f}%")
                    profit_loss += float(row[4]) - float(row[3])
                    total_value += float(row[4])
            if not found:
                print("\nEnter a valid portfolio name. And try again.")
                self.load_portfolio()
            print(f"\nTotal Value Held: ${total_value:,.1f}")
            print(f"Total Profit/Loss: ${profit_loss:,.1f}\n")
            print("-"*100)
            output = ''
            while(output != 'y' and output != 'n'):
                output = input("\nWould you like to view another portfolio? (y/n): ")
                if output == 'y':
                    self.load_portfolio()
                elif output == 'n':
                    self.start_program()
        
if __name__ == "__main__":
    tracker = CoinTracker()
    
    
    
    
    
    
    
    
    


    