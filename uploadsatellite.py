import os
from dotenv import load_dotenv
from pymongo import MongoClient
import re
import json
from langchain.chat_models import AzureChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Load the MongoDB URL from the .env file
load_dotenv()
mongo_url = os.getenv("DB_ENDPOINT")

# Connect to MongoDB
client = MongoClient(mongo_url)
db = client["satellite"]
collection = db["data"]

gpt_key = os.environ['AZURE_OPENAI_KEY']
gpt_endpoint = os.environ['AZURE_OPENAI_ENDPOINT']
gpt_deployment_name = os.environ['AZURE_OPENAI_DEPLOYMENT_NAME']

new_template = '''
You are a satellite guide aimed to provide info about satellites. 
I will give you a list of satellites. 
Please give info about the satellite origin country in ISO format.

OUTPUT : {{"name_of_satellite": "country_of_origin"}}

only give the output and nothing else.
Thank you, and here is the list of satellites: {satellite_names}
'''

prompt_template = PromptTemplate(
    input_variables=['satellite_names'],
    template=new_template
)

llm = AzureChatOpenAI(
    openai_api_key=gpt_key,
    deployment_name=gpt_deployment_name,
    openai_api_type='azure',
    openai_api_version='2023-05-15',
    openai_api_base=gpt_endpoint
)

# Parse the data from satellite_data.txt and push documents to MongoDB
with open("satellite.txt", "r") as file:
    # Read the file content
    file_content = file.read()
    
    # Remove carriage returns
    processed_data = re.sub(r'\r', '', file_content)
    
    # Split on newline not followed by '1' or '2'
    tle_list = re.split(r'\n(?=[^12])', processed_data)
    
    # Split each TLE entry by newline
    tle_list = [tle.split('\n') for tle in tle_list]

    # Trim each list element
    tle_list = [[element.strip() for element in tle] for tle in tle_list]

    satellite_names = [tle[0] for tle in tle_list]

# Print the TLE list for debugging
# print(tle_list[0:2])
# print(satellite_names)

satellite_sure_origin = [satellite_name for satellite_name in satellite_names if satellite_name.startswith('STARLINK')]

# print(satellite_sure_origin)

for satellite_name in satellite_sure_origin:
    document = {
        "name": satellite_name,
        "country_of_origin": "US"
    }

    # Insert the document into the collection
    # collection.insert_one(document)

satellite_sure_origin = [satellite_name for satellite_name in satellite_names if satellite_name.startswith('ONEWEB')]

# print(satellite_sure_origin)

for satellite_name in satellite_sure_origin:
    document = {
        "name": satellite_name,
        "country_of_origin": "UK"
    }

    # Insert the document into the collection
    # collection.insert_one(document)

satellite_sure_origin = [satellite_name for satellite_name in satellite_names if satellite_name.startswith('COSMOS')]

# print(satellite_sure_origin)

for satellite_name in satellite_sure_origin:
    document = {
        "name": satellite_name,
        "country_of_origin": "RUSSIA"
    }

    # Insert the document into the collection
    # collection.insert_one(document)

filtered_satellite_names = [satellite_name for satellite_name in satellite_names if not satellite_name.startswith('STARLINK') and not satellite_name.startswith('ONEWEB') and not satellite_name.startswith('COSMOS')]

# print(filtered_satellite_names)
# print(len(filtered_satellite_names))

# for 

# 'https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/countries-codes/records?select=iso2_code%2C%20label_en'

# ccodes = collection.distinct("country_of_origin")
# invalid_ccodes = [ccode for ccode in ccodes if len(ccode) != 2]

# print(invalid_ccodes)

