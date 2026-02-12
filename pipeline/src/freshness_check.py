"""
Freshness check for existing places
Periodic validation to detect closures and updates
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from .config import config
from .models import Place, PlaceStatus, PlaceValidation, RiskTier
from .sheets_client import SheetsClient
from .validate_places import PlaceValidator
from .logging_utils import AuditLogger


class FreshnessChecker:
    """
    Check freshness of existing places
    Implements incremental processing (only check due places)
    """
    
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.sheets = SheetsClient()
        self.validator = PlaceValidator()
        self.audit = AuditLogger(run_id)
        
        # Statistics
        self.stats = {
            "checked": 0,
            "passed": 0,
            "flagged": 0,
            "updated": 0,
            "errors": 0,
        }
    
    async def run(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Run freshness check for all due places
        """
        print(f"Starting freshness check (run_id: {self.run_id})")
        
        # Get places needing check
        places = self.sheets.get_places_for_freshness_check()
        print(f"Found {len(places)} places due for check")
        
        if not places:
            return self.stats
        
        # Process in batches
        batch_size = config.max_concurrent_requests
        
        for i in range(0, len(places), batch_size):
            batch = places[i:i + batch_size]
            
            print(f"Processing batch {i//batch_size + 1}/{(len(places)-1)//batch_size + 1}")
            
            await asyncio.gather(*[
                self._check_place(place, dry_run)
                for place in batch
            ])
        
        # Print summary
        print(f"\nFreshness check complete:")
        print(f"  Checked: {self.stats['checked']}")
        print(f"  Passed: {self.stats['passed']}")
        print(f"  Flagged: {self.stats['flagged']}")
        print(f"  Updated: {self.stats['updated']}")
        print(f"  Errors: {self.stats['errors']}")
        
        return self.stats
    
    async def _check_place(self, place: Place, dry_run: bool = False):
        """Check a single place"""
        try:
            self.stats["checked"] += 1
            
            print(f"  Checking: {place.name} ({place.place_id})")
            
            # Run validation
            validation = await self.validator.validate_place(place)
            
            # Determine if status changed
            old_status = place.status
            new_status = validation.status
            
            # Check if anything changed
            status_changed = old_status != new_status
            hash_changed = validation.content_hash_changed
            
            if status_changed:
                self.stats["flagged"] += 1
                
                print(f"    ⚠️ Status changed: {old_status.value} -> {new_status.value}")
                
                # Log status change
                self.audit.log_status_change(
                    place_id=place.place_id,
                    old_status=old_status.value,
                    new_status=new_status.value,
                    reason=validation.llm_rationale or "Freshness check",
                    evidence_urls=validation.evidence_urls,
                )
                
                # Update place
                place.status = new_status
                place.validation_stage = validation.validation_stage
                place.confidence = validation.confidence
                place.risk_tier = validation.risk_tier
                
            elif hash_changed:
                self.stats["updated"] += 1
                print(f"    📝 Content changed (hash)")
                
                # Log update
                self.audit.log_validation(
                    place_id=place.place_id,
                    validation_stage=validation.validation_stage.value,
                    confidence=validation.confidence,
                    evidence_urls=validation.evidence_urls,
                )
                
            else:
                self.stats["passed"] += 1
                print(f"    ✓ No changes")
            
            # Update timestamps
            place.last_checked_at = validation.checked_at
            place.next_check_at = validation.next_check_at
            
            # Update evidence
            if validation.evidence_urls:
                place.evidence_urls = validation.evidence_urls
            if validation.evidence_snippets:
                place.evidence_snippets = validation.evidence_snippets
            
            # Save to sheets (unless dry run)
            if not dry_run:
                self.sheets.update_place(place)
            
        except Exception as e:
            self.stats["errors"] += 1
            print(f"    ❌ Error: {e}")
    
    def get_flagged_places_report(self) -> List[Dict[str, Any]]:
        """Generate report of flagged places for review"""
        # Get all places with Alert/SuspectedClosed status
        flagged = self.sheets.get_places_needing_review([
            PlaceStatus.ALERT,
            PlaceStatus.SUSPECTED_CLOSED,
        ])
        
        report = []
        for place in flagged:
            audit_entries = self.audit.get_entries(place.place_id)
            
            report.append({
                "place_id": place.place_id,
                "name": place.name,
                "district": place.district,
                "status": place.status.value,
                "confidence": place.confidence,
                "evidence_urls": place.evidence_urls,
                "last_checked": place.last_checked_at.isoformat() if place.last_checked_at else None,
                "audit_trail": audit_entries,
            })
        
        return report
    
    def export_flagged_report(self, filepath: str):
        """Export flagged places to CSV for manual review"""
        import csv
        
        report = self.get_flagged_places_report()
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "place_id", "name", "district", "status", "confidence",
                "evidence_urls", "last_checked"
            ])
            writer.writeheader()
            
            for item in report:
                writer.writerow({
                    "place_id": item["place_id"],
                    "name": item["name"],
                    "district": item["district"],
                    "status": item["status"],
                    "confidence": item["confidence"],
                    "evidence_urls": "; ".join(item["evidence_urls"]),
                    "last_checked": item["last_checked"],
                })
        
        print(f"Exported flagged report to {filepath}")


class RiskBasedScheduler:
    """
    Schedule freshness checks based on risk tier
    """
    
    def __init__(self):
        self.sheets = SheetsClient()
    
    def update_schedule_for_place(self, place: Place, validation: PlaceValidation):
        """Update check schedule based on validation results"""
        # Set next check based on risk tier
        place.next_check_at = self._calculate_next_check(validation.risk_tier)
        
        # Update risk tier
        place.risk_tier = validation.risk_tier
        
        # Save
        self.sheets.update_place(place)
    
    def _calculate_next_check(self, risk_tier: RiskTier) -> datetime:
        """Calculate next check time"""
        now = datetime.utcnow()
        
        if risk_tier == RiskTier.HIGH:
            days = config.risk_tier_high_days
        elif risk_tier == RiskTier.MEDIUM:
            days = config.risk_tier_medium_days
        else:
            days = config.risk_tier_low_days
        
        return now + timedelta(days=days)
    
    def rebalance_all_schedules(self):
        """
        Rebalance all place schedules
        Useful when changing risk tier parameters
        """
        places = self.sheets.get_all_places()
        
        for place in places:
            if place.status in (PlaceStatus.CLOSED, PlaceStatus.OPEN):
                # Calculate new schedule based on current risk tier
                place.next_check_at = self._calculate_next_check(place.risk_tier)
                self.sheets.update_place(place)
        
        print(f"Rebalanced {len(places)} place schedules")
