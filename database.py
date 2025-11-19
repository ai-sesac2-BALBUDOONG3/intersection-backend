from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# [ ⚡️ 1. '비밀 쪽지' 도구들 가져오기 ]
from dotenv import load_dotenv
import os

# [ ⚡️ 2. '.env' 파일에서 '비밀 쪽지'를 읽어오기 ]
load_dotenv() 

# [ ⚡️ 3. '비밀 쪽지'에서 "DATABASE_URL" 항목을 찾아오기 ]
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()