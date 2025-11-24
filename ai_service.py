# ai_service.py

def check_text_safety(content: str):
    """
    (임시) 텍스트 유해성을 검사합니다.
    """
    forbidden_words = ["바보", "멍청이"]
    
    for word in forbidden_words:
        if word in content:
            return False, f"부적절한 단어('{word}')가 포함되어 있습니다."
            
    return True, "안전한 콘텐츠입니다."