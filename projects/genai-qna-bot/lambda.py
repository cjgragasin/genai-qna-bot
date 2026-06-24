import boto3
import json
import os
import urllib.request
import base64

s3 = boto3.client('s3', region_name='ap-southeast-1')

BUCKET_NAME = os.environ.get('BUCKET_NAME', 'cjgragasin.ai.project')


def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'content-type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': ''
        }

    try:
        body = json.loads(event.get('body', '{}'))
        question = body.get('question', '')
        filename = body.get('filename', '')

        if not question or not filename:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Question and filename are required'})
            }

        # Read PDF from S3 as base64
        response = s3.get_object(Bucket=BUCKET_NAME, Key=filename)
        pdf_bytes = response['Body'].read()
        pdf_base64 = base64.standard_b64encode(pdf_bytes).decode('utf-8')

        # Call Gemini API
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={InputAPIHere}'

        payload = json.dumps({
            'contents': [{
                'parts': [
                    {
                        'inline_data': {
                            'mime_type': 'application/pdf',
                            'data': pdf_base64
                        }
                    },
                    {
                        'text': question
                    }
                ]
            }]
        }).encode('utf-8')

        req = urllib.request.Request(
            url,
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req) as res:
            result = json.loads(res.read().decode('utf-8'))
            answer = result['candidates'][0]['content']['parts'][0]['text']

        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'answer': answer})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }