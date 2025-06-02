from dagster import asset, get_dagster_logger
import shutil
import os

@asset
def clean_working_directory(run_fastqc, run_bwa, run_samtools, analyze_flagstat, run_freebayes):
    """Cleans up the working directory by removing temporary files."""
    logger = get_dagster_logger()
    work_dir = "working_files"
    
    logger.info(f"Attempting to clean up working directory: {work_dir}")
    
    if os.path.exists(work_dir):
        try:
            shutil.rmtree(work_dir, ignore_errors=True)
            logger.info(f"Successfully cleaned up {work_dir}")
            return {
                "status": "success",
                "directory": work_dir,
                "message": f"Directory {work_dir} was successfully removed"
            }
        except Exception as e:
            logger.error(f"Failed to clean up {work_dir}: {str(e)}")
            return {
                "status": "error",
                "directory": work_dir,
                "error": str(e)
            }
    else:
        logger.warning(f"Directory {work_dir} does not exist - nothing to clean")
        return {
            "status": "skipped",
            "directory": work_dir,
            "message": "Directory did not exist"
        }
