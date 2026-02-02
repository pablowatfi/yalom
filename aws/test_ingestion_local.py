#!/usr/bin/env python3
"""
Local test script for Lambda ingestion handler.
Simulates AWS Lambda invocation locally.
"""
import json
import os
import sys

# Add parent directory to path to import src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Set environment variables if not set
os.environ.setdefault('PINECONE_API_KEY', 'test-pinecone-key')
os.environ.setdefault('S3_BUCKET', 'test-bucket')

# Import handler
from aws.lambda_ingestion.handler import lambda_handler


def test_ingestion_local():
    """Test ingestion handler with sample event."""

    # Simulate Lambda event from EventBridge
    event = {
        'video_ids': [
            'dQw4w9WgXcQ',  # Sample video ID
        ]
    }

    # Simulate Lambda context
    class MockContext:
        aws_request_id = 'test-request-123'
        function_name = 'yalom-ingestion-test'
        memory_limit_in_mb = 1024
        invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789:function:test'

    context = MockContext()

    print("=" * 60)
    print("Testing Lambda Ingestion Handler Locally")
    print("=" * 60)
    print(f"\nEvent: {json.dumps(event, indent=2)}")
    print(f"\nContext: {context.function_name}")
    print("\n" + "=" * 60 + "\n")

    try:
        # Call the handler
        response = lambda_handler(event, context)

        print("\n" + "=" * 60)
        print("Response:")
        print("=" * 60)
        print(f"Status Code: {response['statusCode']}")
        print(f"Body: {response['body']}")

        # Parse and pretty-print body
        if response.get('body'):
            try:
                body = json.loads(response['body'])
                print(f"\nParsed Response:")
                print(json.dumps(body, indent=2))
            except json.JSONDecodeError:
                pass

        return response

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    # Check required environment variables
    required_vars = ['PINECONE_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("⚠️  Warning: Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nSet them with:")
        for var in missing_vars:
            print(f"   export {var}=your-key-here")
        print("\nContinuing with test values...\n")

    result = test_ingestion_local()
    sys.exit(0 if result and result.get('statusCode') == 200 else 1)
