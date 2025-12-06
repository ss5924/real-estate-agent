TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_news",
            "description": "특정 주제와 날짜 기준의 최신 뉴스기사, 소식, 정보를 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_vector_store",
            "description": "부동산 관련 질의응답시 참조할 내용을 검색합니다. 최신 공문, 시행 방안 등을 담고 있습니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "사용자 질문"},
                    "top_k": {
                        "type": "integer",
                        "description": "검색 개수",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_datetime",
            "description": "에이전트의 답변에 현재 날짜, 시간 참조가 필요한 경우 현재 날짜, 시간을 불러옵니다.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_korean_law",
            "description": "국가법령정보를 검색합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "사용자가 특정 국가법령정보 요청 시 검색할 키워드",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_policy_and_safety",
            "description": "최종 답변이 정책/안전 측면에서 문제 없는지 검토하고, 필요 시 더 안전한 답변으로 재작성.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_query": {"type": "string", "description": "사용자 질문"},
                    "answer": {"type": "string", "description": "에이전트 답변"},
                },
                "required": ["query", "answer"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_summary",
            "description": "사용자의 요약 정보를 조회합니다. 과거 상담 이력을 통해 축적된 사용자의 장기 기억(선호 지역, 예산, 제약사항 등)을 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "사용자 ID"},
                },
                "required": ["user_id"],
            },
        },
    },
]
