#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { CicdStack } from '../lib/cicd-stack';

const app = new cdk.App();
new CicdStack(app, 'CicdStack', {
  stackName: `mytaptrack-pipeline-${process.env.STAGE}-backend`,
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION }
});