

from .fastqc_op import run_fastqc
from .align_op import run_bwa
from .samtools_op import run_samtools
from .analyze_op import analyze_flagstat
from .variant_op import run_freebayes
from .cleanup_op import clean_working_directory

from dagster import Definitions, define_asset_job, AssetSelection

defs = Definitions(
    assets=[
        run_fastqc,
        run_bwa, 
        run_samtools,
        analyze_flagstat,
        run_freebayes,
        clean_working_directory,
    ],
    jobs=[
        # Main pipeline job
        define_asset_job(
            "bio_pipeline",
            selection=AssetSelection.all() - AssetSelection.keys("clean_working_directory")
        ),
        
        # Optional cleanup job (run separately)
        define_asset_job(
            "cleanup_job",
            selection=AssetSelection.keys("clean_working_directory")
        )
    ]
)


__all__ = [
    'run_fastqc',
    'run_bwa',
    'run_samtools',
    'analyze_flagstat',
    'run_freebayes',
    'clean_working_directory'
]
