import sys
from pathlib import Path
from dagster import Definitions, load_assets_from_modules, AssetSelection, define_asset_job

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Now import using absolute path
from mapping_pipeline.ops import (
    run_fastqc,
    run_bwa,
    run_samtools,
    analyze_flagstat,
    run_freebayes,
    clean_working_directory,
)

# Import ops module for load_assets_from_modules
from mapping_pipeline import ops

all_assets = load_assets_from_modules([ops])

defs = Definitions(
    assets=all_assets,
    jobs=[
        define_asset_job(
            "bio_pipeline",
            selection=AssetSelection.all() - AssetSelection.keys("clean_working_directory")
        ),
        define_asset_job(
            "cleanup_job", 
            selection=AssetSelection.keys("clean_working_directory")
        )
    ]
)
