from flask import Flask, request
from langchain.chat_models import AzureChatOpenAI
from dotenv import load_dotenv
import os
import json
from flask_cors import CORS
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

load_dotenv()

gpt_key = os.environ['AZURE_OPENAI_KEY']
gpt_endpoint = os.environ['AZURE_OPENAI_ENDPOINT']
gpt_deployment_name = os.environ['AZURE_OPENAI_DEPLOYMENT_NAME']

new_template = '''
You are a satellite guide aimed to provide info about satellites. 
        I will give you the name of a satellite. 
        Please give info about the satellite in the following
        json format :{{ origin: [country of origin], launch_date: [launch date of the satellite], 
        purpose: [purpose of the satellite], 
        weight: [weight of the satellite], 
        cost: [cost of the satellite],
        history: [history of the satellite] }}.
        Also, please don't say any other words besides the json info. 
        Thank you, and here is the satellite name: {satellite_name}
'''
prompt_template = PromptTemplate(
    input_variables=['satellite_name'],
    template=new_template
)

app = Flask(__name__)
CORS(app)

llm = AzureChatOpenAI(
    openai_api_key=gpt_key,
    deployment_name=gpt_deployment_name,
    openai_api_type='azure',
    openai_api_version='2023-05-15',
    openai_api_base=gpt_endpoint
)

@app.route('/', methods=['POST'])
def homeroute():
    data = request.get_data()  # Get JSON data sent in the request
    text = json.loads(data)['satellite_name']  # Access the 'satellite_name' field
    llm_chain = LLMChain(llm=llm, prompt=prompt_template)
    result  = llm_chain.invoke({"satellite_name": text})['text']
    print(result)
    return json.dumps(result)

if __name__ == '__main__':
    app.run(debug=True)