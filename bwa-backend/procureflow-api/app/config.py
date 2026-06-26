from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_cloud_project: str = "project-598daa32-4125-4a00-9ec"
    google_cloud_location: str = "asia-south1"
    firestore_database: str = "(default)"
    nasiko_base_url: str = "http://localhost:9100"
    agent_base_url: str = "http://localhost:8081"
    use_nasiko: bool = False


settings = Settings()
