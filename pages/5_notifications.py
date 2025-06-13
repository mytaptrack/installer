import streamlit as st

st.set_page_config(page_title="Mytaptrack Installer", page_icon="./favicon.ico", layout="wide")

import boto3
import json

from components.utils import bottom_bar
from components.auth import auth_check
auth_check()
from components.utils import apply_styles
apply_styles()

from components.html_resources import link

ses = boto3.client('ses')
sns = boto3.client('sns')
secretsmanager = boto3.client('secretsmanager')
chatbot = boto3.client('chatbot')

region = st.session_state['config']['env']['region']['primary']

st.write('### Notifications')

if st.checkbox("Use Push Notifications", value= st.session_state['config']['env']['app']['pushSnsArns']['android'] != '' or st.session_state['config']['env']['app']['pushSnsArns']['ios'] != ''):
    st.session_state['config']['env']['app']['pushSnsArns']['android'] = st.text_input('Android SNS Topic Arn')
    if st.session_state['config']['env']['app']['pushSnsArns']['android']:
        # Verify the SNS topic exists and print exception if it fails
        try:
            sns.get_topic_attributes(
                TopicArn=st.session_state['config']['env']['app']['pushSnsArns']['android']
            )
            st.success('Android SNS Topic found')
        except Exception as e:
            st.error('Android SNS Topic not found')
            print(e)
    else:
        pass

    st.session_state['config']['env']['app']['pushSnsArns']['ios'] = st.text_input('IOS SNS Topic Arn')
    if st.session_state['config']['env']['app']['pushSnsArns']['ios']:
        # Verify the SNS topic exists and print exception if it fails
        try:
            sns.get_topic_attributes(
                TopicArn=st.session_state['config']['env']['app']['pushSnsArns']['ios']
            )
            st.success('IOS SNS Topic found')
        except Exception as e:
            st.error('IOS SNS Topic not found')
            print(e)
    else:
        pass
    
    link('AWS SNS Console', f'https://{region}.console.aws.amazon.com/sns/v3/home?region={region}#/mobile/push-notifications')
else:
    st.session_state['config']['env']['app']['pushSnsArns']['android'] = ''
    st.session_state['config']['env']['app']['pushSnsArns']['ios'] = ''

if st.checkbox("Use email", value= st.session_state['config']['env']['system']['email'] != ''):
    st.session_state['config']['env']['system']['email'] = st.text_input('Email to use for notifications')

    if st.session_state['config']['env']['system']['email']:
        # Check to see if the email is verified
        st.button("Refresh verification status")
        try:
            email_result = ses.get_identity_verification_attributes(
                Identities=[
                    st.session_state['config']['env']['system']['email']
                ]
            )
            if email_result['VerificationAttributes'][st.session_state['config']['env']['system']['email']]['VerificationStatus'] != 'Success':
                print(f"Email Result: {email_result}")
                st.error('Email not verified')

                if st.button('Send verification Email'):
                    email_result = ses.verify_email_identity(
                        EmailAddress=st.session_state['config']['env']['system']['email']
                    )
                    print('Email Result')
                    print(email_result)
                    st.success('Email verified')
            else:
                st.success('Email verified')
            
            # Check to see if email in sandbox mode
            email_result = ses.get_account_sending_enabled()
            if email_result['Enabled']:
                st.error('Email in sandbox mode. Only verified emails can be sent to currently.')
                link('AWS SES Get Set Up', f'https://{region}.console.aws.amazon.com/ses/home?region={region}#/get-set-up')
        except Exception as e:
            print(f"Email Error: {e}")
            st.error('Email not verified')
            if st.button('Send verification Email'):
                email_result = ses.verify_email_identity(
                    EmailAddress=st.session_state['config']['env']['system']['email']
                )
                print('Email Result')
                print(email_result)
                st.success('Email verified')

else:
    st.session_state['config']['env']['system']['email'] = ''

twilio_secret = None

# Try to get twilio secret
try:
    twilio_secret = secretsmanager.get_secret_value(
        SecretId=f'twilio/authToken'
    )['SecretString']
    twilio_secret = json.loads(twilio_secret)
except Exception as e:
    print(f"Twilio Error: {e}")
    twilio_secret = None

if st.checkbox("Use twilio for sending text messages", value= twilio_secret != None):
    account_sid = st.text_input('Enter your twilio account sid', value=twilio_secret['accountSid'])
    auth_token = st.text_input('Enter your twilio auth token', type='password', value=twilio_secret['authToken'])
    phone = st.text_input('Enter your twilio origination phone number', value=twilio_secret['phone'])
    
    if st.session_state['config']['env']['sms']['origin'] and st.session_state['config']['env']['sms']['accountSid'] and auth_token:
        # Set secrets manager value
        secret_value = json.dumps({
            'accountSid': account_sid,
            'authToken': auth_token,
            'phone': phone
        })
        try:
            result = secretsmanager.put_secret_value(
                SecretId=f'twilio/authToken',
                SecretString=secret_value
            )
            st.session_state['config']['env']['sms']['arn'] = result['ARN']
            st.success('Auth token set')
        except:
            result = secretsmanager.create_secret(
                Name=f'twilio/authToken',
                SecretString=secret_value
            )
            st.session_state['config']['env']['sms']['arn'] = result['ARN']
            st.success('Auth token created')
        st.session_state['config']['env']['sms']['secret'] = 'twilio/authToken'
    else:
        # see if the 'twilio/authToken' secret exists
        if twilio_secret:
            # Delete the secret
            secretsmanager.delete_secret(
                SecretId=f'twilio/authToken',
                ForceDeleteWithoutRecovery=True
            )
            st.success('Auth token deleted')
else:
    st.session_state['config']['env']['sms']['secret'] = ''

st.write('Chatbots are useful when supporting mytaptrack as errors and specific alerts can be sent to the chatbot')
if st.checkbox("Use chatbot messaging", value= st.session_state['config']['env']['chatbot'] is not None ):
    st.session_state['config']['env']['chatbot'] = {
        'arn': st.text_input('Enter the chatbot arn')
    }
else:
    st.session_state['config']['env']['chatbot'] = None

bottom_bar('./pages/4_encryption.py', './pages/6_general.py')
