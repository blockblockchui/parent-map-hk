#!/bin/bash
# Run low cost pipeline daily
# Usage: ./run_lowcost_pipeline.sh

cd "$(dirname "$0")"

LOG_FILE="logs/pipeline_$(date +%Y%m%d_%H%M%S).log"
mkdir -p logs

echo "Starting low cost pipeline at $(date)" | tee "$LOG_FILE"
python3 ingest_lowcost.py 2>&1 | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Pipeline completed successfully" | tee -a "$LOG_FILE"
    
    # Export to JSON
    echo "Exporting to JSON..." | tee -a "$LOG_FILE"
    python3 export_json.py 2>&1 | tee -a "$LOG_FILE"
    
    # Git commit if there are changes
    cd ..
    if git diff --quiet data/locations.json; then
        echo "No changes to commit" | tee -a "$LOG_FILE"
    else
        echo "Committing changes..." | tee -a "$LOG_FILE"
        git add data/locations.json
        git commit -m "Auto update locations from RSS pipeline $(date +%Y-%m-%d)"
        git push
    fi
else
    echo "❌ Pipeline failed" | tee -a "$LOG_FILE"
fi

echo "Finished at $(date)" | tee -a "$LOG_FILE"
