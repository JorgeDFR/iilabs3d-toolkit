import typer
import os
import numpy as np
from pathlib import Path
from evo.tools import file_interface
from evo.core import lie_algebra as lie
from typing import Optional

from iilabs3d_toolkit.tools.console import console

iilabs3d_ref_frames = ["base_footprint", "lidar", "imu"]

# Transformation definitions (meters)
LIDAR_TO_BASE_LINK = {
    "livox_mid_360": lie.sim3(np.eye(3), np.array([0.0, 0.0, 0.4612]), 1.0),
    "ouster_os1_64": lie.sim3(np.eye(3), np.array([0.0, 0.0, 0.4367]), 1.0),
    "robosense_rs_helios_5515": lie.sim3(np.eye(3), np.array([0.0, 0.0, 0.4777]), 1.0),
    "velodyne_vlp_16": lie.sim3(np.eye(3), np.array([0.0, 0.0, 0.4519]), 1.0),
}
IMU_TO_BASE_LINK = lie.sim3(np.eye(3), np.array([0.0, 0.0, 0.19996]), 1.0)
BASE_FOOTPRINT_TO_BASE_LINK = lie.sim3(np.eye(3), np.array([0.0, 0.0, -0.0508]), 1.0)

def correct_ref_frame(tum_file: Path, ref_frame: str, sensor: Optional[str] = None) -> None:
    """Correct trajectory frame to base_link"""
    # Load trajectory
    traj = file_interface.read_tum_trajectory_file(str(tum_file))
    
    # Get transformation based on reference frame
    if ref_frame == "lidar":
        T_left = LIDAR_TO_BASE_LINK[sensor]
    elif ref_frame == "imu":
        T_left = IMU_TO_BASE_LINK
    else:  # base_footprint
        T_left = BASE_FOOTPRINT_TO_BASE_LINK

    # Apply transformations
    traj.transform(T_left)
    T_right = lie.se3_inverse(T_left)
    traj.transform(T_right, right_mul=True)

    # Create backup
    backup_path = tum_file.parent / f"{tum_file.stem}.orig{tum_file.suffix}"
    if backup_path.exists():
        console.log(f"[yellow]Backup file already exists at {backup_path}")
        if not typer.confirm("Overwrite existing backup?"):
            console.log("[red]Aborting frame correction")
            return

    os.rename(tum_file, backup_path)
    
    # Save corrected trajectory
    file_interface.write_tum_trajectory_file(tum_file, traj)
    console.log(f"[green]Success! Corrected trajectory saved to {tum_file}")
    console.log(f"[dim]Original file backed up at {backup_path}")