country_dict = {
    "AE": "United Arab Emirates",
    "AR": "Argentina",
    "AT": "Austria",
    "AU": "Australia",
    "AZ": "Azerbaijan",
    "BD": "Bangladesh",
    "BE": "Belgium",
    "BG": "Bulgaria",
    "BO": "Bolivia",
    "BR": "Brazil",
    "BY": "Belarus",
    "CA": "Canada",
    "CH": "Switzerland",
    "CL": "Chile",
    "CN": "China",
    "DE": "Germany",
    "DJ": "Djibouti",
    "DK": "Denmark",
    "DZ": "Algeria",
    "EC": "Ecuador",
    "EE": "Estonia",
    "EG": "Egypt",
    "ES": "Spain",
    "EU": "European Union",
    "FI": "Finland",
    "FR": "France",
    "GB": "United Kingdom",
    "GR": "Greece",
    "GT": "Guatemala",
    "HK": "Hong Kong",
    "HU": "Hungary",
    "ID": "Indonesia",
    "IE": "Ireland",
    "IL": "Israel",
    "IN": "India",
    "IR": "Iran",
    "IT": "Italy",
    "JO": "Jordan",
    "JP": "Japan",
    "KE": "Kenya",
    "KR": "South Korea",
    "KW": "Kuwait",
    "KZ": "Kazakhstan",
    "LA": "Laos",
    "LU": "Luxembourg",
    "MA": "Morocco",
    "MX": "Mexico",
    "MY": "Malaysia",
    "NG": "Nigeria",
    "NL": "Netherlands",
    "NO": "Norway",
    "PE": "Peru",
    "PH": "Philippines",
    "PK": "Pakistan",
    "PL": "Poland",
    "QA": "Qatar",
    "RU": "Russia",
    "SA": "Saudi Arabia",
    "SE": "Sweden",
    "SG": "Singapore",
    "TH": "Thailand",
    "TM": "Turkmenistan",
    "TR": "Turkey",
    "TW": "Taiwan",
    "TZ": "Tanzania",
    "UA": "Ukraine",
    "UK": "United Kingdom",
    "US": "United States",
    "VE": "Venezuela",
    "VN": "Vietnam",
    "ZA": "South Africa"
}

all_entries = collection.find()
for entry in all_entries:
    country_of_origin = entry["country_of_origin"]
    if country_of_origin in country_dict.keys():
        collection.update_one({"_id": entry["_id"]}, {"$set": {"country": country_dict[country_of_origin]}})


# remaining_satellites = []

# for satellite in filtered_satellite_names:
#     document = collection.find_one({"name": satellite})
    
#     if document is None:
#         remaining_satellites.append(satellite)

# print(len(remaining_satellites))
# print(remaining_satellites)

# llm_chain = LLMChain(llm=llm, prompt=prompt_template)
# result  = llm_chain.invoke({"satellite_names": remaining_satellites})["text"]
# # data = json.loads(result)
# print(result)

# json_match = re.search(r'{[^}]*}', result, re.DOTALL)
# json_str = json_match.group()
# data = json.loads(json_str)
# print(data)

# for name in data.keys():
#     # Create a document to insert into the collection
#     document = {
#         "name": name,
#         "country_of_origin": data[name]
#     }

#     # Insert the document into the collection
#     collection.insert_one(document)
    
# batch_size = 200
# num_batches = len(remaining_satellites) // batch_size

# for i in range(num_batches):
#     start_index = i * batch_size
#     end_index = start_index + batch_size
#     batch = remaining_satellites[start_index:end_index]

#     llm_chain = LLMChain(llm=llm, prompt=prompt_template)
#     result  = llm_chain.invoke({"satellite_names": batch})["text"]
#     # data = json.loads(result)
#     print(result)

#     json_match = re.search(r'{[^}]*}', result, re.DOTALL)
#     json_str = json_match.group()
#     data = json.loads(json_str)
#     print(data)

#     for name in data.keys():
#         # Create a document to insert into the collection
#         document = {
#             "name": name,
#             "country_of_origin": data[name]
#         }

#         # Insert the document into the collection
#         collection.insert_one(document)

# -----------------------------------------------------------------
# batch_size = 500
# num_batches = len(filtered_satellite_names) // batch_size

# for i in range(num_batches):
#     start_index = i * batch_size
#     end_index = start_index + batch_size
#     batch = filtered_satellite_names[start_index:end_index]

#     llm_chain = LLMChain(llm=llm, prompt=prompt_template)
#     result  = llm_chain.invoke({"satellite_names": batch})["text"]
#     # data = json.loads(result)
#     print(result)

#     json_match = re.search(r'{[^}]*}', result, re.DOTALL)
#     json_str = json_match.group()
#     data = json.loads(json_str)
#     print(data)

#     for name in data.keys():
#         # Create a document to insert into the collection
#         document = {
#             "name": name,
#             "country_of_origin": data[name]
#         }

#         # Insert the document into the collection
#         collection.insert_one(document)
# -----------------------------------------------------------------

# # Insert documents into the MongoDB collection
# for name in data.keys():
#     # Create a document to insert into the collection
#     document = {
#         "name": name,
#         "country_of_origin": data[name]
#     }

#     # Insert the document into the collection
#     collection.insert_one(document)



# Close the MongoDB connection
client.close()
