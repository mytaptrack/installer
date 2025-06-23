import streamlit as st

st.set_page_config(page_title="Mytaptrack Installer", page_icon="./favicon.ico", layout="wide")

import json
import boto3
from components.auth import auth_check
auth_check()
from components.utils import apply_styles
apply_styles()

# Create cognito user pool client
cognito = boto3.client('cognito-idp', config=st.session_state['b3config'])
dynamodb = boto3.client('dynamodb', config=st.session_state['b3config'])

def get_users_from_pool(stage: str):
    # Get user pool id from pool name
    user_pool_name = f"mytaptrack-{stage}-user-pool"
    
    # Get user pools
    user_pools = cognito.list_user_pools(MaxResults=60)['UserPools']
    matching_pools = [pool for pool in user_pools if pool['Name'] == user_pool_name]
    
    if not matching_pools:
        st.error(f"No user pool found with name: {user_pool_name}")
        return
        
    user_pool_id = matching_pools[0]['Id']
    st.write('Found Cognito User Pool')

    # Get users
    users = cognito.list_users(UserPoolId=user_pool_id)['Users']
    st.write('Found Cognito Users')
    print(f"Cognito Users: {users}")
    return users
    
if st.button("Export users"):
    # Get user pool id from pool name
    users = get_users_from_pool(stage)

    # Construct a list of email addresses and usernames
    user_data = []
    for user in users:
        # find the attribute named email
        email = [attr['Value'] for attr in user['Attributes'] if attr['Name'] == 'email'][0]
        user_data.append({
            'email': email,
            'username': user['Username']
        })
    
    # Download this list as a csv
    st.download_button(
        label="Download user data",
        data="\n".join([f'{user['email']},{user['username']}' for user in user_data]),
        file_name="user_data.csv",
        mime="text/csv"
    )

# User will upload a zip file with data to import
uploaded_file = st.file_uploader("Upload data package", type=["zip"])

if uploaded_file is not None:
    # Save the uploaded file to the file system
    with open("data.zip", "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Unzip the file
    import zipfile
    with zipfile.ZipFile("data.zip", "r") as zip_ref:
        zip_ref.extractall("data")

    user_lookup = []
    # Extract user_data.csv and create a lookup dict
    with open("data/user_data.csv", "r") as f:
        user_data = [line.strip().split(",") for line in f.readlines()]
        
        # For each line in the file, create a dict with email and username
        user_data = [{ 'email': line[0], 'previous_id': line[1]} for line in user_data]

        # Get all users from the user pool
        users = get_users_from_pool(stage)

        # For each user in the user pool, if the email is in the lookup dict, update the username
        for user in users:
            # find the attribute named email
            email = [attr['Value'] for attr in user['Attributes'] if attr['Name'] == 'email'][0]
            
            # Find user in user_data
            user_data_line = [line for line in user_data if line['email'] == email]

            # If user data result found, add to user_lookup
            if user_data_line:
                user_lookup.append({
                    'new_id': user['Username'],
                    'old_id': user_data_line[0]['previous_id'],
                    'email': email,
                    'old_u': f"U#{user_data_line[0]['previous_id']}",
                    'new_u': f"U#{user['Username']}"
                })

    # Extract data.json and convert each line to a dict
    with open("data/data.json", "r") as f:
        data = [json.load(line) for line in f.readlines()]

        # Add each line to the dynamodb table mytaptrack-{stage}-data
        table_name = f"mytaptrack-{stage}-data"

        # Get the table
        table = dynamodb.Table(table_name)

        # Add each line to the table
        for line in data:
            # Check for pk has user_data old_u
            for user in user_lookup:
                # Check if pk has old_u in it
                if user['old_u'] in line['pk']:
                    # Replace old_u with new_u
                    line['pk'] = line['pk'].replace(user['old_u'], user['new_u'])
                if user['old_u'] in line['sk']:
                    # Replace old_u with new_u
                    line['sk'] = line['sk'].replace(user['old_u'], user['new_u'])

                if user['old_id'] == line['generatingUserId']:
                    line['generatingUserId'] = user['new_id']
                
                if user['old_id'] == line['userId']:
                    line['userId'] = user['new_id']
                
                if user['old_u'] in line['tsk']:
                    # Replace old_u with new_u
                    line['tsk'] = line['tsk'].replace(user['old_u'], user['new_u'])
                
            table.put_item(Item=line)

    # Extract data from primary.json with each line being a json object
    with open("data/primary.json", "r") as f:
        data = [json.load(line) for line in f.readlines()]

        # Add each line to the dynamodb table mytaptrack-{stage}-data
        table_name = f"mytaptrack-{stage}-primary"

        # Get the table
        table = dynamodb.Table(table_name)

        # Add each line to the table
        for line in data:
            # Check for pk has user_data old_u
            for user in user_lookup:
                # Check if pk has old_u in it
                if user['old_u'] in line['pk']:
                    # Replace old_u with new_u
                    line['pk'] = line['pk'].replace(user['old_u'], user['new_u'])
                if user['old_u'] in line['sk']:
                    # Replace old_u with new_u
                    line['sk'] = line['sk'].replace(user['old_u'], user['new_u'])

                if user['old_id'] == line['generatingUserId']:
                    line['generatingUserId'] = user['new_id']

                if user['old_id'] == line['userId']:
                    line['userId'] = user['new_id']

                if user['old_u'] in line['tsk']:
                    # Replace old_u with new_u
                    line['tsk'] = line['tsk'].replace(user['old_u'], user['new_u'])

            table.put_item(Item=line)

    # Delete the zip file
    import os
    os.remove("data.zip")
    os.remove("data/user_data.csv")
    os.remove("data/data.json")
    os.remove("data/private.json")
    os.rmdir("data")
