"""
Pydantic models for Parent Map HK Data Pipeline
Schema definitions for places, validation results, and evidence
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, validator


class PlaceStatus(str, Enum):
    """Status of a place in the pipeline"""
    PENDING_REVIEW = "PendingReview"
    NEEDS_REVIEW = "NeedsReview"
    ALERT = "Alert"
    SUSPECTED_CLOSED = "SuspectedClosed"
    CLOSED = "Closed"
    OPEN = "Open"


class RiskTier(str, Enum):
    """Risk tier for freshness check scheduling"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ValidationStage(str, Enum):
    """Validation stage in the pipeline"""
    EXTRACTED = "extracted"
    CHEAP_PASS = "cheap_pass"
    CHEAP_FAIL = "cheap_fail"
    SEARCH_FLAG = "search_flag"
    LLM_FLAG = "llm_flag"
    HUMAN_CONFIRMED = "human_confirmed"


class Evidence(BaseModel):
    """Evidence for a claim about a place"""
    url: HttpUrl
    snippet: str = Field(..., max_length=1000)
    title: Optional[str] = None
    published_at: Optional[datetime] = None
    accessed_at: datetime = Field(default_factory=datetime.utcnow)
    evidence_type: str = Field(default="web")  # web, social, official


class PlaceExtract(BaseModel):
    """Raw extraction from a source"""
    # Identification
    name: str = Field(..., min_length=2, max_length=100)
    name_en: Optional[str] = None
    
    # Location
    address: Optional[str] = None
    district: Optional[str] = None
    region: Optional[str] = None  # hk-island, kowloon, nt
    
    # Details
    category: str = Field(default="playhouse")  # playhouse, park, museum, etc.
    indoor: bool = Field(default=True)
    age_min: Optional[int] = Field(None, ge=0, le=18)
    age_max: Optional[int] = Field(None, ge=0, le=18)
    price_note: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    
    # Links
    website_url: Optional[HttpUrl] = None
    facebook_url: Optional[HttpUrl] = None
    instagram_url: Optional[str] = None
    
    # Source tracking
    source_url: HttpUrl
    source_name: str
    published_at: Optional[datetime] = None
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Content for deduplication
    content_hash: Optional[str] = None
    
    class Config:
        extra = "allow"


class PlaceValidation(BaseModel):
    """Validation result for a place"""
    place_id: str
    
    # HTTP checks
    http_status: Optional[int] = None
    http_ok: Optional[bool] = None
    http_checked_at: Optional[datetime] = None
    
    # Content checks
    content_hash: Optional[str] = None
    content_hash_changed: bool = False
    last_modified: Optional[datetime] = None
    etag: Optional[str] = None
    
    # Social checks
    social_last_post: Optional[datetime] = None
    social_active: Optional[bool] = None
    
    # Evidence
    evidence_urls: List[str] = Field(default_factory=list)
    evidence_snippets: List[str] = Field(default_factory=list)
    
    # LLM analysis
    llm_summary: Optional[str] = None
    llm_rationale: Optional[str] = Field(None, max_length=200)
    llm_needs_review: bool = False
    llm_missing_fields: List[str] = Field(default_factory=list)
    
    # Classification
    confidence: int = Field(0, ge=0, le=100)
    risk_tier: RiskTier = RiskTier.MEDIUM
    
    # Status
    status: PlaceStatus = PlaceStatus.PENDING_REVIEW
    validation_stage: ValidationStage = ValidationStage.EXTRACTED
    
    # Timing
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    next_check_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        extra = "allow"


