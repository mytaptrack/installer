import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
// import * as sqs from 'aws-cdk-lib/aws-sqs';
import yaml from 'yaml';
import fs from 'fs';
import moment from 'moment-timezone';
import { Bucket } from 'aws-cdk-lib/aws-s3';

const solution_actions = [
  's3:*',
  'codebuild:*',
  'kms:*',
  'cloudformation:*',
  'acm:*',
  'route53:*',
  'apigateway:*',
  'logs:*',
  'events:*',
  'lambda:*',
  'dynamodb:*',
  'cognito-idp:*',
  'cognito-identity:*',
  'dynamodb:*',
  'timestream:*',
  'cloudfront:*',
  'ecs:*',
  'ecr:*',
  'sqs:*',
  'sns:*',
  'ses:*',
  'sts:AssumeRole',
  'sts:GetCallerIdentity',
  'sts:GetSessionToken',
  'states:*',
  'appsync:*',
  'secretsmanager:*',
  'iam:AttachRolePolicy',
  'iam:CreatePolicy',
  'iam:CreateRole',
  'iam:DeleteRole',
  'iam:DeleteRolePolicy',
  'iam:DetachRolePolicy',
  'iam:GetRole',
  'iam:GetRolePolicy',
  'iam:List*',
  'iam:ListInstanceProfilesForRole',
  'iam:PutRolePolicy',
  'iam:UpdateRole',
  'iam:UpdateRoleDescription',
  'ssm:DescribeParameters',
  'ssm:GetParameters',
  'ssm:PutParameter',
  'ssm:DeleteParameter',
  'ssm:GetParametersByPath',
  'ssm:GetParameter',
  'ssm:DeleteParameters'
];

