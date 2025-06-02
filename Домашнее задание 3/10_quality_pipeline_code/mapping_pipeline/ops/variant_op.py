from dagster import asset, get_dagster_logger
import subprocess
import os

@asset
def run_freebayes(run_samtools) -> dict:
    """Runs FreeBayes variant calling on sorted BAM files."""
    logger = get_dagster_logger()

    reference = "working_files/ecoli.fa"
    sorted_bam = "output/sample.sorted.bam"
    vcf_out = "output/sample.vcf"

    if not os.path.exists(reference):
        raise FileNotFoundError(f"Reference genome not found at {reference}")
    if not os.path.exists(sorted_bam):
        raise FileNotFoundError(f"Input BAM file not found at {sorted_bam}")

    os.makedirs(os.path.dirname(vcf_out), exist_ok=True)

    logger.info(f"Running FreeBayes with:")
    logger.info(f"  Reference: {reference}")
    logger.info(f"  BAM: {sorted_bam}")
    logger.info(f"  Output: {vcf_out}")

    try:
        with open(vcf_out, "w") as vcf_file:
            subprocess.run(
                ["freebayes", "-f", reference, sorted_bam],
                stdout=vcf_file,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )

        if os.path.exists(vcf_out) and os.path.getsize(vcf_out) > 0:
            with open(vcf_out, "r") as f:
                variant_count = sum(1 for line in f if not line.startswith("#"))

            return {
                "vcf_output": vcf_out,
                "reference": reference,
                "input_bam": sorted_bam,
                "status": "success",
                "message": "Variant calling completed successfully",
                "metrics": {
                    "variant_count": variant_count,
                    "file_size": f"{os.path.getsize(vcf_out)/1024:.2f} KB"
                }
            }
        else:
            return {
                "vcf_output": vcf_out,
                "reference": reference,
                "input_bam": sorted_bam,
                "status": "failed",
                "message": "VCF file was not generated properly",
                "metrics": {}
            }

    except subprocess.CalledProcessError as e:
        logger.error(f"FreeBayes failed: {e.stderr}")
        return {
            "status": "failed",
            "error": e.stderr.strip(),
            "command": " ".join(e.cmd),
            "returncode": e.returncode
        }

