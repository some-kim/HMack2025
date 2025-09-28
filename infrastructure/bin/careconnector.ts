#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { CareFlowStack } from '../lib/careconnector-stack';

const app = new cdk.App();

new CareFlowStack(app, 'CareFlowStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  description: 'CareFlow Healthcare Platform Infrastructure',
  tags: {
    Project: 'CareFlow',
    Environment: 'Development',
    Team: 'Hackathon',
  },
});