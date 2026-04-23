from huggingface_hub import snapshot_download
import os
from config import HF_TOKEN
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

snapshot_download(
    repo_id="manu/project_gutenberg",
    repo_type="dataset",
    local_dir="/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_parquet",
    allow_patterns=["data/en*"],
    token=HF_TOKEN,
)
