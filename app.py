from flask import Flask,request, json
from flask import render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
import recastai
import os
import requests
import pdb

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
    return render_template('index.html')

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
    # SAMPLE DATA
    # data = {
    #     "action_id": "5149f96e-b2c5-4e30-96ec-c587ae978d52",
    #     "conversation": {
    #         "id": '1f4b092a-8837-4944-b467-f495216e34d5',
    #         "language": "en",
    #         "memory": {},
    #         "participant_data": {},
    #         "skill": "foo",
    #         "skill_occurences": 2,
    #         "skill_stack": []
    #     },
    #     "nlp": {
    #         "act": "assert",
    #         "entities": {},
    #         "intents": [],
    #         "language": "en",
    #         "processing_language": "en",
    #         "sentiment": "neutral",
    #         "source": "This is a sample message.",
    #         "status": 200,
    #         "timestamp": "2018-06-29T22:00:50.591367+00:00",
    #         "type" : "",
    #         "uuid": "c1bc4e40-ca14-4ce2-bc18-700433b001d9",
    #         "version": "2.12.0"
    #     }
    # }
    print(request.args)

    # conversationId = data["conversation"]["id"]
    # insuranceData = session.query(Insurance).filter_by(policy_number='EBU097711156').first()
    # response = sendMessageToUser(insuranceData,conversationId)
    return "response"


# def sendMessageToUser(data, convId):
#     responseMessageObj = [{
#         "type": "text",
#         "content": f"Your policy number is {data.policy_number}"
#     },{
#         "type": "text",
#         "content": f"Your policy name is {data.account_name}"
#     },{
#         "type": "text",
#         "content": f"Your policy premium is {data.premium}"
#     },{
#         "type": "text",
#         "content": f"Your policy Expiration date is {data.expiration_date}"
#     }]
#
#     message_sent_response = requests.post(f'https://api.recast.ai/connect/v1/conversations/{convId}/messages',
#             headers={'Authorization': f'Token {RECAST_DEVELOPER_TOKEN}'},
#             json={"messages": responseMessageObj}
#     )
#     return "OK"


if __name__ == '__main__':
    app.run()
