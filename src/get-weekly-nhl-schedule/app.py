""" This lambda function queries the upcoming weekly NHL schedule for a given date. It returns a schedule. At 15:44 in the hockey-statistics video."""

import boto3 as boto3
import json as json
import requests as requests
from requests.exceptions import Timeout, ConnectionError, HTTPError, RequestException
from botocore.exceptions import ClientError
import logging

# date should come from the event
date = "2023-11-10"

def fetch_schedule(date=date):
    url = f"https://api-web.nhle.com/v1/schedule/{date}"

    response = None

    try:
        response = requests.get(url=url)
    except Exception as e:
        print(f"Could not fetch data due to {e}")

    return response

# Next create a function that parses the response from the schedule fetcher

