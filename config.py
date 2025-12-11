"""Configuration management for MLS Comp Bot."""
from pydantic_settings import BaseSettings
from typing import Literal
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ATTOM API (only option now)
    # Note: MLS types removed - using ATTOM only
    
    # ATTOM API Settings (required)
    attom_api_key: str = ""
    
    # Estated API (optional - fallback for missing data)
    estated_api_key: str = ""
    estated_enabled: bool = False  # Set to True to enable Estated as fallback
    
    # Oxylabs Web Scraper API (optional - fallback for missing data via scraping)
    oxylabs_username: str = ""
    oxylabs_password: str = ""
    oxylabs_enabled: bool = False  # Set to True to enable Oxylabs as fallback
    
    # PropertyRadar API (optional - investor data: equity, liens, ownership)
    propertyradar_api_key: str = ""
    propertyradar_enabled: bool = False  # Set to True to enable PropertyRadar
    
    # Broker/Agent Branding for Reports
    broker_name: str = "Dallas Wormley"
    broker_title: str = "Designated Broker"
    broker_company: str = "R&I Realty"
    broker_phone: str = "480-433-2744"
    broker_email: str = "dallas@reliabilityrealtyaz.com"
    broker_website: str = "www.reliabilityrealtyaz.com"
    broker_tagline: str = "Residential • Commercial • Investment"
    broker_logo_path: str = "static/broker_logo.png"
    
    # Google Maps API (optional - for Street View images)
    google_maps_api_key: str = ""
    
    # Email Settings (optional - for sending reports)
    email_enabled: bool = False
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_smtp_username: str = ""
    email_smtp_password: str = ""
    email_from_address: str = ""
    email_from_name: str = "MLS Comp Bot"
    
    # Database
    database_url: str = "sqlite:///mls_comp_bot.db"
    
    # Comp Analysis Settings
    enable_learning: bool = True
    min_comp_score: float = 0.7
    max_comp_distance_miles: float = 5.0
    max_comp_age_days: int = 180
    max_comps_to_return: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

