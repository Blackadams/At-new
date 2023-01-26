# works with both python 2 and 3
from __future__ import print_function
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from heyoo import WhatsApp
from log import post_logger, logger
import json
from utils import MobileWallet
from datetime import datetime

application = Flask(__name__)

Token = 'EAAM6OPcHa5EBAFbGWLvrZAmmipboHL3ZBIMy4FmAZBqs4tW8gzA3PfnkxibQnA9SJKG3DU16gIgRTRARgNbbDjN06N0Q1WashMd1pHxvsacm1mCwSz9YgIOqlZBqkRGCJ7IkHZCSkXqoaPZBM1A7cwUlp77xZCJZAQa2u3aAypYOYJFjJmFZAvmwq0ZCaVdv4stzaPiDJR9bn242zn6TRZAlV2K'

messenger = WhatsApp(Token, phone_number_id='105441719125872')

VERIFY_TOKEN = "30cca545-3838-48b2-80a7-9e43b1ae8ce4"


application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///conversations.db"

db = SQLAlchemy(application)

class IncomingRequest(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    status = db.Column(db.String(255))
    timestamp = db.Column(db.String(255))
    recipient_id = db.Column(db.String(255))
    conversation_id = db.Column(db.String(255))
    message_id = db.Column(db.String, unique=True)
    expiration_timestamp = db.Column(db.String(255))
    origin = db.Column(db.String(255))
    billable = db.Column(db.String(255))
    pricing_model = db.Column(db.String(255))
    processed = db.Column(db.Boolean, default=False)
   

    def __init__(self, status, timestamp, recipient_id, conversation_id, message_id, origin, billable, pricing_model, processed):

        self.status = status
        self.timestamp = timestamp
        self.recipient_id = recipient_id
        self.conversation_id = conversation_id
        self.message_id = message_id
        self.origin = origin
        self.billable = billable
        self.pricing_model = pricing_model
        self.processed = processed



def save_request(data):


        # Extract the conversation_id and message_id from the data
        conversation_id = data['entry'][0]['changes'][0]['value']['statuses'][0]['conversation']['id'] #c1b63a1655a036852a22a89da7fb908a
        # message_id = messenger.get_message_id(data)
        message_id = data['entry'][0]['changes'][0]['value']['statuses'][0]['id'] #wamid.HBgMMjU0NzQxNTkwMzMwFQIAERgSMTZCMjIzOTlEMjVFQTE2MjUyAA==
        
        
        # Check if a request with the same conversation_id and message_id already exists in the database
        request_exists = IncomingRequest.query.filter_by(conversation_id=conversation_id, id=message_id).first()

        if request_exists:
            logging.info("Incoming request already exists in the database")
        else:

            try:            
                status = data['entry'][0]['changes'][0]['value']['statuses'][0]['status'] #sent
                timestamp = data['entry'][0]['changes'][0]['value']['statuses'][0]['timestamp'] #1674635192
                recipient_id = data['entry'][0]['changes'][0]['value']['statuses'][0]['recipient_id'] #254716434058 
                origin = data['entry'][0]['changes'][0]['value']['statuses'][0]['conversation']['origin']['type'] #user_initiated
                billable = data['entry'][0]['changes'][0]['value']['statuses'][0]['pricing']['billable'] #True
                pricing_model = data['entry'][0]['changes'][0]['value']['statuses'][0]['pricing']['pricing_model'] #CBP

        
                new_request = IncomingRequest(status=status, timestamp=timestamp, recipient_id=recipient_id, conversation_id=conversation_id, message_id=message_id, origin=origin, billable=billable, pricing_model=pricing_model, processed=False)
                db.session.add(new_request)
                db.session.commit()             

            except Exception as e:
                logger.exception(e)

        return 'ok'

def check_message_processed(message_id):
    processed = IncomingRequest.query.filter_by(message_id=message_id, processed=True).first()
    return True if processed else False




@application.before_request
def log_request():
    try:
        if request.method == 'POST':

            # Log the incoming request
            post_logger.info(f"Incoming request: {request.url} {request.method} {request.data}")

            # Store the incoming request to variable data
            data = request.get_json()

            # Store the incoming request to database
            save_request(data)

        else:
            pass
    except Exception as e:
        pass

    
@application.route('/', methods=['GET'])
def index():
    conversations = IncomingRequest.query.all()
    return render_template('conversation.html', conversations=conversations)


@application.route('/heyoo',methods=['GET','POST'])
def heyoo():

    # complicated
    if request.method == "GET":
        if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
            if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
                return "Verification token mismatch", 403
            return request.args["hub.challenge"], 200

    data = request.get_json()


    changed_field = messenger.changed_field(data)
   
    if changed_field == 'messages':

        new_message = messenger.get_mobile(data)
     
        if new_message:

            mobile = messenger.get_mobile(data)
            message_type = messenger.get_message_type(data)
            name1 = messenger.get_name(data)
            name=name1.capitalize()

         
            if message_type == "text":

                message = messenger.get_message(data).lower()

                print(f"{mobile} sent {message}")


                message_id = messenger.get_message_id(data)

                true_id = f'{message_id}=='
              


                # try:

                #     messenger.send_message(f"Hi {name} what service would you like today?\n\n1 - Open account\n\n💡type *1* to make your selection 👇🏾", mobile)
                # except Exception as e:
                #     logger.exception(e)

                if "Hi" == message:

                    if not check_message_processed(true_id):
                        print(f"{mobile} sent {message}")
                        try:
                            messenger.send_message(f"Hi *{name}* what service would you like today?\n\n1 - *Top-up account*\n2 - *Check Balance*\n3 - *Top-up airtime*\n4 - *About Us*\n\n💡type *1 - 4* to make your selection below 👇🏾", mobile)

                            #Mark the message as processed
                            processed_message = IncomingRequest.query.filter_by(message_id=message_id,  processed=False).first()
                            processed_message.processed = True
                            db.session.commit()

                            print('ookkkkk')
                           
                        except Exception as e:
                            logger.exception(e)
                    else:
                        print(f"{mobile} sent {message} but it's already processed.")

                elif "1" == message:

                    if not check_message_processed(true_id):
                        print(f"{mobile} sent {message}")
                        try:
                            messenger.send_message(f"Hi *{name}* Top-up successful 👍", mobile)

                            #Mark the message as processed
                            processed_message = IncomingRequest.query.filter_by(message_id=message_id,  processed=False).first()
                            processed_message.processed = True
                            db.session.commit()

                            print('ookkkkk')
                           
                        except Exception as e:
                            logger.exception(e)
                    else:
                        print(f"{mobile} sent {message} but it's already processed.")
                    print('duplicate')

                elif "2" == message:

                    if not check_message_processed(true_id):
                        print(f"{mobile} sent {message}")
                        try:
                            balance = 2
                            messenger.send_message(f"Hi *{name.capitalize()}* Balance for account is *{balance} KSH*", mobile)
                            #Mark the message as processed
                            processed_message = IncomingRequest.query.filter_by(message_id=message_id,  processed=False).first()
                            processed_message.processed = True
                            db.session.commit()

                            print('ookkkkk')
                           
                        except Exception as e:
                            logger.exception(e)
                    else:
                        print(f"{mobile} sent {message} but it's already processed.")
                    print('duplicate')

                elif "3" == message:

                    amount = 5

                    if not check_message_processed(true_id):
                        print(f"{mobile} sent {message}")
                        try:
                            messenger.send_reply_button(
                                recipient_id=mobile,
                                button={
                                    "type": "button",
                                    "body": {
                                        "text": f"Hi {name.capitalize()} top-up {amount} KSH airtime to {mobile}?"
                                    },
                                    "action": {
                                        "buttons": [
                                            {
                                                "type": "reply",
                                                "reply": {
                                                    "id": "b2",
                                                    "title": "Confirm"
                                                }
                                            },
                                            {
                                                "type": "reply",
                                                "reply": {
                                                    "id": "b3",
                                                    "title": "Change Number"
                                                }
                                            },
                                        
                                        ]
                                    }
                              },
                            )
                            #Mark the message as processed
                            processed_message = IncomingRequest.query.filter_by(message_id=message_id,  processed=False).first()
                            processed_message.processed = True
                            db.session.commit()

                            print('ookkkkk')
                           
                        except Exception as e:
                            logger.exception(e)
                    else:
                        print(f"{mobile} sent {message} but it's already processed.")
                    print('duplicate')

                elif "4" == message:

                    if not check_message_processed(true_id):
                        print(f"{mobile} sent {message}")
                        try:
                            messenger.send_reply_button(
                                recipient_id=mobile,
                                button={
                                    "type": "button",
                                    "body": {
                                        "text": "About Us\n\nWelcome to Bankify, where we specialize in creating innovative solutions.\n\nOne of our flagship products is a savings wallet chatbot that allows customers to save money in their accounts, which is then used to purchase airtime and resell it.\n\nThe interest earned from this process is shared with the customer's savings account, providing a unique and convenient way for individuals to manage their finances."
                                    },
                                    "action": {
                                        "buttons": [
                                            {
                                                "type": "reply",
                                                "reply": {
                                                    "id": "b1",
                                                    "title": "Return to main menu"
                                                }
                                            },
                                        
                                        ]
                                    }
                              },
                            )
                            #Mark the message as processed
                            processed_message = IncomingRequest.query.filter_by(message_id=message_id,  processed=False).first()
                            processed_message.processed = True
                            db.session.commit()

                            print('ookkkkk')
                           
                        except Exception as e:
                            logger.exception(e)
                    else:
                        print(f"{mobile} sent {message} but it's already processed.")
                    print('duplicate')

                else:
                    print('duplicate')


                if message.startswith("+254"):

                    true_id = f'{message_id}=='

                    if not check_message_processed(true_id):

                
                        try:
                            # wallet = MobileWallet()
                            # wallet.topup(f"+{mobile}", f"{amount}", "KES")

                            amount = 5

                            messenger.send_reply_button(
                                recipient_id=mobile,
                                button={
                                    "type": "button",
                                    "body": {
                                        "text": f"Hi {name.capitalize()} top-up {amount} KSH airtime to {message}?"
                                    },
                                    "action": {
                                        "buttons": [
                                            {
                                                "type": "reply",
                                                "reply": {
                                                    "id": "b2",
                                                    "title": "Confirm"
                                                }
                                            },
                                           
                                        
                                        ]
                                    }
                              },
                            )
                            #Mark the message as processed
                            processed_message = IncomingRequest.query.filter_by(message_id=message_id,  processed=False).first()
                            processed_message.processed = True
                            db.session.commit()

                            print('ookkkkk')
                           
                        except Exception as e:
                            logger.exception(e)
                    else:
                        print(f"{mobile} sent {message} but it's already processed.")




                    

            elif message_type == "interactive":

                message_response = messenger.get_interactive_response(data)
                intractive_type = message_response.get("type")
                message_id = message_response[intractive_type]["id"]
                message_text = message_response[intractive_type]["title"]

                # logging.info(f"Interactive Message; {message_id}: {message_text}")

                if "b1" in message_id:

                    true_id = f'{message_id}=='

                    if not check_message_processed(true_id):
                
                        try:
                            messenger.send_message(f"Hi *{name}* what service would you like today?\n\n1 - *Top-up account*\n2 - *Check Balance*\n3 - *Top-up airtime*\n4 - *About Us*\n\n💡type *1 - 4* to make your selection below 👇🏾", mobile)

                            #Mark the message as processed
                            processed_message = IncomingRequest.query.filter_by(message_id=message_id,  processed=False).first()
                            processed_message.processed = True
                            db.session.commit()

                            print('ookkkkk')
                           
                        except Exception as e:
                            logger.exception(e)
                    else:
                        print(f"{mobile} sent {message} but it's already processed.")

                if "b2" in message_id:

                    true_id = f'{message_id}=='

                    if not check_message_processed(true_id):

                        amount = 5
                
                        try:
                            wallet = MobileWallet()
                            wallet.topup(f"+{mobile}", f"{amount}", "KES")

                            messenger.send_message(f"Hi *{name.capitalize()}* recharge of *{amount} KSH* to *{mobile}* was successful 👍", mobile)
                          
                            #Mark the message as processed
                            processed_message = IncomingRequest.query.filter_by(message_id=message_id,  processed=False).first()
                            processed_message.processed = True
                            db.session.commit()

                            print('ookkkkk')
                           
                        except Exception as e:
                            logger.exception(e)
                    else:
                        print(f"{mobile} sent {message} but it's already processed.")

                if "b3" in message_id:

                    true_id = f'{message_id}=='

                    if not check_message_processed(true_id):

                
                        try:
                            # wallet = MobileWallet()
                            # wallet.topup(f"+{mobile}", f"{amount}", "KES")

                            messenger.send_message(f"Please enter the *recipient number*\n\n💡 use format *+2547******** to make your selection below 👇🏾", mobile)
                          
                            #Mark the message as processed
                            processed_message = IncomingRequest.query.filter_by(message_id=message_id,  processed=False).first()
                            processed_message.processed = True
                            db.session.commit()

                            print('ookkkkk')
                           
                        except Exception as e:
                            logger.exception(e)
                    else:
                        print(f"{mobile} sent {message} but it's already processed.")

            else:

                print(f"{mobile} sent {message_type} ")
                # logging.info(f"{mobile} sent {message_type}")

        else:

            delivery = messenger.get_delivery(data)

            if delivery:
                print(f"Message : {delivery}")
            else:
                print("No new message")
                
    return "ok"

if __name__ == '__main__':

    with application.app_context():
        db.create_all()
    application.run(port=4000)