class Place(BaseModel):
    """Full place record (as stored in Google Sheets / output JSON)"""
    # Core IDs
    place_id: str = Field(..., description="UUID, immutable")
    slug: str = Field(..., description="URL-friendly name")
    
    # Names
    name: str = Field(..., min_length=2, max_length=100)
    name_en: Optional[str] = None
    
    # Location
    region: str = Field(..., description="hk-island, kowloon, nt")
    district: str
    address: Optional[str] = None
    lat: Optional[float] = Field(None, ge=22.0, le=23.0)  # Hong Kong bounds
    lng: Optional[float] = Field(None, ge=113.0, le=115.0)
    geocode_confidence: Optional[str] = None
    geocode_provider: Optional[str] = None
    
    # Details
    category: str = "playhouse"
    indoor: bool = True
    age_min: Optional[int] = Field(None, ge=0, le=18)
    age_max: Optional[int] = Field(None, ge=0, le=18)
    age_range: List[int] = Field(default_factory=lambda: [0, 6])
    
    # Pricing
    price_tier: Optional[str] = None  # free, low, medium, high
    price_description: Optional[str] = None
    
    # Description
    description: str = Field(default="", max_length=500)
    tips: Optional[str] = None
    
    # Facilities
    facilities: List[str] = Field(default_factory=list)
    has_baby_room: bool = False
    has_stroller_access: bool = True
    has_restaurant: bool = False
    rainy_day_suitable: bool = True
    
    # Hours
    opening_hours: str = "請查詢官網"
    
    # Links
    website_url: Optional[HttpUrl] = None
    affiliate_url: Optional[HttpUrl] = None
    facebook_url: Optional[HttpUrl] = None
    instagram_url: Optional[str] = None
    
    # Pipeline status
    status: PlaceStatus = PlaceStatus.PENDING_REVIEW
    validation_stage: ValidationStage = ValidationStage.EXTRACTED
    confidence: int = Field(0, ge=0, le=100)
    
    # Evidence & Sources
    evidence_urls: List[str] = Field(default_factory=list)
    evidence_snippets: List[str] = Field(default_factory=list)
    source_urls: List[str] = Field(default_factory=list)
    
    # Timing
    published_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_checked_at: Optional[datetime] = None
    next_check_at: Optional[datetime] = None
    
    # Review tracking
    review_owner: Optional[str] = None
    review_due_at: Optional[datetime] = None
    resolution: Optional[str] = None
    false_alarm_reason: Optional[str] = None
    
    # Frontend fields
    verified: bool = False
    auto_discovered: bool = True
    
    @validator('age_range', always=True)
    def set_age_range(cls, v, values):
        """Derive age_range from age_min/age_max"""
        if 'age_min' in values and 'age_max' in values:
            if values['age_min'] is not None and values['age_max'] is not None:
                return [values['age_min'], values['age_max']]
        return v
    
    def to_frontend_dict(self) -> Dict[str, Any]:
        """Convert to frontend-friendly format"""
        return {
            "id": self.place_id,
            "name": self.name,
            "nameEn": self.name_en,
            "district": self.district,
            "region": self.region,
            "lat": self.lat,
            "lng": self.lng,
            "category": self.category,
            "indoor": self.indoor,
            "ageRange": self.age_range,
            "priceType": self.price_tier or "medium",
            "priceDescription": self.price_description or "$100-200",
            "description": self.description,
            "website": str(self.website_url) if self.website_url else None,
            "tips": self.tips,
            "openingHours": self.opening_hours,
            "address": self.address,
            "hasBabyRoom": self.has_baby_room,
            "hasStrollerAccess": self.has_stroller_access,
            "hasRestaurant": self.has_restaurant,
            "rainyDaySuitable": self.rainy_day_suitable,
            "verified": self.verified and self.status == PlaceStatus.OPEN,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class PipelineRun(BaseModel):
    """Record of a pipeline execution"""
    run_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    stage: str = "started"  # started, ingesting, validating, exporting, completed, failed
    
    # Statistics
    sources_checked: int = 0
    places_extracted: int = 0
    places_validated: int = 0
    places_added: int = 0
    places_updated: int = 0
    places_flagged: int = 0
    errors: List[str] = Field(default_factory=list)
    
    class Config:
        extra = "allow"
