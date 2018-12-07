from flask import Flask,request, json
from flask import render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
import recastai
import os
import requests
import pdb
import datetime
import time
from urllib.request import Request, urlopen
import dateutil.parser
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = True

#


# DB
Base = automap_base()
engine = create_engine('postgresql+psycopg2://root:rootroot@testdbinstance.cjgud0fxglke.us-east-1.rds.amazonaws.com:5432/insurance_info')
Base.prepare(engine, reflect=True)
Insurance = Base.classes.insurances
session = Session(engine)


RECAST_REQUEST_TOKEN = os.environ.get("API_REQUEST_TOKEN", default=None)
RECAST_DEVELOPER_TOKEN = os.environ.get("API_DEVELOPER_TOKEN", default=None)

@app.route('/')
def hello():
    insurances = session.query(Insurance).limit(10).all()
    return render_template('index.html', insurances=insurances)


@app.route('/api/v1/get_insurance_data', methods=['POST'])
def get_insurance_data():
    sampledata = {'nlp': {'uuid': 'cf771ba7-bc07-4520-8c1f-86f29c185d19', 'intents': [{'slug': 'insurancedetails', 'confidence': 0.99, 'description': None}], 'entities': {'policynumber': [{'value': '3123123', 'raw': '3123123', 'confidence': 0.87}]}, 'language': 'en', 'processing_language': 'en', 'version': '2.12.0-20a34c24', 'timestamp': '2018-11-29T06:12:23.139483+00:00', 'status': 200, 'source': '3123123', 'act': 'assert', 'type': None, 'sentiment': 'neutral'}, 'action_id': 'ed62dc85-d66f-4121-ac56-4034f95e1729', 'conversation': {'id': 'test-1543471909240', 'conversation_id': 'test-1543471909240', 'warning': 'The conversation_id field will be depreciated on January 1st 2018! Switch to using the id field instead', 'language': 'en', 'memory': {'policyNumber': {'value': '3123123', 'raw': '3123123', 'confidence': 0.87}}, 'skill_stack': ['askforinsurancenumber'], 'skill': 'askforinsurancenumber', 'skill_occurences': 2, 'participant_data': {}}}
    recast_response = json.loads(request.get_data())
    policy_number = recast_response['nlp']['entities']['policy_number'][0]['value']
    conversation_id = recast_response['conversation']['id']
    insurance_data = session.query(Insurance).filter_by(policy_number=policy_number)
    if insurance_data.count() == 0:
        response_message_obj = [{
            "type": "text",
            "content": "The policy you entered wasn't found. Please enter a valid policy number."
        }]
        data_to_store_in_memory = {
            "memory": {}
        }
    else:
        insurance_data = insurance_data.first()
        response_message_obj = [
            {
                "type": "text",
                "content":f"Policy with number {insurance_data.policy_number} found! Here are the details"
            },{
                "type": "card",
                "content": {
                    "title": "",
                    "subtitle": f"Account Name : {insurance_data.account_name} \n Premium : {insurance_data.premium}",
                    "imageUrl": "https://media.licdn.com/dms/image/C4E0BAQEqJ7-YxlwqSA/company-logo_200_200/0?e=2159024400&v=beta&t=7uwWiOsPAiYiv94Nr3tVZRfqeRVTXfObj2B1tPbAfL0",
                    "buttons": []
                }
            },{
                "type": "text",
                "content":"What else would you like to know? You can search for either of expiration date, policy status, address, phone number and policy type."
            }
        ]
        data_to_store_in_memory = {
            "memory" : {
                "policy_number": insurance_data.policy_number,
                "account_name": insurance_data.account_name,
                "premium": insurance_data.premium,
                "expiration_date": insurance_data.expiration_date.strftime('%d-%m-%Y'),
                "policy_status": insurance_data.status,
                "user_insurance_type":insurance_data.insurance_type,
                "user_insurance_address":insurance_data.address,
                "user_phone_number":insurance_data.phone_number,
                "plan":insurance_data.plan
            }
        }

    placeholder = [{
        "type": "text",
        "content": "Give me a minute, I'm searching for your policy"
    }]

    message_sent_response = requests.post(f'https://api.recast.ai/connect/v1/conversations/{conversation_id}/messages',
                                          headers={'Authorization': f'Token {RECAST_DEVELOPER_TOKEN}'},
                                          json={"messages": placeholder})
    time.sleep(20)
    store = requests.put(f'https://api.recast.ai/build/v1/users/kratiknayak/bots/insurance/versions/v1/builder/conversation_states/{conversation_id}',
                         headers={'Authorization': f'Token {RECAST_DEVELOPER_TOKEN}'},
                         json= data_to_store_in_memory)
    message_sent_response = requests.post(f'https://api.recast.ai/connect/v1/conversations/{conversation_id}/messages',
                                          headers={'Authorization': f'Token {RECAST_DEVELOPER_TOKEN}'},
                                          json={"messages": response_message_obj})
    return "OK"

