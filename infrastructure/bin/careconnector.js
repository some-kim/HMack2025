#!/usr/bin/env node
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
require("source-map-support/register");
const cdk = require("aws-cdk-lib");
const careconnector_stack_1 = require("../lib/careconnector-stack");
const app = new cdk.App();
new careconnector_stack_1.CareConnectorStack(app, 'CareConnectorStack', {
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
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiY2FyZWNvbm5lY3Rvci5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbImNhcmVjb25uZWN0b3IudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6Ijs7O0FBQ0EsdUNBQXFDO0FBQ3JDLG1DQUFtQztBQUNuQyxvRUFBZ0U7QUFFaEUsTUFBTSxHQUFHLEdBQUcsSUFBSSxHQUFHLENBQUMsR0FBRyxFQUFFLENBQUM7QUFFMUIsSUFBSSx3Q0FBa0IsQ0FBQyxHQUFHLEVBQUUsb0JBQW9CLEVBQUU7SUFDaEQsR0FBRyxFQUFFO1FBQ0gsT0FBTyxFQUFFLE9BQU8sQ0FBQyxHQUFHLENBQUMsbUJBQW1CO1FBQ3hDLE1BQU0sRUFBRSxPQUFPLENBQUMsR0FBRyxDQUFDLGtCQUFrQixJQUFJLFdBQVc7S0FDdEQ7SUFDRCxXQUFXLEVBQUUsa0RBQWtEO0lBQy9ELElBQUksRUFBRTtRQUNKLE9BQU8sRUFBRSxlQUFlO1FBQ3hCLFdBQVcsRUFBRSxhQUFhO1FBQzFCLElBQUksRUFBRSxXQUFXO0tBQ2xCO0NBQ0YsQ0FBQyxDQUFDIiwic291cmNlc0NvbnRlbnQiOlsiIyEvdXNyL2Jpbi9lbnYgbm9kZVxyXG5pbXBvcnQgJ3NvdXJjZS1tYXAtc3VwcG9ydC9yZWdpc3Rlcic7XHJcbmltcG9ydCAqIGFzIGNkayBmcm9tICdhd3MtY2RrLWxpYic7XHJcbmltcG9ydCB7IENhcmVDb25uZWN0b3JTdGFjayB9IGZyb20gJy4uL2xpYi9jYXJlY29ubmVjdG9yLXN0YWNrJztcclxuXHJcbmNvbnN0IGFwcCA9IG5ldyBjZGsuQXBwKCk7XHJcblxyXG5uZXcgQ2FyZUNvbm5lY3RvclN0YWNrKGFwcCwgJ0NhcmVDb25uZWN0b3JTdGFjaycsIHtcclxuICBlbnY6IHtcclxuICAgIGFjY291bnQ6IHByb2Nlc3MuZW52LkNES19ERUZBVUxUX0FDQ09VTlQsXHJcbiAgICByZWdpb246IHByb2Nlc3MuZW52LkNES19ERUZBVUxUX1JFR0lPTiB8fCAndXMtZWFzdC0yJyxcclxuICB9LFxyXG4gIGRlc2NyaXB0aW9uOiAnQ2FyZUNvbm5lY3RvciBIZWFsdGhjYXJlIFBsYXRmb3JtIEluZnJhc3RydWN0dXJlJyxcclxuICB0YWdzOiB7XHJcbiAgICBQcm9qZWN0OiAnQ2FyZUNvbm5lY3RvcicsXHJcbiAgICBFbnZpcm9ubWVudDogJ0RldmVsb3BtZW50JyxcclxuICAgIFRlYW06ICdIYWNrYXRob24nLFxyXG4gIH0sXHJcbn0pOyJdfQ==