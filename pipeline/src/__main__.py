"""
Main entry point for ingesting new places from sources
Usage: python -m src.ingest_sources [--source SOURCE] [--dry-run]
"""

import asyncio
import argparse
import uuid
from datetime import datetime
from typing import List

from .config import config, SourceConfig
from .models import Place, PlaceStatus, PipelineRun
from .extract_places import PlaceExtractor, DuplicateDetector
from .validate_places import PlaceValidator
from .sheets_client import SheetsClient
from .logging_utils import setup_logging, AuditLogger, PipelineMetrics


async def ingest_sources(
    source_filter: str = None,
    dry_run: bool = False
) -> PipelineRun:
    """
    Main ingestion workflow
    """
    run_id = str(uuid.uuid4())[:8]
    logger = setup_logging(run_id)
    audit = AuditLogger(run_id)
    metrics = PipelineMetrics(run_id)
    
    logger.info(f"Starting ingestion run {run_id}")
    metrics.record_stage_start("ingestion")
    
    # Initialize components
    extractor = PlaceExtractor()
    validator = PlaceValidator()
    sheets = SheetsClient()
    dedup = DuplicateDetector()
    
    # Get existing places for deduplication
    existing_places = sheets.get_all_places()
    logger.info(f"Loaded {len(existing_places)} existing places")
    
    # Get sources to process
    sources = config.get_enabled_sources()
    if source_filter:
        sources = [s for s in sources if source_filter.lower() in s.name.lower()]
    
    logger.info(f"Processing {len(sources)} sources")
    metrics.sources_checked = len(sources)
    
    # Process each source
    for source in sources:
        logger.info(f"Processing source: {source.name} ({source.type})")
        
        try:
            # Extract places
            extracts = await extractor.extract_from_source(source)
            logger.info(f"  Extracted {len(extracts)} potential places")
            
            for extract in extracts:
                metrics.places_extracted += 1
                
                # Check for duplicates
                duplicate_id = dedup.is_duplicate(extract, existing_places)
                
                if duplicate_id:
                    logger.info(f"  Skipping duplicate: {extract.name}")
                    continue
                
                # Validate new place
                logger.info(f"  Validating: {extract.name}")
                place, validation = await validator.validate_new_place(extract)
                
                metrics.places_validated += 1
                
                # Log extraction
                audit.log_extraction(
                    place_id=place.place_id,
                    source_url=str(extract.source_url),
                    extracted_fields={
                        "name": extract.name,
                        "district": extract.district,
                        "address": extract.address,
                    }
                )
                
                # Add to sheets (unless dry run)
                if not dry_run:
                    sheets.add_place(place)
                    metrics.places_added += 1
                    logger.info(f"  ✓ Added: {place.name} (status: {place.status.value})")
                else:
                    logger.info(f"  [DRY RUN] Would add: {place.name}")
                
                # Mark as seen
                dedup.add_seen(extract, place.place_id)
                
        except Exception as e:
            logger.error(f"Error processing source {source.name}: {e}")
            metrics.add_error(str(e), {"source": source.name})
    
    metrics.record_stage_end("ingestion")
    metrics.completed_at = datetime.utcnow()
    metrics.save()
    
    logger.info(f"Ingestion complete. Added {metrics.places_added} new places.")
    
    return PipelineRun(
        run_id=run_id,
        completed_at=datetime.utcnow(),
        stage="completed",
        sources_checked=metrics.sources_checked,
        places_extracted=metrics.places_extracted,
        places_validated=metrics.places_validated,
        places_added=metrics.places_added,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Ingest new places from configured sources"
    )
    parser.add_argument(
        "--source",
        help="Filter to specific source (partial name match)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually write to Sheets"
    )
    
    args = parser.parse_args()
    
    result = asyncio.run(ingest_sources(
        source_filter=args.source,
        dry_run=args.dry_run
    ))
    
    print(f"\n{'='*50}")
    print(f"Run ID: {result.run_id}")
    print(f"Sources checked: {result.sources_checked}")
    print(f"Places extracted: {result.places_extracted}")
    print(f"Places added: {result.places_added}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
