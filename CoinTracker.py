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

# python3 CoinTracker.py

class CoinTracker:
    def __init__(self): 
        load_dotenv(find_dotenv())
        self.cg_api_url = 'https://api.coingecko.com/api/v3/'
        self.cg_api_key = os.getenv('COINGECKO_API_KEY')
        self.gpt_api_key = os.getenv('OPENAI_API_KEY')
        self.encoded_image = self.analyze_pasted_image()
        self.portfolio_dict = self.ai_prompting(self.encoded_image)
        print(self.portfolio_dict)
    
    def analyze_pasted_image(self):
        # analyze pasted image format to base64 for openAi to process
        input("Press Enter to analyze image copied to clipboard.\n")
        
        while True:
            image = ImageGrab.grabclipboard()
            if isinstance(image, Image.Image):
                print('Succesfully grabbed image from clipboard.\n')
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
            template = """Analyze the user's crypto portfolio from the image. {format_instructions}
            Based on the image, what are the user's crypto holdings and their values?""",
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
        
        chain = model | parser
        
        crypto_dict = chain.invoke([message])
        
        return crypto_dict
        
        
        
if __name__ == "__main__":
    tracker = CoinTracker()
    
    
    
    
    
    
    
    
    


    