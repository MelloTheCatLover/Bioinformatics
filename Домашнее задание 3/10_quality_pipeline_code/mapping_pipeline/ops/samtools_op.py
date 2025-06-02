from dagster import asset, get_dagster_logger
import subprocess
import os
from typing import Dict, List

@asset
def run_samtools(run_bwa) -> Dict[str, str]:
    """Processes SAM files through samtools pipeline including:
    - SAM to BAM conversion
    - Flagstat generation
    - BAM sorting
    - BAM indexing
    
    Returns:
        Dictionary containing metadata about the generated files including:
        - intermediate_bam: Path to unsorted BAM
        - sorted_bam: Path to sorted BAM
        - bam_index: Path to BAM index
        - flagstat: Path to flagstat file
        - status: Processing status
    """
    logger = get_dagster_logger()
    work_dir = "working_files"
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # Define file paths
    bam_output = os.path.join(work_dir, "sample.bam")
    sam_input = os.path.join(work_dir, "sample.sam")
    sorted_bam = os.path.join(output_dir, "sample.sorted.bam")
    flagstat_txt = os.path.join(work_dir, "flagstat.txt")
    bam_index = f"{sorted_bam}.bai"

    # Validate input
    if not os.path.exists(sam_input):
        raise FileNotFoundError(f"Input SAM file not found at {sam_input}")

    try:
        # 1. Convert SAM to BAM
        logger.info(f"Converting SAM to BAM: {sam_input} → {bam_output}")
        with open(bam_output, "wb") as bam_file:
            subprocess.run(
                ["samtools", "view", "-@4", "-Sb", sam_input],
                stdout=bam_file,
                check=True
            )

        # 2. Generate flagstat
        logger.info(f"Generating flagstat: {bam_output} → {flagstat_txt}")
        with open(flagstat_txt, "w") as flagstat_file:
            subprocess.run(
                ["samtools", "flagstat", bam_output],
                stdout=flagstat_file,
                check=True
            )

        # 3. Sort BAM
        logger.info(f"Sorting BAM: {bam_output} → {sorted_bam}")
        subprocess.run(
            ["samtools", "sort", "-@4", "-o", sorted_bam, bam_output],
            check=True
        )

        # 4. Index sorted BAM
        logger.info(f"Indexing sorted BAM: {sorted_bam}")
        subprocess.run(
            ["samtools", "index", sorted_bam],
            check=True
        )

        return {
            "intermediate_bam": bam_output,
            "sorted_bam": sorted_bam,
            "bam_index": bam_index,
            "flagstat": flagstat_txt,
            "status": "success",
            "message": "SAM processing completed successfully"
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Samtools processing failed at step: {e.cmd}")
        return {
            "status": "failed",
            "error": str(e),
            "failed_command": e.cmd,
            "returncode": e.returncode
        }
