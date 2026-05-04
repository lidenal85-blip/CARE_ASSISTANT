from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    telegram_bot_token: str = ""
    EDAMAM_NUTR_ID: str = ""
    EDAMAM_NUTR_KEY: str = ""
    SPOONACULAR_KEY: str = ""
    
    def model_post_init(self, __context):
        # Если BOT_TOKEN пустой — берём из telegram_bot_token
        if not self.BOT_TOKEN and self.telegram_bot_token:
            object.__setattr__(self, 'BOT_TOKEN', self.telegram_bot_token)
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow"
    }

settings = Settings()
