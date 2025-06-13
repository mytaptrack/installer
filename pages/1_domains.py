import streamlit as st

st.set_page_config(page_title="Mytaptrack Installer", page_icon="./favicon.ico", layout="wide")

import boto3
from components.html_resources import link
from components.utils import generate_api_key
from components.utils import bottom_bar
from components.auth import auth_check
auth_check()
from components.utils import apply_styles
apply_styles()

route53 = boto3.client('route53')
acm = boto3.client('acm')

st.write('### DNS')

if st.checkbox('Use Route53', value=st.session_state['config']['env']['domain']['name'] != ''):
    domain = st.text_input('Enter the route 53 domain name', value=st.session_state['config']['env']['domain']['name'])
    if domain:
        # Remove spaces before and after domain
        domain = domain.strip()

        st.session_state['config']['env']['domain']['name'] = domain
        hosted_zones = route53.list_hosted_zones()['HostedZones']
        print(f"Hosted Zones: {hosted_zones}")
        route53_name = domain + '.'
        print(f"Domain: {route53_name}")
        for zone in hosted_zones:
            print(f'Zone: "{zone['Name']}" check agains "{route53_name}"')
            if route53_name == zone['Name']:
                print(f"Found hosted zone: {zone['Name']}")
                st.session_state['config']['env']['domain']['hostedzone']['id'] = zone['Id'].split('/')[2]
                break
        
        if not st.session_state['config']['env']['domain']['hostedzone']['id']:
            st.error('Domain hosted zone not found in route 53')
        else:
            st.success('Domain found in route 53')

        # Check certificate manager for a wildcard certificate
        certificates = acm.list_certificates()['CertificateSummaryList']
        print(certificates)
        for cert in certificates:
            if domain in cert['DomainName']:
                if cert['Status'] == 'ISSUED':
                    st.success('Certificate found')
                    st.session_state['config']['env']['domain']['sub']['api']['cert'] = cert['CertificateArn']
                    st.session_state['config']['env']['domain']['sub']['device']['cert'] = cert['CertificateArn']
                else:
                    st.error('Certificate not issued')
                    link('AWS Certificate Manager', f'https://{st.session_state['config']['env']['region']['primary']}.console.aws.amazon.com/acm/home')
                break
        
        if not st.session_state['config']['env']['domain']['sub']['api']['cert']:
            st.error('Certificate not found in certificate manager')
            
            if st.button('Create Certificate'):
                # Create certificate
                response = acm.request_certificate(
                    DomainName=domain,
                    ValidationMethod='DNS',
                    SubjectAlternativeNames=[domain, '*.' + domain]
                )
                st.session_state['config']['env']['domain']['sub']['api']['cert'] = response['CertificateArn']
                st.session_state['config']['env']['domain']['sub']['device']['cert'] = response['CertificateArn']

                # Check if certificate has been validated
                response = acm.describe_certificate(CertificateArn=response['CertificateArn'])
                if response['Certificate']['Status'] != 'ISSUED':
                    # Add route53 records
                    for record in acm.describe_certificate(CertificateArn=response['CertificateArn'])['Certificate']['DomainValidationOptions']:
                        route53.change_resource_record_sets(
                            HostedZoneId=st.session_state['config']['env']['domain']['hostedzone']['id'],
                            ChangeBatch={
                                'Changes': [
                                    {
                                        'Action': 'UPSERT',
                                        'ResourceRecordSet': {
                                            'Name': record['ResourceRecord']['Name'],
                                            'Type': record['ResourceRecord']['Type'],
                                            'TTL': 300,
                                            'ResourceRecords': [
                                                {
                                                    'Value': record['ResourceRecord']['Value']
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        )

                st.success('Certificate created')

        st.divider()
        if not st.session_state['config']['env']['domain']['sub']['api']['subdomain']:
            st.session_state['config']['env']['domain']['sub']['api']['subdomain'] = 'api'
        st.session_state['config']['env']['domain']['sub']['api']['subdomain'] = st.text_input('Enter the api subdomain', value=st.session_state['config']['env']['domain']['sub']['api']['subdomain'])
        st.session_state['config']['env']['domain']['sub']['api']['name'] = f"{st.session_state['config']['env']['domain']['sub']['api']['subdomain']}.{st.session_state['config']['env']['domain']['name']}"
        st.session_state['config']['env']['domain']['sub']['api']['path'] = st.text_input('Enter the api path', value=st.session_state['config']['env']['domain']['sub']['api']['path'])

        st.divider()
        if not st.session_state['config']['env']['domain']['sub']['device']['subdomain']:
            st.session_state['config']['env']['domain']['sub']['device']['subdomain'] = 'device'
        st.session_state['config']['env']['domain']['sub']['device']['subdomain'] = st.text_input('Enter the device subdomain', value=st.session_state['config']['env']['domain']['sub']['device']['subdomain'])
        st.session_state['config']['env']['domain']['sub']['device']['path'] = st.text_input('Enter the device api path', value=st.session_state['config']['env']['domain']['sub']['device']['path'])
else:
    st.session_state['config']['env']['domain']['name'] = ''
    st.session_state['config']['env']['domain']['hostedzone']['id'] = ''
    st.session_state['config']['env']['domain']['sub']['device']['subdomain'] = ''
    st.session_state['config']['env']['domain']['sub']['device']['name'] = ''
    st.session_state['config']['env']['domain']['sub']['device']['cert'] = ''
    st.session_state['config']['env']['domain']['sub']['api']['name'] = ''
    st.session_state['config']['env']['domain']['sub']['api']['subdomain'] = ''
    st.session_state['config']['env']['domain']['sub']['api']['cert'] = ''

if not st.session_state['config']['env']['domain']['sub']['device']['apikey']:
    st.session_state['config']['env']['domain']['sub']['device']['apikey'] = generate_api_key()

st.session_state['config']['env']['domain']['sub']['device']['apikey'] = st.text_input('Enter the api key to use for the mytaptrack app', value=st.session_state['config']['env']['domain']['sub']['device']['apikey'])

if not st.session_state['config']['env']['domain']['sub']['website']['name']:
    st.stop()

bottom_bar('./mytaptrack_installer.py', './pages/2_website.py')
