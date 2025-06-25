import streamlit as st

st.set_page_config(page_title="Mytaptrack Installer", page_icon="./favicon.ico", layout="wide")

import boto3
import yaml
import os
import time

from components.utils import bottom_bar
from components.html_resources import link
from components.auth import auth_check
auth_check()
from components.utils import apply_styles
apply_styles()

codebuild = boto3.client('codebuild', config=st.session_state['b3config'])
codepipeline = boto3.client('codepipeline', config=st.session_state['b3config'])

st.write('### Deploy the system')

def deploy_codebuild(stage: str):
    # Set stage
    os.environ['STAGE'] = stage

    # Save configuration file to ./cicd in the file system
    st.write('Setting up config file')
    with open('./cicd/config.yml', 'w') as f:
        f.write(yaml.dump(st.session_state['config']))

    st.write('Bootstrapping CDK environment')
    install_result = os.system('cd ./cicd && cdk bootstrap')
    
    st.write('Setting up deployment pipeline for mytaptrack back end')
    # In the ./cicd subdirectory run npm deploy
    install_result = os.system('cd ./cicd && npm run deploy -- --require-approval never')

    # Check if the install was successful
    if install_result == 0:
        st.success('Build pipeline created')
    else:
        st.error('Build pipeline  failed')

# Check if the backend pipeline stack is already present
stage = st.session_state['config']['env']['name']
pipeline_stack_name = f'mytaptrack-{stage}'
stack_found = False
build_pipelines = codepipeline.list_pipelines()['pipelines']
pipeline = None
for project in build_pipelines:
    print(f'Project: {project} ?? {pipeline_stack_name}')
    if project['name'] == pipeline_stack_name:
        st.success('Backend codebuild project found')
        stack_found = True
        pipeline = project
        break

st.write('Make sure to save before deploying')

if not stack_found:
    print(f'Projects: {build_pipelines}')
    if st.button('Create build pipeline', key=f'deploybuildpipeline{stage}', icon=":material/build:"):
        # Write to ./config.yml
        with open('./cicd/config.yml', 'w') as f:
            yaml.dump(st.session_state['config'], f)
        deploy_codebuild(stage)
else:
    if st.button('Update build pipeline', key=f'updatebuildpipeline{stage}', icon=":material/build:"):
        # Write to ./config.yml
        with open('./cicd/config.yml', 'w') as f:
            yaml.dump(st.session_state['config'], f)
        deploy_codebuild(stage)

stack_found = False
build_pipelines = codepipeline.list_pipelines()['pipelines']
pipeline = None
for project in build_pipelines:
    print(f'Project: {project} ?? {pipeline_stack_name}')
    if project['name'] == pipeline_stack_name:
        st.success('Backend codebuild project found')
        stack_found = True
        pipeline = project
        break

if stack_found and st.button('Run Pipeline', icon=":material/play_arrow:"):
    # Run the codebuild project
    st.write('Running deployment')

    # Get the project name
    build_response = codepipeline.start_pipeline_execution(name=pipeline_stack_name)

    # Poll status of build until its done
    build_id = build_response['pipelineExecutionId']
    build_status = 'InProgress'
    print(f'Build Id {build_id}')

    time.sleep(5)

    while build_status == 'InProgress':
        build_status = codepipeline.get_pipeline_execution(pipelineName=pipeline_stack_name, pipelineExecutionId=build_id)['pipelineExecution']['status']
        print(f"Build status: {build_status}")
        time.sleep(5)
    
    if build_status == 'Succeeded':
        st.success('Deployment successful')
    else:
        st.error('Deployment failed')

cloudformation = boto3.client('cloudformation', config=st.session_state['b3config'])
try:
    stack = cloudformation.describe_stacks(StackName=f'mytaptrack-{stage}')
    if stack['Stacks'][0]['StackStatus'] in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
        st.success('Deployment stack found')
        print(f"Stack output: {stack['Stacks'][0]['Outputs']}")

        # Get BehaviorWebsiteStackOutput
        behavior_website_output = [output for output in stack['Stacks'][0]['Outputs'] if output['OutputKey'] == 'BehaviorWebsiteStackOutput'][0]['OutputValue']
        if behavior_website_output:
            link("Behavior Website", behavior_website_output)
        
        # Get ManagementWebsiteStackOutput
        management_website_output = [output for output in stack['Stacks'][0]['Outputs'] if output['OutputKey'] == 'ManagementWebsiteStackOutput'][0]['OutputValue']
        if management_website_output:
            link("Management Website", management_website_output)

    st.divider()
except Exception as e:
    print(f"Error: {e}")
    st.write('Deployment stack not found')

if st.button('Remove installer (Save Money)', type='tertiary', icon=':material/delete:'):
    # Delete the installer stack
    cloudformation = boto3.client('cloudformation', config=st.session_state['b3config'])
    cloudformation.delete_stack(StackName=f'mytaptrack-installer')
st.write("""Removing the installer does not mean you can't reinstall it and continue where you left off. 
         All this does is remove the active components which cost money to run and are not necessary for mytaptrack to operate.""")

bottom_bar('deploy')
