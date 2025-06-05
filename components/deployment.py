import streamlit as st
import boto3
import yaml
import os

import time

from components.html_resources import link

codebuild = boto3.client('codebuild')

# Create AWS codestar client
codestar = boto3.client('codeconnections')

def deployment_ui():
    if 'deploy' not in st.session_state['config']['env']:
        st.session_state['config']['env']['deploy'] = {
            'website': False,
            'auto': False
        }

    st.session_state['config']['env']['deploy']['website'] = st.checkbox('Deploy website with public access', value=st.session_state['config']['env']['deploy']['website'])
    st.session_state['config']['env']['deploy']['auto'] = st.checkbox('When mytaptrack github has updates, automatically deploy updates', st.session_state['config']['env']['deploy']['auto'])

    st.button('Refresh')
    # Check to see if there is a codestar github connection
    connections = codestar.list_connections()['Connections']
    # Find a connection to github
    git_connection_found = False
    for connection in connections:
        if connection['ProviderType'] == 'GitHub':
            git_connection_found = True
            st.success('Github connection found')
            break

    if not git_connection_found:
        st.error('No github connection found')
        primary = st.session_state['config']['env']['region']['primary']
        st.write('You need to create a connection to github and authenticate with your account')
        link('CodeStar', f'https://{primary}.console.aws.amazon.com/codesuite/settings/connections/create?origin=settings&region={primary}')
        st.stop()

def deploy_codebuild(stage: str):
    # Check if the backend pipeline stack is already present
    pipeline_stack_name = f'mytaptrack-{stage}-back-end'
    stack_found = False
    codebuild_projects = codebuild.list_projects()['projects']
    for project in codebuild_projects:
        print(f'Project: {project} ?? {pipeline_stack_name}')
        if project == pipeline_stack_name:
            st.success('Backend codebuild project found')
            stack_found = True
            break

    def deploy_codebuild():
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
            st.success('Deployment successful')
        else:
            st.error('Deployment failed')

    st.write('Make sure to save before deploying')

    if not stack_found:
        print(f'Projects: {codebuild_projects}')
        if st.button('Deploy'):
            deploy_codebuild()
    else:
        if st.button('Update Build'):
            deploy_codebuild()

    if stack_found and st.button('Run Pipeline'):
        # Run the codebuild project
        st.write('Running deployment')

        # Get the project name
        build_response = codebuild.start_build(projectName=pipeline_stack_name)

        # Poll status of build until its done
        build_id = build_response['build']['id']
        build_status = 'IN_PROGRESS'

        while build_status == 'IN_PROGRESS':
            build_status = codebuild.batch_get_builds(ids=[build_id])['builds'][0]['buildStatus']
            print(f"Build status: {build_status}")
            time.sleep(5)
        
        if build_status == 'SUCCEEDED':
            st.success('Deployment successful')
        else:
            st.error('Deployment failed')
