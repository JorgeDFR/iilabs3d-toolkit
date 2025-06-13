import json
import time
import requests
from pathlib import Path
from typing import List, Tuple
from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TimeRemainingColumn
from pkg_resources import resource_filename

from iilabs3d_toolkit.download.dataset_info import *
from iilabs3d_toolkit.tools.console import console

DATASET_LINK = "https://open-datasets.inesctec.pt/Aja94l1j"
SENSOR_NAME_MAP = {
    "livox_mid_360": "livox_mid-360",
    "ouster_os1_64": "ouster_os1-64",
    "robosense_rs_helios_5515": "robosense_rs-helios-5515",
    "velodyne_vlp_16": "velodyne_vlp-16"
}

def download_files(sensors: List[str], sequences: List[str], output_dir: Path) -> None:
    """Download multiple sequences with specific folder structure."""
    try:
        json_path = resource_filename('iilabs3d_toolkit.download', 'dataset_files.json')
        with open(json_path, "r") as f:
            dataset_info = json.load(f)
    except Exception as e:
        console.print(f"[red]Failed to load dataset info: {e}")
        return

    output_base = output_dir.resolve() / "iilabs3d_dataset"
    download_list = build_download_list(sensors, sequences, output_base, dataset_info)

    console.rule(f"[bold green]Downloading {len(download_list)} files")
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.percentage:>3.0f}%"),
        DownloadColumn(),
        TimeRemainingColumn(),
        transient=False,
    ) as progress, requests.Session() as session:
        for url, local_path in download_list:
            download_file_with_retry(session, url, local_path, progress)

    console.print(":tada: [bold green]All downloads completed!")

def download_file_with_retry(session: requests.Session, url: str, local_path: Path, progress: Progress,
                             retries: int = 3, delay: int = 2) -> None:
    """Download with retries on failure."""
    for attempt in range(retries):
        try:
            download_file(session, url, local_path, progress)
            return
        except Exception as e:
            console.print(f"[bold red]Attempt {attempt+1} failed for {url}: {e}")
            time.sleep(delay)
    console.print(f"[bold red]All attempts failed for {url}")

def download_file(session: requests.Session, url: str, local_path: Path, progress: Progress) -> None:
    """Download a single file with progress tracking."""
    local_path.parent.mkdir(parents=True, exist_ok=True)
    if local_path.exists():
        return
    with session.get(url, stream=True) as response:
        response.raise_for_status()
        total_length = int(response.headers.get('Content-Length', 0))
        task_id = progress.add_task(f"Downloading {local_path.name}", total=total_length)
        with open(local_path, "wb") as f_out:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f_out.write(chunk)
                    progress.update(task_id, advance=len(chunk))

def build_download_list(sensors: List[str], sequences: List[str], output_base: Path, dataset_info: dict) -> List[Tuple[str, Path]]:
    """Build the list of (url, local_path) tuples for download."""
    download_list = set()
    handled_calibrations = set()

    for sensor_arg in sensors:
        sensor = SENSOR_NAME_MAP.get(sensor_arg)
        for sequence in sequences:
            if sequence in iilabs3d_bench_seq:
                add_benchmark_entries(sensor, sequence, dataset_info, output_base, download_list, handled_calibrations)
            elif sequence in iilabs3d_calib_seq_imu_intrinsic:
                add_imu_intrinsic_entries(sequence, dataset_info, output_base, download_list)
            elif sequence in iilabs3d_calib_seq_wheel_odom:
                add_wheel_odom_entries(sensor, sequence, dataset_info, output_base, download_list)
            elif sequence in iilabs3d_calib_seq_extrinsic:
                add_extrinsic_entries(sensor, sequence, dataset_info, output_base, download_list)

    return download_list

def add_benchmark_entries(sensor: str, sequence: str, dataset_info: dict,
                          output_base: Path, download_list: set, handled_calibrations: set):
    file_name = dataset_info["benchmark"].get(sensor, {}).get(sequence)
    url = f"{DATASET_LINK}/benchmark/{sensor}/{file_name}"
    local_path = output_base / "benchmark" / sensor / sequence / file_name
    download_list.add((url, local_path))

    gt_url = f"{DATASET_LINK}/ground-truth/benchmark/{sensor}/{sequence}/ground_truth.tum"
    gt_path = output_base / "benchmark" / sensor / sequence / "ground_truth.tum"
    download_list.add((gt_url, gt_path))

    if sensor not in handled_calibrations:
        calib_url = f"{DATASET_LINK}/calibration/calib_{sensor}.yaml"
        calib_path = output_base / "benchmark" / sensor / f"calib_{sensor}.yaml"
        download_list.add((calib_url, calib_path))
        handled_calibrations.add(sensor)

def add_imu_intrinsic_entries(sequence: str, dataset_info: dict,
                              output_base: Path, download_list: set):
    file_name = dataset_info["calibration"].get("intrinsic", {}).get("imu", {}).get(sequence)
    url = f"{DATASET_LINK}/calibration/intrinsic/imu/{file_name}"
    local_path = output_base / "calibration" / "intrinsic" / "imu" / file_name
    download_list.add((url, local_path))

def add_wheel_odom_entries(sensor: str, sequence: str, dataset_info: dict,
                           output_base: Path, download_list: set):
    file_name = dataset_info["calibration"].get("intrinsic", {}).get("wheel-odometry", {}).get(sensor, {}).get(sequence)
    url = f"{DATASET_LINK}/calibration/intrinsic/wheel-odometry/{sensor}/{file_name}"
    local_path = output_base / "calibration" / "intrinsic" / "wheel-odometry" / file_name
    download_list.add((url, local_path))

    gt_url = f"{DATASET_LINK}/ground-truth/calibration/intrinsic/wheel-odometry/{sensor}/{sequence}/ground_truth.tum"
    gt_path = output_base / "calibration" / "intrinsic" / "wheel-odometry" / f"gt_{Path(file_name).stem}.tum"
    download_list.add((gt_url, gt_path))

def add_extrinsic_entries(sensor: str, sequence: str, dataset_info: dict,
                          output_base: Path, download_list: set):
    file_name = dataset_info["calibration"].get("extrinsic", {}).get(sensor, {}).get(sequence)
    url = f"{DATASET_LINK}/calibration/extrinsic/{sensor}/{file_name}"
    local_path = output_base / "calibration" / "extrinsic" / sensor / sequence / file_name
    download_list.add((url, local_path))

    if sequence != "calib_full_excite":
        gt_url = f"{DATASET_LINK}/ground-truth/calibration/extrinsic/{sensor}/{sequence}/ground_truth.tum"
        gt_path = output_base / "calibration" / "extrinsic" / sensor / f"gt_{Path(file_name).stem}.tum"
        download_list.add((gt_url, gt_path))