from dagster import asset, get_dagster_logger
import subprocess
import os
import shutil

@asset
def run_bwa(run_fastqc):
    """Runs BWA alignment pipeline including indexing and read alignment."""
    logger = get_dagster_logger()
    input_dir = "input"
    work_dir = "working_files"
    os.makedirs(work_dir, exist_ok=True)

    reference = os.path.join(input_dir, "ecoli.fa")
    reference_copy = os.path.join(work_dir, "ecoli.fa")
    read1 = os.path.join(input_dir, "SRR2584863_1.fastq")
    read2 = os.path.join(input_dir, "SRR2584863_2.fastq")
    bwa_index_prefix = os.path.join(work_dir, "ecoli")
    sam_output = os.path.join(work_dir, "sample.sam")

    # Copy reference genome
    logger.info(f"Copying reference genome from {reference} to {reference_copy}")
    shutil.copy(reference, reference_copy)

    # Index reference genome
    logger.info("Building BWA index...")
    subprocess.run(
        ["bwa", "index", "-p", bwa_index_prefix, reference_copy],
        check=True
    )

    # Align reads
    logger.info("Running BWA alignment...")
    with open(sam_output, "w") as sam_file:
        subprocess.run(
            ["bwa", "mem", "-t", "4", bwa_index_prefix, read1, read2],
            stdout=sam_file,
            check=True
        )

    logger.info(f"Alignment complete. SAM file created at {sam_output}")

    # Return metadata for Dagster UI
    return {
        "reference": reference_copy,
        "reads": [read1, read2],
        "sam_output": sam_output,
        "index_files": [
            f"{bwa_index_prefix}.{ext}" for ext in ["amb", "ann", "bwt", "pac", "sa"]
        ]
    }
