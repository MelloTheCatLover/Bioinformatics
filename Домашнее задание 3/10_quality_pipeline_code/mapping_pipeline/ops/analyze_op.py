from dagster import asset, get_dagster_logger
import os
import subprocess

@asset
def analyze_flagstat(run_samtools):
    """Analyzes flagstat output and calculates mapping quality statistics."""
    logger = get_dagster_logger()
    input_file = "working_files/flagstat.txt"
    output_file = "output/mapping_quality.txt"

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    if not os.path.isfile(input_file):
        raise FileNotFoundError(f"{input_file} not found!")
    if os.stat(input_file).st_size == 0:
        raise ValueError(f"{input_file} is empty!")

    with open(input_file, "r") as f:
        lines = f.readlines()

    total = mapped = None
    for line in lines:
        if "in total" in line:
            total = int(line.split()[0])
        elif "mapped (" in line:
            mapped = int(line.split()[0])

    if total is None or mapped is None:
        raise ValueError("Could not extract read counts from flagstat.txt")
    if total == 0:
        raise ZeroDivisionError("Total reads is 0 - division by zero")

    percent = round((mapped / total) * 100, 2)
    status = "OK" if percent > 90 else "NOT OK"

    with open(output_file, "w") as f:
        f.write(f"Mapped reads: {mapped} / {total} ({percent}%)\n")
        f.write(f"Mapping quality: {status}\n")

    logger.info(f"[Mapping Quality] {mapped}/{total} ({percent}%) -> {status}")
    
    # Return metadata that will be visible in Dagster UI
    return {
        "total_reads": total,
        "mapped_reads": mapped,
        "mapping_percentage": percent,
        "status": status,
        "output_path": output_file
    }
