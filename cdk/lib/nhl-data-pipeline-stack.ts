import { Stack, StackProps, CfnOutput, Duration } from 'aws-cdk-lib';
import * as cdk from 'aws-cdk-lib'; // <-- Add this line
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as path from 'path'; // Needed for path.join

interface NhlDataPipelineStackProps extends StackProps {
  dataBucketName: string;
  existingTargetLambdaName: string; // <-- Add a prop for the existing Lambda's name
}

export class NhlDataPipelineStack extends Stack {
  constructor(scope: Construct, id: string, props: NhlDataPipelineStackProps) {
    super(scope, id, props);

    // 1. Define the S3 Bucket (same as before)
    const nhlDataBucket = new s3.Bucket(this, 'NhlPlayerBiosBucket', {
      bucketName: props.dataBucketName,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev
      autoDeleteObjects: true, // For dev
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
    });

    // 2. Import the Existing Target Lambda Function
    // We reference it by its function name. CDK will resolve its ARN.
    const existingTargetLambda = lambda.Function.fromFunctionName(
      this,
      'ExistingTargetLambdaRef', // A unique logical ID for this reference within your stack
      props.existingTargetLambdaName // The actual name of the Lambda function in AWS
    );

    // 3. Define the Source Lambda Function (your data fetcher)
    const sourceLambda = new lambda.Function(this, 'NhlApiFetcherLambda', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'app.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '..', '..', 'src')),
      timeout: Duration.minutes(5),
      memorySize: 256,
      environment: {
        S3_BUCKET_NAME: nhlDataBucket.bucketName,
        // Pass the ARN of the existing Lambda to your source Lambda
        TARGET_LAMBDA_ARN: existingTargetLambda.functionArn,
      },
    });

    // --- GRANT PERMISSIONS ---

    // Grant the Source Lambda permission to add objects (put) to the S3 bucket.
    nhlDataBucket.grantPut(sourceLambda);

    // Grant the Source Lambda permission to invoke the existing Target Lambda.
    // The `grantInvoke` method works just as well with imported functions!
    existingTargetLambda.grantInvoke(sourceLambda);

    // Output the bucket name for easy reference
    new CfnOutput(this, 'NhlDataBucketName', {
      value: nhlDataBucket.bucketName,
      description: 'Name of the S3 bucket for NHL player bios',
    });

    // Output the ARN of the target Lambda (for verification)
    new CfnOutput(this, 'ExistingTargetLambdaArn', {
        value: existingTargetLambda.functionArn,
        description: 'ARN of the existing Lambda function being invoked',
    });
  }
}