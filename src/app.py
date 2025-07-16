import boto3 as boto3
import json as json
import requests as requests
from botocore.exceptions import ClientError

# Initialize the Lambda client globally for reuse across invocations
# This helps with performance in subsequent calls within the same execution environment.
lambda_client = boto3.client('lambda')

# Define the NHL API endpoint for skater bios
NHL_SKATER_BIOS_API_URL = "https://api.nhle.com/stats/rest/en/skater/bios?limit=-1&start=0&cayenneExp=seasonId="

def invoke_get_nhl_seasons():
    """
    Invokes the 'GetNHLSeasonsLambda' function and returns its raw response.
    Handles AWS client-level errors (e.g., permissions, function not found).

    Returns:
        dict: The raw response dictionary from boto3.client('lambda').invoke().
              This dictionary will contain a 'Payload' StreamingBody if successful,
              or an error structure if a ClientError occurred.
    """
    target_lambda_name = 'GetNHLSeasonsLambda'
    payload_to_send = {} # Empty payload as per your existing Lambda's expected input

    try:
        print(f"Attempting to invoke Lambda function: {target_lambda_name}")
        response = lambda_client.invoke(
            FunctionName=target_lambda_name,
            InvocationType='RequestResponse', # Ensures we wait for a response
            Payload=json.dumps(payload_to_send)
        )
        # Note: The 'StatusCode' here is the status of the *invocation API call*,
        # not necessarily the HTTP status code returned by the invoked Lambda itself.
        # The invoked Lambda's internal status is within the 'Payload'.
        return response
    except ClientError as e:
        # Catch specific AWS client errors (e.g., permissions, function not found, throttling)
        error_code = e.response.get('Error', {}).get('Code')
        error_message = e.response.get('Error', {}).get('Message')
        print(f"AWS Client Error invoking Lambda '{target_lambda_name}': {error_code} - {error_message}")
        # Log the full error response for detailed debugging in CloudWatch
        print(f"Full ClientError response: {json.dumps(e.response, indent=2)}")
        # Return an error structure that can be consistently handled by calling code
        return {
            'InvocationError': True, # Custom key to indicate an invocation failure
            'errorCode': error_code,
            'errorMessage': error_message
        }
    except Exception as e:
        # Catch any other unexpected errors during the invocation process
        print(f"An unexpected error occurred during Lambda invocation: {e}")
        return {
            'InvocationError': True,
            'errorCode': 'UnexpectedError',
            'errorMessage': str(e)
        }

def parse_nhl_seasons_response(lambda_response):
    """
    Parses the raw response payload from a boto3 Lambda invocation into a Python dictionary.
    This function handles the StreamingBody and initial JSON parsing.

    Args:
        lambda_response (dict): The raw response dictionary from boto3.client('lambda').invoke().
                                This should contain a 'Payload' StreamingBody.

    Returns:
        dict or None: A Python dictionary representing the invoked Lambda's full response
                      (e.g., {'statusCode': 200, 'headers': {}, 'body': '...'}).
                      Returns None if the payload cannot be read or parsed.
    """
    payload_string = None # Initialize for error reporting context

    # Check for invocation-level errors first
    if lambda_response.get('InvocationError'):
        print(f"Skipping payload parsing due to invocation error: {lambda_response.get('errorMessage')}")
        return None

    if 'Payload' in lambda_response and hasattr(lambda_response['Payload'], 'read'):
        try:
            payload_stream = lambda_response['Payload']
            payload_bytes = payload_stream.read()
            payload_string = payload_bytes.decode('utf-8')
            
            # Check if the invoked Lambda itself returned an error (e.g., unhandled exception)
            # This is indicated by 'FunctionError' in the top-level response from AWS.
            if 'FunctionError' in lambda_response:
                # The payload_string will contain the error details from the invoked Lambda
                print(f"Invoked Lambda reported a FunctionError. Payload: {payload_string}")
                # You might want to parse this payload_string to extract error details
                # and return them, or simply return None to indicate failure.
                # For this example, we'll return the parsed error payload.
                try:
                    return json.loads(payload_string)
                except json.JSONDecodeError:
                    print("Error: FunctionError payload is not valid JSON.")
                    return None
            
            parsed_lambda_output = json.loads(payload_string)
            return parsed_lambda_output
        except json.JSONDecodeError as e:
            print(f"Error: Could not parse Lambda payload string as JSON: {e}")
            print(f"Problematic payload string: {payload_string}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during payload processing: {e}")
            return None
    else:
        # This case might occur if the 'Payload' key is missing or not a StreamingBody
        print("Error: 'Payload' not found or not readable in Lambda response.")
        # If lambda_response itself is the desired dict (e.g., for testing), handle it here.
        # For actual boto3 invoke, 'Payload' is always present for 'RequestResponse'.
        if isinstance(lambda_response, dict):
            # If it's already a dictionary, assume it's the final parsed output
            # This branch is primarily for flexible local testing.
            print("Assuming lambda_response is already the parsed output (for testing purposes).")
            return lambda_response
        return None

def parse_seasons_json(parsed_lambda_output):
    """
    Extracts the list of NHL seasons from the parsed Lambda output.
    It verifies the 'statusCode' and then parses the 'body' field.

    Args:
        parsed_lambda_output (dict): The dictionary output from parse_nhl_seasons_response.
                                     Expected to contain 'statusCode', 'headers', and 'body'.

    Returns:
        list or None: A list of season identifiers (e.g., [19171918, ...]) if the
                      statusCode is 200 and the body is valid JSON.
                      Returns None if the status code is not 200, the 'body' is missing,
                      or if the 'body' cannot be parsed as JSON.
    """
    if parsed_lambda_output is None:
        print("Error: Input to parse_seasons_json is None.")
        return None
    
    # Check if the input dictionary indicates an unhandled FunctionError from the invoked Lambda
    # This check is important if parse_nhl_seasons_response passes through the FunctionError payload.
    if parsed_lambda_output.get('errorMessage') and parsed_lambda_output.get('errorType'):
        print(f"Invoked Lambda reported an unhandled error: {parsed_lambda_output.get('errorType')} - {parsed_lambda_output.get('errorMessage')}")
        return None

    status_code = parsed_lambda_output.get('statusCode')

    if status_code == 200:
        response_body_string = parsed_lambda_output.get('body')

        if response_body_string is None:
            print("Warning: statusCode is 200 but 'body' field is missing or None.")
            return [] # Return empty list if no data is expected for a successful call
        
        try:
            # The 'body' content is itself a JSON string, so it needs another parse
            final_seasons_list = json.loads(response_body_string)
            print(f"Successfully extracted seasons list from body. Status Code: {status_code}")
            return final_seasons_list
        except json.JSONDecodeError as e:
            print(f"Error: Could not parse 'body' content as JSON: {e}")
            print(f"Problematic body string: {response_body_string}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred while parsing seasons body: {e}")
            return None
    else:
        # Handle cases where the invoked Lambda returned a non-200 status code
        print(f"Invoked Lambda returned non-200 status code: {status_code}")
        # You can log more details if needed, e.g., parsed_lambda_output.get('body')
        return None

def lambda_handler(event, context):
    """
    First: invoke the GetNHLSeasonsLambda and save to raw_response
    Second: parse the seasons response
    Third: save the seasons list to a variable seasons
    Fourth: Loop through seasons list to make repeated HTTP requests to the NHL_SKATER_BIOS_API_URL
    Fifth: Using new JSON write the processed payer bios to S3 in one file?
    """
