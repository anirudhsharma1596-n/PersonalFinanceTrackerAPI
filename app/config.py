from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 1440

    BASE_URL: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

if __name__ == "__main__":
    print(settings.model_dump())
    