from flask import Flask, request
from langchain.chat_models import AzureChatOpenAI
from dotenv import load_dotenv
import os
import json
import re
from flask_cors import CORS
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017')
db = client['satellite']
collection = db['data']

load_dotenv()

gpt_key = os.environ['AZURE_OPENAI_KEY']
gpt_endpoint = os.environ['AZURE_OPENAI_ENDPOINT']
gpt_deployment_name = os.environ['AZURE_OPENAI_DEPLOYMENT_NAME']

new_template = '''
You are a satellite guide aimed to provide info about satellites. 
        I will give you the name of a satellite and the country of origin. 
        Please give info about the satellite in the following
        json format :{{ "origin": [country of origin], "launch_date": [launch date of the satellite], 
        "purpose": [purpose of the satellite], 
        "weight": [weight of the satellite], 
        "cost": [cost of the satellite],
        "orbit": [Geostationary Orbit, Low Earth Orbit (LEO) or Medium Earth Orbit (MEO)],
        "lifespan": [lifespan of the satellite],
        "status": [operational or not operational]
        "history": [history of the satellite] }}.
        Also, please don't say any other words besides the json info. 
        Thank you, and here is the input:
        
        satellite name: {satellite_name}
        country of origin : {country_origin}
'''
prompt_template = PromptTemplate(
    input_variables=['satellite_name', 'country_origin'],
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

@app.route('/hello', methods=['GET'])
def hello_world():
    return 'hello world'

@app.route('/', methods=['POST'])
def homeroute():
    data = request.get_data()  # Get JSON data sent in the request
    text = json.loads(data)['satellite_name']  # Access the 'satellite_name' field
    query = collection.find_one({"name" : text}, projection={'_id': False})
    country = query['country']

    llm_chain = LLMChain(llm=llm, prompt=prompt_template)
    result  = llm_chain.invoke({"satellite_name": text, "country_origin": country})['text']
    print(result)
    json_match = re.search(r'{[^}]*}', result, re.DOTALL)
    json_str = json_match.group()
    data2 = json.loads(json_str)
    return json.dumps(data2)

@app.route('/satellites', methods=['GET'])
def get_all_satellites():
    query = collection.find(projection={'_id': False}, sort=[('country_of_origin', 1)])
    results = dict()
    for entry in query:
        results[entry['name']] = entry['country_of_origin']
    print(results)
    return json.dumps(results)

if __name__ == '__main__':
    app.run(debug=True)