@app.route('/api/v1/get_individual_details', methods=['POST'])
def get_policy_individual_details():
    recast_response = json.loads(request.get_data())
    entities = list(recast_response['nlp']['entities'].keys())
    all_entities = ['policy_number','premium','account_name','expiration_date','policy_status',"user_insurance_type","user_insurance_address","user_phone_number","plan"]
    memory = recast_response['conversation']['memory']
    conversation_id = recast_response['conversation']['id']
    entity_mapping = {"policy_number": "Policy Number",
                      "account_name": "Account Name",
                      "premium": "Premium",
                      "expiration_date": "Expiration Date",
                      "policy_status": "Policy Status",
                      "user_insurance_type": "Insurance Type",
                      "user_insurance_address": "Address",
                      "user_phone_number": "Phone Number",
                      "plan": "Plan"}
    response_message_obj = [{
        "type": "text",
        "content": "Here's what I found."
    }]
    resp = requests.post(f'https://api.recast.ai/connect/v1/conversations/{conversation_id}/messages',
                         headers={'Authorization': f'Token {RECAST_DEVELOPER_TOKEN}'},
                         json={"messages": response_message_obj})
    for entity in entities[:]:
        if entity not in all_entities:
            entities.remove(entity)

    for entity in entities:
        response_message_obj = [{
            "type": "text",
            "content": f"Your {entity_mapping[entity]}  is {memory[entity]}"
        }]
        resp = requests.post(f'https://api.recast.ai/connect/v1/conversations/{conversation_id}/messages',
                             headers={'Authorization': f'Token {RECAST_DEVELOPER_TOKEN}'},
                             json={"messages": response_message_obj})
    return "OK"


@app.route('/api/v1/select_insurance', methods=['POST'])
def buy_assistance():
    recast_response = json.loads(request.get_data())
    conversation_id = recast_response['conversation']['id']
    button_types = [{
        "type": "buttons",
        "content": {
            "title": "Please select from the options below",
            "buttons": [
                {
                    "title": "travel",
                    "type": "postback",
                    "value": "travel"
                },
                {
                    "title": "vehicle",
                    "type": "postback",
                    "value": "vehicle"
                },
                {
                    "title": "health",
                    "type": "postback",
                    "value": "health"
                }
            ]
        }
    }]
    resp = requests.post(f'https://api.recast.ai/connect/v1/conversations/{conversation_id}/messages',
                         headers={'Authorization': f'Token {RECAST_DEVELOPER_TOKEN}'},
                         json={"messages": button_types})
    return "Ok"

@app.route('/api/v1/select_insurance_1', methods=['POST'])
def buy_assistance_1():
    recast_response = json.loads(request.get_data())
    conversation_id = recast_response['conversation']['id']
    button_types = [{
        "type": "buttons",
        "content": {
            "title": "Please select from the options below",
            "buttons": [
                {
                    "title": "life",
                    "type": "postback",
                    "value": "life"
                },
                {
                    "title": "medical",
                    "type": "postback",
                    "value": "medical"
                },
                {
                    "title": "dental",
                    "type": "postback",
                    "value": "dental"
                }
            ]
        }
    }]
    resp = requests.post(f'https://api.recast.ai/connect/v1/conversations/{conversation_id}/messages',
                         headers={'Authorization': f'Token {RECAST_DEVELOPER_TOKEN}'},
                         json={"messages": button_types})
    return "Ok"



