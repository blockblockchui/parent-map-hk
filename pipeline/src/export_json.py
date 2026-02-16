"""
Export clean data from Sheets to JSON for frontend
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import config
from .models import Place, PlaceStatus
from .sheets_client import SheetsClient


class JSONExporter:
    """
    Export places from Google Sheets to clean JSON
    For frontend consumption
    """
    
    # Frontend field mapping
    FIELD_MAP = {
        "place_id": "id",
        "name": "name",
        "name_en": "nameEn",
        "district": "district",
        "region": "region",
        "lat": "lat",
        "lng": "lng",
        "category": "category",
        "indoor": "indoor",
        "age_range": "ageRange",
        "price_tier": "priceType",
        "price_description": "priceDescription",
        "description": "description",
        "tips": "tips",
        "opening_hours": "openingHours",
        "address": "address",
        "has_baby_room": "hasBabyRoom",
        "has_stroller_access": "hasStrollerAccess",
        "has_restaurant": "hasRestaurant",
        "rainy_day_suitable": "rainyDaySuitable",
        "verified": "verified",
        "updated_at": "updatedAt",
        "website_url": "website",
        "facebook_url": "facebook",
        "instagram_url": "instagram",
    }
    
    def __init__(self):
        self.sheets = SheetsClient()
        self.output_path = Path(config.export.output_path)
    
    def export(
        self,
        dry_run: bool = False,
        only_verified: bool = True,
        min_confidence: int = 50
    ) -> Dict[str, Any]:
        """
        Export places to JSON
        
        Args:
            dry_run: Only print what would be exported
            only_verified: Only export verified places
            min_confidence: Minimum confidence score
        """
        print(f"Starting export...")
        
        # Get all places
        all_places = self.sheets.get_all_places()
        print(f"Total places in Sheets: {len(all_places)}")
        
        # Filter places (include all non-closed places)
        filtered = self._filter_places(
            all_places,
            only_verified=False,
            min_confidence=0
        )
        print(f"Places after filtering: {len(filtered)}")
        
        # Convert to frontend format
        export_data = self._convert_to_frontend_format(filtered)
        
        # Add metadata
        output = {
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "total_count": len(export_data),
                "version": "1.0",
            },
            "locations": export_data,
        }
        
        if dry_run:
            print("\nDRY RUN - Would export:")
            print(f"  Output file: {self.output_path}")
            print(f"  Places: {len(export_data)}")
            print(f"  Sample: {export_data[0]['name'] if export_data else 'None'}")
            return {"exported": 0, "dry_run": True}
        
        # Write JSON file
        self._write_json(output)
        
        print(f"\n✓ Exported {len(export_data)} places to {self.output_path}")
        
        return {
            "exported": len(export_data),
            "total": len(all_places),
            "filtered_out": len(all_places) - len(filtered),
            "output_path": str(self.output_path),
        }
    
    def _filter_places(
        self,
        places: List[Place],
        only_verified: bool = True,
        min_confidence: int = 50
    ) -> List[Place]:
        """Filter places based on criteria"""
        filtered = []
        
        for place in places:
            # Skip closed places
            if place.status == PlaceStatus.CLOSED:
                continue
            
            # Skip pending review (unless specifically included)
            if place.status == PlaceStatus.PENDING_REVIEW and only_verified:
                continue
            
            # Check confidence
            if place.confidence < min_confidence:
                continue
            
            # Must have location data
            if not place.lat or not place.lng:
                continue
            
            filtered.append(place)
        
        return filtered
    
    def _convert_to_frontend_format(self, places: List[Place]) -> List[Dict[str, Any]]:
        """Convert Place models to frontend format"""
        result = []
        
        for place in places:
            # Use the built-in to_frontend_dict method
            frontend_dict = place.to_frontend_dict()
            result.append(frontend_dict)
        
        return result
    
    def _write_json(self, data: Dict[str, Any]):
        """Write data to JSON file"""
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write with proper formatting
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2,
                default=str
            )
    
    def git_commit_and_push(self, auto_push: bool = False) -> bool:
        """
        Commit and push changes to git
        """
        try:
            # Check if there are changes
            result = subprocess.run(
                ["git", "status", "--porcelain", str(self.output_path)],
                capture_output=True,
                text=True,
                cwd=self.output_path.parent.parent  # Repo root
            )
            
            if not result.stdout.strip():
                print("No changes to commit")
                return True
            
            # Add file
            subprocess.run(
                ["git", "add", str(self.output_path)],
                check=True,
                cwd=self.output_path.parent.parent
            )
            
            # Commit
            commit_msg = config.export.git_commit_message.format(
                date=datetime.utcnow().strftime("%Y-%m-%d")
            )
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                check=True,
                cwd=self.output_path.parent.parent
            )
            
            print(f"Committed: {commit_msg}")
            
            # Push if enabled
            if auto_push or config.export.git_auto_commit:
                subprocess.run(
                    ["git", "push"],
                    check=True,
                    cwd=self.output_path.parent.parent
                )
                print("Pushed to remote")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Git error: {e}")
            return False
        except FileNotFoundError:
            print("Git not found - skipping commit")
            return False
    
    def compare_with_current(self) -> Dict[str, Any]:
        """
        Compare current export with existing file
        Returns diff statistics
        """
        # Get current data from Sheets
        all_places = self.sheets.get_all_places()
        filtered = self._filter_places(all_places)
        new_data = self._convert_to_frontend_format(filtered)
        
        # Load existing file
        if not self.output_path.exists():
            return {
                "current_count": 0,
                "new_count": len(new_data),
                "added": len(new_data),
                "removed": 0,
                "modified": 0,
            }
        
        with open(self.output_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        
        existing_data = existing.get("locations", [])
        
        # Compare
        existing_ids = {p["id"] for p in existing_data}
        new_ids = {p["id"] for p in new_data}
        
        added = len(new_ids - existing_ids)
        removed = len(existing_ids - new_ids)
        common = existing_ids & new_ids
        
        # Check for modifications
        modified = 0
        existing_map = {p["id"]: p for p in existing_data}
        new_map = {p["id"]: p for p in new_data}
        
        for place_id in common:
            if existing_map[place_id] != new_map[place_id]:
                modified += 1
        
        return {
            "current_count": len(existing_data),
            "new_count": len(new_data),
            "added": added,
            "removed": removed,
            "modified": modified,
            "unchanged": len(common) - modified,
        }


# Simple CLI for export
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Export places to JSON")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually write files")
    parser.add_argument("--include-pending", action="store_true", help="Include pending review places")
    parser.add_argument("--min-confidence", type=int, default=50, help="Minimum confidence score")
    parser.add_argument("--git-commit", action="store_true", help="Commit changes to git")
    parser.add_argument("--git-push", action="store_true", help="Push changes to remote")
    parser.add_argument("--compare", action="store_true", help="Compare with existing file")
    
    args = parser.parse_args()
    
    exporter = JSONExporter()
    
    if args.compare:
        diff = exporter.compare_with_current()
        print("\nComparison with existing file:")
        print(f"  Current: {diff['current_count']}")
        print(f"  New: {diff['new_count']}")
        print(f"  Added: {diff['added']}")
        print(f"  Removed: {diff['removed']}")
        print(f"  Modified: {diff['modified']}")
    else:
        result = exporter.export(
            dry_run=args.dry_run,
            only_verified=not args.include_pending,
            min_confidence=args.min_confidence,
        )
        
        if args.git_commit and not args.dry_run:
            exporter.git_commit_and_push(auto_push=args.git_push)
