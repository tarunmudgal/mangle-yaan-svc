#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = 'tarun mudgal'

import json
import time

import boto3

# supported env names are - dev, stg, preview, prd
ENV = 'stg'

## Athena configurations
DATABASE = 'default'
BUCKET = 'csp-cdn-logging-dev-standard'
S3_PATH = 'athena-query-results'
WORKGROUP = 'cloudfront_logs'
# for stg, table name is cloudfront_logs_standard and for preview it is cloudfront_logs_preview. Others,
# it is cloudfront_logs only.
ATHENA_TABLE_NAME = 'cloudfront_logs'

if ENV == 'dev':
    ATHENA_TABLE_NAME = 'cloudfront_logs'
    BUCKET = 'csp-cdn-logging-dev-standard'
    WORKGROUP = 'cloudfront_logs'
elif ENV == 'stg':
    ATHENA_TABLE_NAME = 'cloudfront_logs_standard'
    BUCKET = 'csp-cdn-logging-stg-standard'
    WORKGROUP = 'cloudfront_logs_standard'
elif ENV == 'preview':
    ATHENA_TABLE_NAME = 'cloudfront_logs_preview'
    BUCKET = 'csp-cdn-logging-stg-preview'
    WORKGROUP = 'cloudfront_logs_preview'

ATHENA_QUERY = f'''WITH CUR_TS AS (
  SELECT 
    CAST(
      split_part(
        Cast(
          CURRENT_TIMESTAMP AS VARCHAR(30)
        ), 
        ' ', 
        1
      ) || ' ' || split_part(
        Cast(
          CURRENT_TIMESTAMP AS VARCHAR(30)
        ), 
        ' ', 
        2
      ) AS TIMESTAMP
    ) AS TS
) 
SELECT 
  CF_LOGS.status, 
  CF_LOGS.x_edge_detailed_result_type, 
  count(*) as AGGREGATE_COUNT 
from 
  {ATHENA_TABLE_NAME} AS CF_LOGS 
  INNER JOIN CUR_TS ON CF_LOGS.response_result_type = 'Error' AND CAST(CAST(CF_LOGS.date as varchar(10)) || ' ' || 
  CF_LOGS.time AS TIMESTAMP) >= DATE_ADD('minute', -10, CUR_TS.TS)
GROUP BY 
  CF_LOGS.x_edge_detailed_result_type, 
  CF_LOGS.status 
ORDER BY 
  AGGREGATE_COUNT DESC, 
  CF_LOGS.x_edge_detailed_result_type DESC, 
  CF_LOGS.status DESC'''

athena_client = boto3.client('athena')


def has_query_succeeded(execution_id):
    state = "RUNNING"
    max_execution = 12

    while max_execution > 0 and state in ["RUNNING", "QUEUED"]:
        max_execution -= 1
        response = athena_client.get_query_execution(QueryExecutionId=execution_id)
        if (
                "QueryExecution" in response
                and "Status" in response["QueryExecution"]
                and "State" in response["QueryExecution"]["Status"]
        ):
            state = response["QueryExecution"]["Status"]["State"]
            print(f"Query execution current state is: {state}")
            if state == "SUCCEEDED":
                return True

        time.sleep(5)

    return False


def get_query_results(execution_id):
    response = athena_client.get_query_results(
        QueryExecutionId=execution_id
    )

    results = response['ResultSet']['Rows']
    return results


def lambda_handler(event, context):
    # Run query in Athena

    output = "s3://{}/{}".format(BUCKET, S3_PATH)
    # Execution
    response = athena_client.start_query_execution(
        QueryString=ATHENA_QUERY,
        QueryExecutionContext={
            'Database': DATABASE
        },
        ResultConfiguration={
            'OutputLocation': output,
        }
    )
    start_time = time.time()
    query_exe_id = response["QueryExecutionId"]
    time.sleep(5)
    query_exe_status = has_query_succeeded(query_exe_id)
    end_time = time.time()
    print(f"query execution time = {end_time-start_time}")
    results = []
    if query_exe_status:
        results = get_query_results(query_exe_id)
    else:
        raise Exception("Athena query could not be succeeded")

    # q_stats = athena_client.get_query_runtime_statistics(QueryExecutionId=query_exe_id)
    # print(f"q_stats={q_stats}")

    # print(f"results={results}")
    results = results[1:]
    metric_data = []
    for data in results:
        metric_data.append({
            'MetricName': 'CustomCloudFrontErrors',
            'Dimensions': [
                {
                    'Name': 'Status',
                    'Value': data['Data'][0]['VarCharValue']
                },
                {
                    'Name': 'x_edge_detailed_result_type',
                    'Value': data['Data'][1]['VarCharValue']
                },
            ],
            'Unit': 'None',
            'Value': int(data['Data'][2]['VarCharValue'])
        })

    # post query results as a CloudWatch metric
    cloudwatch_client = boto3.client('cloudwatch')

    # response = cloudwatch.get_metric_statistics(
    #     Namespace='AWS/CloudFront',
    #     MetricName='CustomCloudFrontErrors',
    #     Dimensions=[
    #         {
    #             'Name': 'Status',
    #             'Value': '400'
    #         },
    #         {
    #             'Name': 'x_edge_detailed_result_type',
    #             'Value': 'Error'
    #         },
    #     ],
    #     StartTime=datetime.utcnow() - timedelta(seconds=7200),
    #     EndTime=datetime.utcnow(),
    #     Period=300,
    #     Statistics=[
    #         'SampleCount',
    #     ],
    #     Unit='None'
    # )

    # response = cloudwatch.get_metric_data(
    #     MetricDataQueries=[
    #         {
    #             'Id': 'myrequest',
    #             'MetricStat': {
    #                 'Metric': {
    #                     'Namespace': 'AWS/CloudFront',
    #                     'MetricName': 'CustomCloudFrontErrors',
    #                     'Dimensions': [
    #                         {
    #                             'Name': 'Status',
    #                             'Value': '400'
    #                         },
    #                         {
    #                             'Name': 'x_edge_detailed_result_type',
    #                             'Value': 'Error'
    #                         },
    #                     ]
    #                 },
    #                 'Period': 300,
    #                 'Stat': 'Sum',
    #                 'Unit': 'Count'
    #             }
    #         },
    #     ],
    #     StartTime=datetime.utcnow() - timedelta(seconds=10800),
    #     EndTime=datetime.utcnow(),
    #     MaxDatapoints=1,
    # )
    # print("response: {}".format(response))
    # breakpoint()

    response = {
        'statusCode': 500,
        'body': json.dumps('Request could not succeed')}
    if metric_data:
        print("Pushing metrics data to cloudwatch")
        response = cloudwatch_client.put_metric_data(
            MetricData=metric_data,
            Namespace='AWS/CloudFront'
        )
    else:
        print("No metrics data to be pushed to cloudwatch")
        response = {
            'statusCode': 200,
            'body': json.dumps('Request succeeded')}

    return response


lambda_handler('', '')