export class CicdStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const stage = process.env.STAGE ?? 'dev';

    // Read the config yml file from the current directory
    const config = yaml.parse(fs.readFileSync('./config.yml', 'utf8'));

    // Create code pipeline
    const pipeline = new cdk.aws_codepipeline.Pipeline(this, 'MyTapTrackPipeline', {
      pipelineName: `mytaptrack-${stage}`,
    });

    const artifact = new cdk.aws_codepipeline.Artifact('SourceArtifact');
    pipeline.addStage({
      stageName: 'Source',
      actions: [
        new cdk.aws_codepipeline_actions.S3SourceAction({
          actionName: 'Source',
          bucket: Bucket.fromBucketName(this, 'EnvironmentBucket', `mytaptrack-${this.account}-environments`),
          bucketKey: `${this.region}/${stage}.yml`,
          output: artifact
        })
      ]
    });

    // Create codebuild project
    const project = new cdk.aws_codebuild.Project(this, 'MyProject', {
      projectName: `mytaptrack-${stage}-back-end`,
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
          'CDK_DEFAULT_ACCOUNT': {
            value: this.account
          },
          'CDK_DEFAULT_REGION': {
            value: this.region
          },
          'BRANCH': {
            value: config.env.branch ?? 'main'
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
      actions: solution_actions,
      resources: [`*`]
    }));
    
    pipeline.addStage({
      stageName: 'BackEnd',
      actions: [
        new cdk.aws_codepipeline_actions.CodeBuildAction({
          actionName: 'Build',
          project,
          input: artifact
        })
      ]
    });

    let uiProject: cdk.aws_codebuild.Project | undefined = undefined;
    if(config.env.deploy.website) {
      uiProject = new cdk.aws_codebuild.Project(this, 'FrontEnd', {
        projectName: `mytaptrack-${stage}-front-end`,
        buildSpec: cdk.aws_codebuild.BuildSpec.fromAsset('./buildspec_front_end.yml'),
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
            'CDK_DEFAULT_ACCOUNT': {
              value: this.account
            },
            'CDK_DEFAULT_REGION': {
              value: this.region
            },
            'ENVIRONMENT': {
              value: stage
            },
            'STAGE': {
              value: stage
            },
            'BRANCH': {
              value: config.env.ui_branch ?? 'main'
            },
            'USER_POOL_ID': {
              type: cdk.aws_codebuild.BuildEnvironmentVariableType.PARAMETER_STORE,
              value: `/${stage}/regional/calc/cognito/userpoolid`
            },
            'IDENTITY_POOL_ID': {
              type: cdk.aws_codebuild.BuildEnvironmentVariableType.PARAMETER_STORE,
              value: `/${stage}/regional/calc/cognito/idpoolid`
            },
            'MANAGE_DOMAIN': {
              type: cdk.aws_codebuild.BuildEnvironmentVariableType.PARAMETER_STORE,
              value: `/${stage}/regional/calc/website/domain/manage`
            },
            'API_DOMAIN': {
              type: cdk.aws_codebuild.BuildEnvironmentVariableType.PARAMETER_STORE,
              value: `/${stage}/regional/calc/endpoints/api/url`
            },
            'GRAPH_DOMAIN': {
              type: cdk.aws_codebuild.BuildEnvironmentVariableType.PARAMETER_STORE,
              value: `/${stage}/regional/calc/endpoints/appsync/url`
            },
            'COGNITO_DOMAIN': {
              type: cdk.aws_codebuild.BuildEnvironmentVariableType.PARAMETER_STORE,
              value: `/${stage}/regional/calc/cognito/domain`
            },
            'COGNITO_CLIENT_ID': {
              type: cdk.aws_codebuild.BuildEnvironmentVariableType.PARAMETER_STORE,
              value: `/${stage}/regional/calc/cognito/clientid`
            },
            'BEHAVIOR_DOMAIN': {
              type: cdk.aws_codebuild.BuildEnvironmentVariableType.PARAMETER_STORE,
              value: `/${stage}/regional/calc/website/domain/behavior`
            },
            'WEBSITE_BUCKET': {
              type: cdk.aws_codebuild.BuildEnvironmentVariableType.PARAMETER_STORE,
              value: `/${stage}/regional/calc/website/bucket`
            }
          }
        }
      });

      uiProject.addToRolePolicy(new cdk.aws_iam.PolicyStatement({
        actions: solution_actions,
        resources: [`*`]
      }));

      pipeline.addStage({
        stageName: 'FrontEnd',
        actions: [
          new cdk.aws_codepipeline_actions.CodeBuildAction({
            actionName: 'Build',
            project: uiProject,
            input: artifact
          })
        ]
      });
    }

    if(config.env.deploy.auto) {

      console.log('Deploy config', config.env.deploy);

      // Schedule the builds to run weekly
      const buffer: Buffer = config.env.deploy.time[0];
      console.log('Deploy config', config.env.deploy.time[0]);
      const hours = buffer.readInt8()
      console.log('Deploy time hours', hours);
      const minutes = config.env.deploy.time[0].readInt32LE(1);
      console.log('Deploy time minutes', minutes);

      // Set the timezone
      const timezone = config.env.deploy.timezone;
      let time = moment({weekday: config.env.deploy.day, h: hours, m: minutes});
      const goalDay = config.env.deploy.day == 'SUN'? 0 : 6;
      if(time.weekday() != goalDay) {
        time = time.add(goalDay - time.weekday() % 7, 'day');
      }
      time = time.subtract(config.env.deploy.timezone, 'hours');

      let day = 'SAT';
      switch(time.weekday()) {
        case 0:
          day = 'SUN';
          break;
        case 1:
          day = 'MON';
          break;
        case 2:
          day = 'TUE';
          break;
        case 3:
          day = 'WED';
          break;
        case 4:
          day = 'THU';
          break;
        case 5:
          day = 'FRI';
          break;
        case 6:
          day = 'SAT';
          break;
      }

      console.log(`Deploy Time: ${time.weekday()} ${time.hour()}:${time.minute()}`);

      const rule = new cdk.aws_events.Rule(this, 'ScheduleRule', {
        schedule: cdk.aws_events.Schedule.cron({
          weekDay: day,
          hour: `${time.hour()}`,
          minute: `${time.minute()}`
        })
      });

      // Run build projects
      rule.addTarget(new cdk.aws_events_targets.CodePipeline(pipeline));
    }
  }
}
