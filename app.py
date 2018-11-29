from flask import Flask,request, json
from flask import render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
import recastai
import os
import pdb


app = Flask(__name__)
app.config['DEBUG'] = True

# DB
Base = automap_base()
engine = create_engine('postgresql+psycopg2://root:rootroot@testdbinstance.cjgud0fxglke.us-east-1.rds.amazonaws.com:5432/insurance_info')
Base.prepare(engine, reflect=True)
Insurance = Base.classes.insurances
session = Session(engine)

# DB

RECAST_REQUEST_TOKEN = os.environ.get("API_REQUEST_TOKEN", default=None)
RECAST_DEVELOPER_TOKEN = os.environ.get("API_DEVELOPER_TOKEN", default=None)

@app.route('/')
def hello():
    insurances = session.query(Insurance).all()
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
    insuranceData = session.query(Insurance).filter_by(policy_number='EBU097711156').first()
    return "test"



if __name__ == '__main__':
    app.run()