@app.route('/api/v1/buy_travel_insurance', methods=['POST'])
def buy_travel_insurance():
    recast_response = json.loads(request.get_data())
    conversation_id = recast_response['conversation']['id']
    response_message_obj = [{
        "type": "text",
        "content": "Let's do it. First, we need to ask you few questions."
    },
        {
            "type": "text",
            "content": "Please send me your Email Id. We'll send you the policy document on this email id."
        }
    ]
    req = requests.post(f'https://api.recast.ai/connect/v1/conversations/{conversation_id}/messages',
                        headers={'Authorization': f'Token {RECAST_DEVELOPER_TOKEN}'},
                        json={"messages": response_message_obj})
    return "Done"

@app.route('/api/v1/get_best_plan', methods=['POST'])
def get_best_plan():
    recast_response = json.loads(request.get_data())
    conversation_id = recast_response['conversation']['id']
    date = dateutil.parser.parse(recast_response['nlp']['entities']['datetime'][0]['iso']).date()
    today = datetime.now().date()
    number_of_days = (date - today).days
    if number_of_days < 30:
        response_message = [{
            "type": "text",
            "content": "Looking at all the information provided, I suggest you go for the 'basic' insurance plan"
        }]
    elif number_of_days > 30:
        response_message = [{
            "type": "text",
            "content": "Looking at all the information provided, I suggest you go for the 'premium' insurance plan"
        }]
    message_sent_response = requests.post(
        f'https://api.recast.ai/connect/v1/conversations/{conversation_id}/messages',
        headers={'Authorization': f'Token {RECAST_DEVELOPER_TOKEN}'},
        json={"messages": response_message})
    return "Okay"

@app.route('/api/v1/get_best_policies', methods=['POST'])
def get_best_healty_policy():
    recast_response = json.loads(request.get_data())
    conversation_id = recast_response['conversation']['id']
    memory = recast_response['conversation']['memory']
    age = memory['age']['value']
    salary = recast_response['nlp']['entities']['salary'][0]['value']
    response_message_obj = [{
        "type": "text",
        "content": "According to the date you've provided, here are some plans you could go for."
    }]
    if age == "20-40" and salary== "more_than_5000":
        carousle_items = create_carousel("$80","$100","$120","$10000","10 years")
    elif age == "20-40" and salary == "less_than_5000":
        carousle_items = create_carousel("$40", "$60", "$80","$8000","10 years")
    elif age == "40-60" and salary == "less_than_5000":
        carousle_items = create_carousel("$120", "$140", "$160","$8000","15 years")
    elif age == "40-60" and salary == "more_than_5000":
        carousle_items = create_carousel("$200", "$220", "$250","$10000","15 years")

    response_message_obj.append(carousle_items)
    message_sent_response = requests.post(
        f'https://api.recast.ai/connect/v1/conversations/{conversation_id}/messages',
        headers={'Authorization': f'Token {RECAST_DEVELOPER_TOKEN}'},
        json={"messages": response_message_obj})

    print(message_sent_response.text)
    return "Ok"

def create_carousel(plan_1,plan_2,plan_3,sum_assured,term):
    list_of_plans = {
        "type": "carousel",
        "content": [
            {
                "title": "Policy 1",
                "subtitle": f"Premium per month: {plan_1},Sum assured: {sum_assured}, Term: {term}",
                "imageUrl": "https://media.licdn.com/dms/image/C4E0BAQEqJ7-YxlwqSA/"
                            "company-logo_200_200/0?e=2159024400&v=beta&t=7uwWiOsPAiYiv94Nr3tVZRfqeRVTXfObj2B1tPbAfL0",
                "buttons": []
            },
            {
                "title": "Policy 2",
                "subtitle": f"Premium per month: {plan_2}, Sum assured: {sum_assured}, Term: {term}",
                "imageUrl": "https://media.licdn.com/dms/image/C4E0BAQEqJ7-YxlwqSA/"
                            "company-logo_200_200/0?e=2159024400&v=beta&t=7uwWiOsPAiYiv94Nr3tVZRfqeRVTXfObj2B1tPbAfL0",
                "buttons": []
            },
            {
                "title": "Policy 3",
                "subtitle": f"Premium per month: {plan_3}, Sum assured: {sum_assured}, Term: {term}",
                "imageUrl": "https://media.licdn.com/dms/image/C4E0BAQEqJ7-YxlwqSA/"
                            "company-logo_200_200/0?e=2159024400&v=beta&t=7uwWiOsPAiYiv94Nr3tVZRfqeRVTXfObj2B1tPbAfL0",
                "buttons": []
            }
        ]
    }
    return  list_of_plans


if __name__ == '__main__':
    app.run()
