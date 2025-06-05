import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
// import * as sqs from 'aws-cdk-lib/aws-sqs';
import yaml from 'yaml';
import fs from 'fs';

export class CicdStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Read the config yml file from the current directory
    const config = yaml.parse(fs.readFileSync('./config.yml', 'utf8'));

    // Create codebuild project
    const project = new cdk.aws_codebuild.Project(this, 'MyProject', {
      projectName: `mytaptrack-${process.env.STAGE}-back-end`,
      buildSpec: cdk.aws_codebuild.BuildSpec.fromAsset('./buildspec.yml'),
      environment: {
        buildImage: cdk.aws_codebuild.LinuxBuildImage.AMAZON_LINUX_2_5,
        privileged: true,
        environmentVariables: {
          'AWS_ACCOUNT_ID': {
            value: this.account
          },
          'AWS_REGION': {
            value: this.region
          },
          'ENVIRONMENT': {
            value: config.env.name ?? 'dev'
          },
          'STAGE': {
            value: config.env.name ?? 'dev'
          }
        }
      }
    });

    project.addToRolePolicy(new cdk.aws_iam.PolicyStatement({
      actions: [
        '*'
      ],
      resources: [
        `*`
      ]
    }));
  }
}
