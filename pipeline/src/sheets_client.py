"""
Google Sheets client for staging and CMS
Handles read/write operations with the Google Sheets API
"""

import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from .config import config
from .models import Place, PlaceStatus, RiskTier, ValidationStage


class SheetsClient:
    """Client for Google Sheets operations"""
    
    # Sheet column mapping
    COLUMNS = [
        "place_id",
        "slug",
        "name",
        "name_en",
        "region",
        "district",
        "address",
        "lat",
        "lng",
        "geocode_confidence",
        "category",
        "indoor",
        "age_min",
        "age_max",
        "price_tier",
        "price_description",
        "description",
        "tips",
        "facilities",
        "opening_hours",
        "website_url",
        "facebook_url",
        "instagram_url",
        "status",
        "validation_stage",
        "confidence",
        "risk_tier",
        "evidence_urls",
        "evidence_snippets",
        "source_urls",
        "published_at",
        "updated_at",
        "last_checked_at",
        "next_check_at",
        "review_owner",
        "review_due_at",
        "resolution",
        "false_alarm_reason",
    ]
    
    def __init__(self):
        self.spreadsheet_id = config.google_sheets_id
        self.client = self._authenticate()
        self.sheet = self.client.open_by_key(self.spreadsheet_id)
    
    def _authenticate(self):
        """Authenticate with Google Sheets API"""
        # Try service account first
        creds_path = config.base_dir / "credentials.json"
        
        if creds_path.exists():
            creds = Credentials.from_service_account_file(
                str(creds_path),
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ]
            )
            return gspread.authorize(creds)
        
        # Fall back to OAuth (for local development)
        # This would require a token.json file
        raise FileNotFoundError(
            f"credentials.json not found at {creds_path}. "
            "Please download service account credentials from Google Cloud Console."
        )
    
    def get_worksheet(self, sheet_name: str = "Places"):
        """Get or create a worksheet"""
        try:
            return self.sheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            # Create new worksheet with headers
            ws = self.sheet.add_worksheet(sheet_name, rows=1000, cols=len(self.COLUMNS))
            ws.append_row(self.COLUMNS)
            return ws
    
    def _place_to_row(self, place: Place) -> list:
        """Convert Place model to sheet row"""
        return [
            place.place_id,
            place.slug,
            place.name,
            place.name_en or "",
            place.region,
            place.district,
            place.address or "",
            place.lat or "",
            place.lng or "",
            place.geocode_confidence or "",
            place.category,
            "TRUE" if place.indoor else "FALSE",
            place.age_min or "",
            place.age_max or "",
            place.price_tier or "",
            place.price_description or "",
            place.description,
            place.tips or "",
            ",".join(place.facilities),
            place.opening_hours,
            str(place.website_url) if place.website_url else "",
            str(place.facebook_url) if place.facebook_url else "",
            place.instagram_url or "",
            place.status.value,
            place.validation_stage.value,
            place.confidence,
            place.risk_tier.value if place.risk_tier else "medium",
            ",".join(place.evidence_urls),
            " | ".join(place.evidence_snippets)[:500],  # Truncate for sheet
            ",".join(place.source_urls),
            place.published_at.isoformat() if place.published_at else "",
            place.updated_at.isoformat() if place.updated_at else "",
            place.last_checked_at.isoformat() if place.last_checked_at else "",
            place.next_check_at.isoformat() if place.next_check_at else "",
            place.review_owner or "",
            place.review_due_at.isoformat() if place.review_due_at else "",
            place.resolution or "",
            place.false_alarm_reason or "",
        ]
    
    def _row_to_place(self, row: list) -> Place:
        """Convert sheet row to Place model"""
        data = dict(zip(self.COLUMNS, row))
        
        return Place(
            place_id=data.get("place_id", str(uuid.uuid4())),
            slug=data.get("slug", ""),
            name=data.get("name", ""),
            name_en=data.get("name_en") or None,
            region=data.get("region", ""),
            district=data.get("district", ""),
            address=data.get("address") or None,
            lat=float(data["lat"]) if data.get("lat") else None,
            lng=float(data["lng"]) if data.get("lng") else None,
            geocode_confidence=data.get("geocode_confidence") or None,
            category=data.get("category", "playhouse"),
            indoor=data.get("indoor", "TRUE").upper() == "TRUE",
            age_min=int(data["age_min"]) if data.get("age_min") else None,
            age_max=int(data["age_max"]) if data.get("age_max") else None,
            price_tier=data.get("price_tier") or None,
            price_description=data.get("price_description") or None,
            description=data.get("description", ""),
            tips=data.get("tips") or None,
            facilities=[f.strip() for f in data.get("facilities", "").split(",") if f.strip()],
            opening_hours=data.get("opening_hours", "請查詢官網"),
            website_url=data.get("website_url") or None,
            facebook_url=data.get("facebook_url") or None,
            instagram_url=data.get("instagram_url") or None,
            status=PlaceStatus(data.get("status", "PendingReview")),
            validation_stage=ValidationStage(data.get("validation_stage", "extracted")),
            confidence=int(data.get("confidence", 0)) if data.get("confidence") else 0,
            risk_tier=RiskTier(data.get("risk_tier", "medium")),
            evidence_urls=[u.strip() for u in data.get("evidence_urls", "").split(",") if u.strip()],
            evidence_snippets=[s.strip() for s in data.get("evidence_snippets", "").split(" | ") if s.strip()],
            source_urls=[u.strip() for u in data.get("source_urls", "").split(",") if u.strip()],
            published_at=datetime.fromisoformat(data["published_at"]) if data.get("published_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            last_checked_at=datetime.fromisoformat(data["last_checked_at"]) if data.get("last_checked_at") else None,
            next_check_at=datetime.fromisoformat(data["next_check_at"]) if data.get("next_check_at") else None,
            review_owner=data.get("review_owner") or None,
            review_due_at=datetime.fromisoformat(data["review_due_at"]) if data.get("review_due_at") else None,
            resolution=data.get("resolution") or None,
            false_alarm_reason=data.get("false_alarm_reason") or None,
        )
    
    def get_all_places(self, sheet_name: str = "Places") -> List[Place]:
        """Get all places from sheet"""
        ws = self.get_worksheet(sheet_name)
        records = ws.get_all_records()
        
        places = []
        for record in records:
            try:
                place = self._dict_to_place(record)
                places.append(place)
            except Exception as e:
                print(f"Error parsing place: {e}")
                continue
        
        return places
    
    def _dict_to_place(self, data: Dict[str, Any]) -> Place:
        """Convert sheet dict to Place (handles type conversion)"""
        # Helper to parse boolean
        def parse_bool(val):
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.upper() in ("TRUE", "YES", "1")
            return bool(val)
        
        # Helper to parse datetime
        def parse_datetime(val):
            if not val:
                return None
            try:
                return datetime.fromisoformat(str(val).replace('Z', '+00:00'))
            except:
                return None
        
        return Place(
            place_id=str(data.get("place_id", uuid.uuid4())),
            slug=str(data.get("slug", "")),
            name=str(data.get("name", "")),
            name_en=data.get("name_en") or None,
            region=str(data.get("region", "")),
            district=str(data.get("district", "")),
            address=data.get("address") or None,
            lat=float(data["lat"]) if data.get("lat") else None,
            lng=float(data["lng"]) if data.get("lng") else None,
            category=str(data.get("category", "playhouse")),
            indoor=parse_bool(data.get("indoor", True)),
            age_min=int(data["age_min"]) if data.get("age_min") else None,
            age_max=int(data["age_max"]) if data.get("age_max") else None,
            price_tier=data.get("price_tier") or None,
            price_description=data.get("price_description") or None,
            description=str(data.get("description", "")),
            opening_hours=str(data.get("opening_hours", "請查詢官網")),
            website_url=data.get("website_url") or None,
            facebook_url=data.get("facebook_url") or None,
            instagram_url=data.get("instagram_url") or None,
            status=PlaceStatus(str(data.get("status", "PendingReview"))),
            validation_stage=ValidationStage(str(data.get("validation_stage", "extracted"))),
            confidence=int(data.get("confidence", 0)) or 0,
            risk_tier=RiskTier(str(data.get("risk_tier", "medium"))),
            evidence_urls=[u.strip() for u in str(data.get("evidence_urls", "")).split(",") if u.strip()],
            source_urls=[u.strip() for u in str(data.get("source_urls", "")).split(",") if u.strip()],
            published_at=parse_datetime(data.get("published_at")),
            updated_at=parse_datetime(data.get("updated_at")),
            last_checked_at=parse_datetime(data.get("last_checked_at")),
            next_check_at=parse_datetime(data.get("next_check_at")),
        )
    
    def add_place(self, place: Place, sheet_name: str = "Places") -> str:
        """Add a new place to sheet"""
        ws = self.get_worksheet(sheet_name)
        row = self._place_to_row(place)
        ws.append_row(row)
        return place.place_id
    
    def update_place(self, place: Place, sheet_name: str = "Places") -> bool:
        """Update existing place in sheet"""
        ws = self.get_worksheet(sheet_name)
        
        # Find row with matching place_id
        cell = ws.find(place.place_id)
        if not cell:
            return False
        
        # Update row
        row_num = cell.row
        row_data = self._place_to_row(place)
        
        # Update each cell
        for col_num, value in enumerate(row_data, start=1):
            ws.update_cell(row_num, col_num, value)
        
        return True
    
    def get_places_needing_review(
        self,
        sheet_name: str = "Places",
        status_filter: Optional[List[PlaceStatus]] = None
    ) -> List[Place]:
        """Get places that need human review"""
        all_places = self.get_all_places(sheet_name)
        
        if status_filter:
            return [p for p in all_places if p.status in status_filter]
        
        # Default: PendingReview, NeedsReview, Alert, SuspectedClosed
        review_statuses = [
            PlaceStatus.PENDING_REVIEW,
            PlaceStatus.NEEDS_REVIEW,
            PlaceStatus.ALERT,
            PlaceStatus.SUSPECTED_CLOSED,
        ]
        return [p for p in all_places if p.status in review_statuses]
    
    def get_places_for_freshness_check(
        self,
        sheet_name: str = "Places"
    ) -> List[Place]:
        """Get places where next_check_at <= now"""
        all_places = self.get_all_places(sheet_name)
        now = datetime.utcnow()
        
        return [
            p for p in all_places
            if p.next_check_at and p.next_check_at <= now
            and p.status not in (PlaceStatus.CLOSED,)
        ]
    
    def upsert_place(self, place: Place, sheet_name: str = "Places") -> str:
        """Insert or update place"""
        ws = self.get_worksheet(sheet_name)
        
        # Try to find existing
        try:
            cell = ws.find(place.place_id)
            if cell:
                self.update_place(place, sheet_name)
                return place.place_id
        except:
            pass
        
        # Add new
        return self.add_place(place, sheet_name)
    
    def create_filter_views(self):
        """Create suggested filter views (manual instructions)"""
        instructions = """
        # Google Sheets Filter Views Setup
        
        ## 1. 待審新地點 (PendingReview)
        - Column: status
        - Condition: Text is exactly "PendingReview"
        
        ## 2. 需人工覆核 (NeedsReview/Alert/SuspectedClosed)
        - Column: status
        - Condition: Text is one of "NeedsReview", "Alert", "SuspectedClosed"
        
        ## 3. 到期需校驗 (next_check_at <= today)
        - Column: next_check_at
        - Condition: Date is before or equal to today
        
        ## 4. 高風險地點 (high risk)
        - Column: risk_tier
        - Condition: Text is exactly "high"
        
        ## 5. 已結業 (Closed)
        - Column: status
        - Condition: Text is exactly "Closed"
        """
        return instructions
