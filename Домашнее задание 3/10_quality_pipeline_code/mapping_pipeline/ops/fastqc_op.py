from dagster import asset, get_dagster_logger
import subprocess
import os
from pathlib import Path

@asset
def run_fastqc():
    """Runs FastQC quality control on input FASTQ files."""
    logger = get_dagster_logger()

    # Define paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    input_dir = base_dir / "input"
    work_dir = base_dir / "working_files" / "qc_reports"

    # Create output directory
    work_dir.mkdir(parents=True, exist_ok=True)

    # Input files
    read1 = input_dir / "SRR2584863_1.fastq"
    read2 = input_dir / "SRR2584863_2.fastq"

    # Initialize result structure
    result = {
        "output_files": [],
        "input_files": [str(read1), str(read2)],
        "status": "",
        "output_directory": str(work_dir),
        "error": ""
    }

    # Check for missing files
    missing = [str(f) for f in [read1, read2] if not f.exists()]
    if missing:
        error_msg = f"Missing input files: {', '.join(missing)}"
        logger.error(error_msg)
        result.update({
            "status": "failed",
            "error": error_msg
        })
        return result

    try:
        # Run FastQC
        subprocess.run(
            ["fastqc", str(read1), str(read2), "-o", str(work_dir)],
            check=True,
            capture_output=True,
            text=True
        )

        # Collect output file paths
        result["output_files"] = [
            str(work_dir / f)
            for f in os.listdir(work_dir)
            if f.endswith(("_fastqc.html", "_fastqc.zip"))
        ]
        result["status"] = "success"

    except subprocess.CalledProcessError as e:
        error_msg = f"FastQC failed: {e.stderr}"
        logger.error(error_msg)
        result.update({
            "status": "failed",
            "error": error_msg
        })

    return result
