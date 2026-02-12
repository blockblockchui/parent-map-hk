"""
Configuration management for the data pipeline
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()


@dataclass
class SourceConfig:
    """Configuration for a data source"""
    name: str
    type: str  # rss, sitemap, tag_page, manual
    url: Optional[str] = None
    selectors: Optional[Dict[str, str]] = None
    recency_window_days: int = 30
    category_keywords: List[str] = None
    enabled: bool = True
    pagination: bool = False
    max_pages: int = 1
    sheet_tab: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ValidationConfig:
    """Configuration for validation"""
    http_timeout: int = 10
    http_retries: int = 3
    content_hash_algorithm: str = "sha256"
    hash_cache_ttl_hours: int = 24
    min_evidence_urls: int = 1
    max_evidence_age_days: int = 180
    llm_model: str = "gpt-4o-mini"
    llm_max_tokens: int = 1000
    llm_temperature: float = 0.1


@dataclass
class ExportConfig:
    """Configuration for export"""
    output_path: str = "../data/locations.json"
    dry_run: bool = False
    git_auto_commit: bool = False
    git_commit_message: str = "Update locations.json {date}"
    output_fields: List[str] = None


class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config"
        self.cache_dir = self.base_dir / "cache"
        self.logs_dir = self.base_dir / "logs"
        
        # Ensure directories exist
        self.cache_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Load sources.yaml
        self.sources_config = self._load_sources()
        self.validation = self._load_validation()
        self.export = self._load_export()
        
        # Environment variables
        self.google_sheets_id = os.getenv("GOOGLE_SHEETS_ID")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.bing_api_key = os.getenv("BING_API_KEY")
        
        # Pipeline settings
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.cache_ttl_hours = int(os.getenv("CACHE_TTL_HOURS", "24"))
        self.max_concurrent_requests = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "10"))
        self.rate_limit_per_minute = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "30"))
        
        # Freshness check intervals
        self.risk_tier_high_days = int(os.getenv("RISK_TIER_HIGH_DAYS", "7"))
        self.risk_tier_medium_days = int(os.getenv("RISK_TIER_MEDIUM_DAYS", "14"))
        self.risk_tier_low_days = int(os.getenv("RISK_TIER_LOW_DAYS", "60"))
    
    def _load_sources(self) -> List[SourceConfig]:
        """Load sources from YAML"""
        sources_file = self.config_dir / "sources.yaml"
        if not sources_file.exists():
            return []
        
        with open(sources_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        sources = []
        for src in data.get('sources', []):
            sources.append(SourceConfig(
                name=src['name'],
                type=src['type'],
                url=src.get('url'),
                selectors=src.get('selectors'),
                recency_window_days=src.get('recency_window_days', 30),
                category_keywords=src.get('category_keywords', []),
                enabled=src.get('enabled', True),
                pagination=src.get('pagination', False),
                max_pages=src.get('max_pages', 1),
                sheet_tab=src.get('sheet_tab'),
                description=src.get('description'),
            ))
        return sources
    
    def _load_validation(self) -> ValidationConfig:
        """Load validation config from YAML"""
        sources_file = self.config_dir / "sources.yaml"
        if not sources_file.exists():
            return ValidationConfig()
        
        with open(sources_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        val = data.get('validation', {})
        return ValidationConfig(
            http_timeout=val.get('http_timeout', 10),
            http_retries=val.get('http_retries', 3),
            content_hash_algorithm=val.get('content_hash_algorithm', 'sha256'),
            hash_cache_ttl_hours=val.get('hash_cache_ttl_hours', 24),
            min_evidence_urls=val.get('min_evidence_urls', 1),
            max_evidence_age_days=val.get('max_evidence_age_days', 180),
            llm_model=val.get('llm_model', 'gpt-4o-mini'),
            llm_max_tokens=val.get('llm_max_tokens', 1000),
            llm_temperature=val.get('llm_temperature', 0.1),
        )
    
    def _load_export(self) -> ExportConfig:
        """Load export config from YAML"""
        sources_file = self.config_dir / "sources.yaml"
        if not sources_file.exists():
            return ExportConfig()
        
        with open(sources_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        exp = data.get('export', {})
        return ExportConfig(
            output_path=exp.get('output_path', '../data/locations.json'),
            dry_run=exp.get('dry_run', False),
            git_auto_commit=exp.get('git_auto_commit', False),
            git_commit_message=exp.get('git_commit_message', 'Update locations.json {date}'),
            output_fields=exp.get('output_fields'),
        )
    
    def get_enabled_sources(self) -> List[SourceConfig]:
        """Get only enabled sources"""
        return [s for s in self.sources_config if s.enabled]
    
    def get_source_by_name(self, name: str) -> Optional[SourceConfig]:
        """Get a source by name"""
        for src in self.sources_config:
            if src.name == name:
                return src
        return None


# Global config instance
config = Config()
