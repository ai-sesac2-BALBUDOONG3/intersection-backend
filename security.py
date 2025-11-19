from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone # '시간' 관련 도구
from jose import JWTError, jwt # '출입증(JWT)' 도구
from dotenv import load_dotenv # '비밀 쪽지' 도구
import os

load_dotenv()  # '.env' 파일에서 '비밀 쪽지'를 읽어오기

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# 1. 사용할 암호화 방식을 정합니다. "argon2" 방식을 쓸 겁니다.
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# 2. 비밀번호가 맞는지 확인하는 '확인기'
def verify_password(plain_password, hashed_password):
    """손님이 입력한 '원본 비번'과 창고의 '암호화된 비번'을 비교합니다."""
    return pwd_context.verify(plain_password, hashed_password)

# 3. 비밀번호를 암호화하는 '암호화기'
def get_password_hash(password):
    """손님이 입력한 '원본 비번'을 '암호화된 비번'으로 바꿉니다."""
    return pwd_context.hash(password)

# 4. '출입증(JWT)' 생성기
def create_access_token(data: dict):
    """'출입증(JWT)'을 생성합니다."""
    
    # 1.'출입증' 담을 '정보'를 복사
    to_encode = data.copy()
    
    # 2. '출입증' 만료 시간 설정 (지금 시간 + 30분)
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # 3. '만료 시간' 정보를 '출입증'에 추가
    to_encode.update({"exp": expire})


    # 4. '출입증'을 '암호화'합니다.
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    # 5. '암호화된 출입증'을 반환합니다.
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    """
    '출입증'이 위조되지 않았는지, 만료되진 않았는지 검사합니다.
    성공하면 -> '출입증' 안의 '정보(payload)'를 돌려줍니다.
    실패하면 -> '예외(credentials_exception)'를 발생시킵니다.
    """
    try:
        # 1. '비밀 열쇠'로 '출입증'을 '해독'합니다.
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # 2. '출입증'에서 '이메일(sub)' 정보를 꺼냅니다.
        email: str = payload.get("sub")

        # 3. 이메일 정보가 없으면, '가짜 출입증'으로 간주합니다.
        if email is None:
            raise credentials_exception

        # 4. '출입증' 안의 정보(payload)를 반환합니다.
        return payload

    except JWTError: # '해독' 자체에 실패했다면 (만료, 위조 등)
        # '가짜 출입증'으로 간주합니다.
        raise credentials_exception