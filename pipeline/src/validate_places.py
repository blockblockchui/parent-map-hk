"""
Place validation with cheap checks first, LLM only when needed
Implements Evidence-first principle
"""

import re
import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urlparse

from .config import config
from .models import Place, PlaceExtract, PlaceValidation, PlaceStatus, ValidationStage, RiskTier, Evidence
from .http_client import HttpClient
from .cache import cache, compute_content_hash


class CheapValidator:
    """
    Low-cost validation checks that don't require LLM
    """
    
    def __init__(self):
        self.client = HttpClient()
    
    async def validate(self, place: Place) -> PlaceValidation:
        """
        Run cheap validation checks
        Returns validation result with evidence
        """
        validation = PlaceValidation(
            place_id=place.place_id,
            checked_at=datetime.utcnow(),
        )
        
        # 1. Check website URL
        if place.website_url:
            url_check = await self.client.check_url(str(place.website_url))
            validation.http_status = url_check.get("status_code")
            validation.http_ok = url_check.get("status_code") in [200, 301, 302]
            
            if validation.http_ok:
                # Fetch and hash content
                try:
                    async with self.client as client:
                        response = await client.get(str(place.website_url), use_cache=True)
                        content_hash = compute_content_hash(response.text[:5000])
                        validation.content_hash = content_hash
                        
                        # Check if hash changed
                        cache_key = f"content_hash:{place.place_id}"
                        if cache.has_hash_changed(cache_key, content_hash):
                            validation.content_hash_changed = True
                            cache.set(cache_key, {}, content_hash=content_hash)
                        
                        # Extract Last-Modified/ETag
                        validation.last_modified = self._parse_last_modified(
                            response.headers.get("last-modified")
                        )
                        validation.etag = response.headers.get("etag")
                        
                except Exception as e:
                    # Content fetch failed, but HTTP check passed
                    pass
        
        # 2. Check social media activity
        if place.facebook_url:
            # Note: This is a simplified check - real implementation would use Facebook API
            fb_check = await self.client.check_url(str(place.facebook_url))
            if fb_check.get("status_code") == 200:
                validation.social_active = True
        
        # 3. Check if essential fields are present
        missing_fields = []
        if not place.address:
            missing_fields.append("address")
        if not place.website_url and not place.facebook_url:
            missing_fields.append("contact")
        if not place.description or len(place.description) < 20:
            missing_fields.append("description")
        
        validation.llm_missing_fields = missing_fields
        
        # 4. Determine validation stage and risk
        if validation.http_ok and not missing_fields:
            validation.validation_stage = ValidationStage.CHEAP_PASS
            validation.confidence = 70
            validation.risk_tier = RiskTier.LOW
        elif validation.http_status in [404, 410]:
            validation.validation_stage = ValidationStage.CHEAP_FAIL
            validation.status = PlaceStatus.SUSPECTED_CLOSED
            validation.confidence = 50
            validation.risk_tier = RiskTier.HIGH
        else:
            validation.validation_stage = ValidationStage.SEARCH_FLAG
            validation.confidence = 40
            validation.risk_tier = RiskTier.MEDIUM
        
        return validation
    
    def _parse_last_modified(self, header: Optional[str]) -> Optional[datetime]:
        """Parse Last-Modified header"""
        if not header:
            return None
        
        # Try common formats
        formats = [
            "%a, %d %b %Y %H:%M:%S GMT",
            "%Y-%m-%dT%H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(header, fmt)
            except:
                continue
        
        return None


class SearchValidator:
    """
    Search-based validation with evidence collection
    """
    
    def __init__(self):
        self.client = HttpClient()
    
    async def search_evidence(
        self,
        place: Place,
        query_terms: List[str] = None
    ) -> List[Evidence]:
        """
        Search for evidence about a place
        Returns list of evidence URLs with snippets
        """
        if query_terms is None:
            query_terms = self._build_search_query(place)
        
        evidence_list = []
        
        # This would integrate with Bing/Google Search API
        # For now, return placeholder evidence
        # TODO: Implement actual search API integration
        
        return evidence_list
    
    def _build_search_query(self, place: Place) -> List[str]:
        """Build search queries for evidence collection"""
        queries = []
        
        base_name = place.name
        district = place.district or ""
        
        # Basic query
        queries.append(f"{base_name} {district}")
        
        # Closure check
        queries.append(f"{base_name} 結業 停止營業")
        
        # Opening hours
        queries.append(f"{base_name} 營業時間 2026")
        
        # Recent news
        queries.append(f"{base_name} {district} 2025 2026")
        
        return queries


class LLMValidator:
    """
    LLM-based validation for complex cases
    Only used when cheap checks are inconclusive
    """
    
    def __init__(self):
        self.model = config.validation.llm_model
    
    async def analyze(
        self,
        place: Place,
        evidence_list: List[Evidence],
        validation: PlaceValidation
    ) -> PlaceValidation:
        """
        Use LLM to analyze evidence and make judgment
        """
        # Build prompt
        prompt = self._build_prompt(place, evidence_list)
        
        # Call LLM
        try:
            result = await self._call_llm(prompt)
            
            # Parse result
            if result.get("needs_review"):
                validation.status = PlaceStatus.NEEDS_REVIEW
                validation.llm_needs_review = True
            elif result.get("status") == "closed":
                validation.status = PlaceStatus.CLOSED
            elif result.get("status") == "suspected_closed":
                validation.status = PlaceStatus.SUSPECTED_CLOSED
            else:
                validation.status = PlaceStatus.OPEN
            
            validation.llm_summary = result.get("summary", "")
            validation.llm_rationale = result.get("rationale", "")
            validation.confidence = result.get("confidence", 50)
            validation.validation_stage = ValidationStage.LLM_FLAG
            
        except Exception as e:
            # LLM failed, mark for review
            validation.status = PlaceStatus.NEEDS_REVIEW
            validation.llm_needs_review = True
            validation.validation_stage = ValidationStage.LLM_FLAG
        
        return validation
    
    def _build_prompt(self, place: Place, evidence_list: List[Evidence]) -> str:
        """Build LLM prompt with evidence"""
        
        evidence_text = ""
        for i, ev in enumerate(evidence_list[:5], 1):
            evidence_text += f"\nEvidence {i}:\n"
            evidence_text += f"URL: {ev.url}\n"
            evidence_text += f"Snippet: {ev.snippet[:300]}\n"
        
        prompt = f"""You are a data validator for a Hong Kong parent-child activity directory.

Analyze the following evidence about "{place.name}" in {place.district} and determine its status.

PLACE DETAILS:
- Name: {place.name}
- Address: {place.address or "Unknown"}
- Website: {place.website_url or "None"}
- Previous status: {place.status.value}

EVIDENCE:
{evidence_text}

TASK:
1. Determine if the place is: OPEN, CLOSED, SUSPECTED_CLOSED, or NEEDS_REVIEW
2. Provide a summary (max 100 words)
3. Provide rationale (max 200 words)
4. Rate confidence 0-100

RULES:
- Only mark CLOSED if official announcement or credible media report found
- Mark SUSPECTED_CLOSED if multiple indicators suggest closure but no official confirmation
- Mark NEEDS_REVIEW if insufficient evidence
- Be conservative - false positives are worse than false negatives

Respond in JSON format:
{{
  "status": "OPEN|CLOSED|SUSPECTED_CLOSED|NEEDS_REVIEW",
  "summary": "...",
  "rationale": "...",
  "confidence": 75,
  "needs_review": false,
  "supporting_urls": ["..."]
}}
"""
        return prompt
    
    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """Call LLM API"""
        # This would call OpenAI or Anthropic API
        # For now, return placeholder
        # TODO: Implement actual LLM call
        
        return {
            "status": "NEEDS_REVIEW",
            "summary": "LLM analysis not implemented yet",
            "rationale": "Please implement LLM API integration",
            "confidence": 0,
            "needs_review": True,
            "supporting_urls": []
        }


class PlaceValidator:
    """
    Main validation orchestrator
    Implements "cheap checks before LLM" principle
    """
    
    def __init__(self):
        self.cheap_validator = CheapValidator()
        self.search_validator = SearchValidator()
        self.llm_validator = LLMValidator()
    
    async def validate_place(self, place: Place) -> PlaceValidation:
        """
        Validate a place using the full pipeline:
        1. Cheap checks (HTTP, hash, fields)
        2. Search for evidence (if needed)
        3. LLM analysis (if still unclear)
        """
        # Step 1: Cheap checks
        validation = await self.cheap_validator.validate(place)
        
        # If cheap checks passed clearly, we're done
        if validation.validation_stage == ValidationStage.CHEAP_PASS:
            validation.status = PlaceStatus.OPEN
            validation.next_check_at = self._calculate_next_check(validation.risk_tier)
            return validation
        
        # Step 2: Search for evidence
        evidence_list = await self.search_validator.search_evidence(place)
        validation.evidence_urls = [str(e.url) for e in evidence_list]
        validation.evidence_snippets = [e.snippet for e in evidence_list]
        
        # If we have evidence, proceed to LLM
        if evidence_list:
            validation = await self.llm_validator.analyze(place, evidence_list, validation)
        else:
            # No evidence, mark for review
            validation.status = PlaceStatus.NEEDS_REVIEW
            validation.llm_needs_review = True
        
        # Calculate next check time
        validation.next_check_at = self._calculate_next_check(validation.risk_tier)
        
        return validation
    
    async def validate_new_place(self, extract: PlaceExtract) -> Tuple[Place, PlaceValidation]:
        """
        Validate a newly extracted place
        """
        # Convert extract to place
        place = self._extract_to_place(extract)
        
        # Run validation
        validation = await self.validate_place(place)
        
        # Update place with validation results
        place.status = validation.status
        place.validation_stage = validation.validation_stage
        place.confidence = validation.confidence
        place.risk_tier = validation.risk_tier
        place.evidence_urls = validation.evidence_urls
        place.evidence_snippets = validation.evidence_snippets
        place.last_checked_at = validation.checked_at
        place.next_check_at = validation.next_check_at
        
        return place, validation
    
    def _extract_to_place(self, extract: PlaceExtract) -> Place:
        """Convert PlaceExtract to Place"""
        from slugify import slugify
        
        return Place(
            place_id=str(uuid.uuid4()),
            slug=slugify(extract.name, allow_unicode=True)[:50],
            name=extract.name,
            name_en=extract.name_en,
            region=extract.region or "hk-island",
            district=extract.district or "",
            address=extract.address,
            category=extract.category,
            indoor=extract.indoor,
            age_min=extract.age_min,
            age_max=extract.age_max,
            age_range=[extract.age_min or 0, extract.age_max or 6],
            price_description=extract.price_note,
            description=extract.description or "",
            website_url=extract.website_url,
            facebook_url=extract.facebook_url,
            instagram_url=extract.instagram_url,
            source_urls=[str(extract.source_url)],
            published_at=extract.published_at,
            extracted_at=extract.extracted_at,
            status=PlaceStatus.PENDING_REVIEW,
            auto_discovered=True,
        )
    
    def _calculate_next_check(self, risk_tier: RiskTier) -> datetime:
        """Calculate next check time based on risk tier"""
        now = datetime.utcnow()
        
        if risk_tier == RiskTier.HIGH:
            days = config.risk_tier_high_days
        elif risk_tier == RiskTier.MEDIUM:
            days = config.risk_tier_medium_days
        else:
            days = config.risk_tier_low_days
        
        return now + timedelta(days=days)


# Import needed for slugify
import uuid as uuid_module
uuid = uuid_module
