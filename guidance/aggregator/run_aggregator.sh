#!/bin/bash
# PI Case Aggregator - Run Script
# Usage: ./run_aggregator.sh [case_folder] [output_format]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
CASE_FOLDER="${1:-$PARENT_DIR/sample_files/pi_case_001/output}"
OUTPUT_FORMAT="${2:-markdown}"
OUTPUT_DIR="$PARENT_DIR/sample_files/pi_case_001/reports"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Set output filename based on format
case $OUTPUT_FORMAT in
    json)
        OUTPUT_FILE="$OUTPUT_DIR/case_summary.json"
        ;;
    markdown)
        OUTPUT_FILE="$OUTPUT_DIR/case_summary.md"
        ;;
    html)
        OUTPUT_FILE="$OUTPUT_DIR/case_summary.html"
        ;;
    *)
        echo "Unknown format: $OUTPUT_FORMAT"
        echo "Usage: $0 [case_folder] [json|markdown|html]"
        exit 1
        ;;
esac

echo "============================================"
echo "NY Personal Injury Case Aggregator"
echo "============================================"
echo "Case Folder: $CASE_FOLDER"
echo "Output Format: $OUTPUT_FORMAT"
echo "Output File: $OUTPUT_FILE"
echo "============================================"

# Run the aggregator
python3 "$SCRIPT_DIR/pi_case_aggregator.py" \
    "$CASE_FOLDER" \
    --format "$OUTPUT_FORMAT" \
    --output "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "SUCCESS: Case summary generated!"
    echo "View report: $OUTPUT_FILE"

    # Also generate JSON for data export
    if [ "$OUTPUT_FORMAT" != "json" ]; then
        python3 "$SCRIPT_DIR/pi_case_aggregator.py" \
            "$CASE_FOLDER" \
            --format json \
            --output "$OUTPUT_DIR/case_summary.json"
        echo "JSON export: $OUTPUT_DIR/case_summary.json"
    fi
else
    echo "ERROR: Failed to generate case summary"
    exit 1
fi
