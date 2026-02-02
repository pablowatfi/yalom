#!/usr/bin/env python3
"""
Local test script for Lambda query handler.
Simulates AWS Lambda invocation via API Gateway.
"""
import json
import os
import sys

# Add parent directory to path to import src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Set environment variables if not set
os.environ.setdefault('PINECONE_API_KEY', 'test-pinecone-key')
os.environ.setdefault('GROQ_API_KEY', os.getenv('GROQ_YALOM_API_KEY', 'test-groq-key'))

# Import handler
from aws.lambda_query.handler import lambda_handler


def test_query_local(query: str = "What is neuroplasticity?"):
    """Test query handler with sample event."""

    # Simulate API Gateway event
    event = {
        'body': json.dumps({
            'query': query,
            'top_k': 5
        }),
        'headers': {
            'Content-Type': 'application/json'
        },
        'httpMethod': 'POST',
        'path': '/query'
    }

    # Simulate Lambda context
    class MockContext:
        aws_request_id = 'test-request-456'
        function_name = 'yalom-query-test'
        memory_limit_in_mb = 1024
        invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789:function:test'

    context = MockContext()

    print("=" * 60)
    print("Testing Lambda Query Handler Locally")
    print("=" * 60)
    print(f"\nQuery: {query}")
    print(f"Context: {context.function_name}")
    print("\n" + "=" * 60 + "\n")

    try:
        # Call the handler
        response = lambda_handler(event, context)

        print("\n" + "=" * 60)
        print("Response:")
        print("=" * 60)
        print(f"Status Code: {response['statusCode']}")

        # Parse and pretty-print body
        if response.get('body'):
            try:
                body = json.loads(response['body'])

                if 'answer' in body:
                    print(f"\n✅ Answer:\n{body['answer']}")

                if 'sources' in body:
                    print(f"\n📚 Sources ({len(body['sources'])}):")
                    for i, source in enumerate(body['sources'][:3], 1):
                        print(f"   {i}. Video: {source.get('video_id', 'N/A')}")
                        print(f"      Score: {source.get('score', 0):.3f}")
                        if 'text_preview' in source:
                            preview = source['text_preview'][:100] + '...'
                            print(f"      Preview: {preview}")

                if 'error' in body:
                    print(f"\n❌ Error: {body['error']}")

            except json.JSONDecodeError:
                print(f"Body: {response['body']}")

        return response

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    # Check required environment variables
    required_vars = ['PINECONE_API_KEY', 'GROQ_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("⚠️  Warning: Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nSet them with:")
        print("   export GROQ_API_KEY=$GROQ_YALOM_API_KEY")
        print("   export PINECONE_API_KEY=your-pinecone-key")
        print("\nContinuing with test values...\n")

    # Get query from command line or use default
    query = sys.argv[1] if len(sys.argv) > 1 else "What is neuroplasticity?"

    result = test_query_local(query)
    sys.exit(0 if result and result.get('statusCode') == 200 else 1)
