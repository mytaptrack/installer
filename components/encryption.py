import streamlit as st
import boto3

kms = boto3.client('kms')

def set_encryption_alias(alias_name: str, display_name: str, dict_key: str, kms_keys):
    if dict_key not in st.session_state:
        st.session_state[dict_key] = ''

    aliases = kms.list_aliases()['Aliases']

    # Find the key id for pii_alias
    for alias in aliases:
        if alias['AliasName'] == alias_name:
            print(f"Found pii alias: {alias}")
            st.session_state[dict_key] = alias['TargetKeyId']
            break
    
    if st.button(f'Create new encryption key for {display_name}'):
        # Create the key
        pii_key_data = kms.create_key(
            Description='Encryption key for mytaptrack pii',
            KeyUsage='ENCRYPT_DECRYPT',
            Origin='AWS_KMS',
            BypassPolicyLockoutSafetyCheck=True
        )
        kms.create_alias(
            AliasName=alias_name,
            TargetKeyId=pii_key_data['KeyMetadata']['KeyId']
        )
        st.success('Pii encryption key created')
        st.session_state[dict_key] = pii_key_data['KeyMetadata']['KeyId']

        # Add new key to kms_keys
        kms_keys.append(pii_key_data['KeyMetadata'])

    # Get index for pii_key
    print([key['KeyId'] for key in kms_keys])
    index = 0
    for i, key in enumerate(kms_keys):
        if key['KeyId'] == st.session_state['pii_key']:
            index = i
            break
    
    print(f"index: {index}")
    print(f"pre select {dict_key}: {st.session_state[dict_key]}")

    # Create a dropdown to select the key
    pii_key = st.selectbox(
        f'Select the {display_name} key',
        [key['KeyId'] for key in kms_keys],
        index=index
    )
    print(f"{dict_key} key: {pii_key}")
    st.session_state[dict_key] = pii_key
    
    # Check if the KMS pii key exists
    aliases = kms.list_aliases()['Aliases']
    alias_found = False
    for alias in aliases:
        if 'TargetKeyId' in alias and alias['TargetKeyId'] == st.session_state[key]:
            alias_found = True
            break
    
    if not alias_found:
        st.error('Pii encryption key not configured')
        if st.button(f'Assign {display_name} alias', key=f'{key}_alias'):
            kms.create_alias(
                AliasName=alias_name,
                TargetKeyId=st.session_state[dict_key]
            )
            st.success(f'{display_name} key assigned')
    else:
        st.success(f'{display_name} key configured')

def encryption_settings():
    # Get list of kms keys and aliases
    kms_keys = kms.list_keys()['Keys']

    set_encryption_alias('alias/mytaptrack/pii', 'pii encryption key', 'pii_key', kms_keys)
    set_encryption_alias('alias/mytaptrack/logs', 'logs encryption key', 'logs_key', kms_keys)

    st.session_state['config']['env']['encryption'] = {
        'piiAlias': st.session_state['pii_key'],
        'logAlias': "mytaptrack/logs"
    }
