""" This lambda function queries the upcoming weekly NHL schedule for a given date. It returns a schedule. At 15:44 in the hockey-statistics video."""

import boto3 as boto3
import json as json
import requests as requests
from requests.exceptions import Timeout, ConnectionError, HTTPError, RequestException
from botocore.exceptions import ClientError
import logging

# date should come from the event
date = "2023-11-10"

def fetch_schedule(date="2023-11-10"):
    url = f"https://api-web.nhle.com/v1/schedule/{date}"

    response = None

    try:
        response = requests.get(url=url)
        response.raise_for_status()
        print(response.json())
    except Timeout as e:
        print(f"Cound not fetch data due to:{e}")
    except ConnectionError as e:
        print(f"Could not fetch data due to:{e}")
    except HTTPError as e:
        print(f"Could not fetch data due to:{e}")
    except RequestException as e:
        print(f"Could not fetch data due to: {e}")
    except ClientError as e:
        print(f"Could not fetch data due to: {e}")
    except Exception as e:
        print(f"Could not fetch data due to: {e}")

    return response

# Next create a function that parses the response from the schedule fetcher

