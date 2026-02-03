from rest_framework.decorators import api_view
from rest_framework.response import Response
from .rag_logic import get_verified_answer

@api_view(['POST'])
def query_llm(request):
    """
    API Endpoint that receives a user question,
    passes it to the RAG logic, and returns the verification.
    """
    # 1. Get the 'query' from the frontend JSON
    user_query = request.data.get('query')
    
    if not user_query:
        return Response({"error": "No query provided"}, status=400)
    
    print(f"🔍 Received Query: {user_query}")

    # 2. Call the new function we just added to rag_logic.py
    result = get_verified_answer(user_query)
    
    # 3. Return the result (Answer + Faithfulness Score)
    return Response(result)