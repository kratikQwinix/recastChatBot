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

@app.route('/api/v1/getResponse', methods=['GET'])
def getResponse():
    client = recastai.Client(RECAST_REQUEST_TOKEN)
    response = client.build.dialog({'type': 'text', 'content': request.args.get('message')}, "12345")
    res = {
        "conversation_id":response.conversation.id,
        "messages":response.messages[0].content
    }
    return json.dumps(res)


@app.route('/api/v1/getInsuranceData', methods=['POST'])
def getInsuranceData():
    sampledata = {'nlp': {'uuid': 'cf771ba7-bc07-4520-8c1f-86f29c185d19', 'intents': [{'slug': 'insurancedetails', 'confidence': 0.99, 'description': None}], 'entities': {'policynumber': [{'value': '3123123', 'raw': '3123123', 'confidence': 0.87}]}, 'language': 'en', 'processing_language': 'en', 'version': '2.12.0-20a34c24', 'timestamp': '2018-11-29T06:12:23.139483+00:00', 'status': 200, 'source': '3123123', 'act': 'assert', 'type': None, 'sentiment': 'neutral'}, 'action_id': 'ed62dc85-d66f-4121-ac56-4034f95e1729', 'conversation': {'id': 'test-1543471909240', 'conversation_id': 'test-1543471909240', 'warning': 'The conversation_id field will be depreciated on January 1st 2018! Switch to using the id field instead', 'language': 'en', 'memory': {'policyNumber': {'value': '3123123', 'raw': '3123123', 'confidence': 0.87}}, 'skill_stack': ['askforinsurancenumber'], 'skill': 'askforinsurancenumber', 'skill_occurences': 2, 'participant_data': {}}}
    recast_response = json.loads(request.get_data())
    policy_number = recast_response['nlp']['entities']['policynumber'][0]['value']
    conversation_id = recast_response['conversation']['id']
    insurance_data = session.query(Insurance).filter_by(policy_number=policy_number)
    print(recast_response)
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
        response_message_obj = [{
            "type": "card",
            "content": {
              "title": "CARD_TITLE",
              "title": "CARD_TITLE_1",
              "subtitle": "CARD_SUBTITLE",
              "subtitle": "CARD_SUBTITLE_1",
            }
          }]
        # response_message_obj = [{
        #     "type": "text",
        #     "content":"Policy found! What would you like to know about it?"
        # }]
        data_to_store_in_memory = {
            "memory" : {
                "policy_number": insurance_data.policy_number,
                "account_name": insurance_data.account_name,
                "premium": insurance_data.premium,
                "expiration_date": insurance_data.expiration_date.strftime('%d-%m-%Y')
            }
        }

    placeholder = [{
        "type": "text",
        "content": "Give me a minute, I'm searching for your policy"
    }]


    # time.sleep(20)
    # store = requests.put(f'https://api.recast.ai/build/v1/users/kratiknayak/bots/insurance/versions/v1/builder/conversation_states/{conversation_id}',
    #                                         headers={'Authorization': f'Token {RECAST_DEVELOPER_TOKEN}'},
    #                                         json= data_to_store_in_memory)
    message_sent_response = requests.post(f'https://api.recast.ai/connect/v1/conversations/{conversation_id}/messages',
                                          headers={'Authorization': f'Token {RECAST_DEVELOPER_TOKEN}'},
                                          json={"messages": response_message_obj})
    # print(store.text)
    return "OK"


@app.route('/api/v1/getIndividualDetails', methods=['POST'])
def get_policy_individual_details():
    recast_response = json.loads(request.get_data())
    entities = list(recast_response['nlp']['entities'].keys())
    all_entities = ['policy_number','premium','account_name',"expiration_date"]
    memory = recast_response['conversation']['memory']
    conversation_id = recast_response['conversation']['id']
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
            "content": f"Your {entity}  is {memory[entity]}"
        }]
        resp = requests.post(f'https://api.recast.ai/connect/v1/conversations/{conversation_id}/messages',
                      headers={'Authorization': f'Token {RECAST_DEVELOPER_TOKEN}'},
                      json={"messages": response_message_obj})
        print(resp)
    return "OK"


if __name__ == '__main__':
    app.run()
