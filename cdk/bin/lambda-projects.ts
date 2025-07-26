import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { NhlDataPipelineStack } from '../lib/nhl-data-pipeline-stack';

const app = new cdk.App();

const customBucketName = `nhl-player-data-myproject-${cdk.Aws.ACCOUNT_ID}`; // Example for a more unique name
const myExistingTargetLambdaName = "GetNHLSeasonsLambda"; // <<< IMPORTANT: Replace with your Lambda's actual name

new NhlDataPipelineStack(app, 'NhlDataPipelineStack', {
  // Corrected: Use 'dataBucketName' to match the interface NhlDataPipelineStackProps
  dataBucketName: customBucketName, // This line was changed
  existingTargetLambdaName: myExistingTargetLambdaName, // Pass the name here
  env: { account: process.env.CDK_DEFAULT_ACCOUNT || '050925927410', region: process.env.CDK_DEFAULT_REGION || 'us-east-2'},
});