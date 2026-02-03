from rest_framework.decorators import api_view
from rest_framework.response import Response
from .logic import get_verified_answer
import json

@api_view(['POST'])
def query_llm(request):
    user_query = request.data.get('query')
    
    # Trigger the real RAG + Verification logic
    raw_ai_response = get_verified_answer(user_query)
    
    # Parse the AI's JSON response
    try:
        data = json.loads(raw_ai_response)
    except:
        # Fallback if AI doesn't return clean JSON
        data = {"answer": "Error parsing AI response", "faithfulness_score": 0}

    return Response(data)