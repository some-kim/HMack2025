#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { CareConnectorStack } from '../lib/careconnector-stack';

const app = new cdk.App();

new CareConnectorStack(app, 'CareConnectorStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-2',
  },
  description: 'CareConnector Healthcare Platform Infrastructure',
  tags: {
    Project: 'CareConnector',
    Environment: 'Development',
    Team: 'Hackathon',
  },
});