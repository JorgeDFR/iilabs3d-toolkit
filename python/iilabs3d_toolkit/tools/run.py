import typer
from pathlib import Path
from typing import Sequence
from typing_extensions import Annotated, Optional
from rich.console import Group
from rich.panel import Panel

from iilabs3d_toolkit.tools.console import console
from iilabs3d_toolkit.download.dataset_info import *
from iilabs3d_toolkit.download.download_data import download_files
from iilabs3d_toolkit.tools.convert_bag_ros2 import convert_bags
from iilabs3d_toolkit.tools.eval import compute_metrics
from iilabs3d_toolkit.tools.frame_correction import correct_ref_frame, iilabs3d_ref_frames

app = typer.Typer()

@app.command("list-sequences", 
             help="List all available IILABS 3D Dataset sequences and categories.")
def list_sequences() -> None:
    panel_group = Group(
        Panel("\n".join(["all", "bench", "calib", "calib_imu", "calib_wheel_odom", "calib_extrinsic"]), title="Meta"),
        Panel("\n".join(iilabs3d_bench_seq), title="Benchmark Sequences"),
        Panel("\n".join(iilabs3d_calib_seq_imu_intrinsic), title="IMU Calibration Sequences"),
        Panel("\n".join(iilabs3d_calib_seq_wheel_odom), title="Wheel Odometry Calibration Sequences"),
        Panel("\n".join(iilabs3d_calib_seq_extrinsic), title="Extrinsic Calibration Sequences")
    )
    console.print(panel_group)

def complete_sequence(incomplete: str) -> Sequence[str]:
    sequences = (
        ["all", "bench", "calib", "calib_imu", "calib_wheel_odom", "calib_extrinsic"] 
        + iilabs3d_bench_seq 
        + iilabs3d_calib_seq_imu_intrinsic 
        + iilabs3d_calib_seq_wheel_odom 
        + iilabs3d_calib_seq_extrinsic
    )
    return [seq for seq in sequences if seq.startswith(incomplete)]

@app.command("list-sensors", 
             help="List all available 3D LiDAR sensors in the IILABS 3D Dataset.")
def list_sensors() -> None:
    panel_group = Group(
        Panel("\n".join(iilabs3d_lidar_sensors), title="3D LiDAR Sensors")
    )
    console.print(panel_group)

def complete_sensor(incomplete: str) -> Sequence[str]:
    return [sensor for sensor in iilabs3d_lidar_sensors if sensor.startswith(incomplete)]

@app.command("download",
             help="Download sequences and sensor data. Use 'list-sequences' and 'list-sensors' to view available options.")
def download(
    dataset_dir: Annotated[Path, typer.Argument(
        help="Output directory to save the dataset. Sequences will be stored in sub-folders. Use the same directory for multiple downloads.", 
        show_default=False
    )],
    sequence: Annotated[str, typer.Argument(
        help="Sequence to download from the dataset (see 'list-sequences' for available options)", 
        show_default=False, 
        autocompletion=complete_sequence
    )],
    sensor: Annotated[Optional[str], typer.Argument(
        help="3D LiDAR sensor model to download (see 'list-sensors' for available options)", 
        show_default=False, 
        autocompletion=complete_sensor
    )] = None
) -> None:
    # Handle sequences
    if sequence == "all":
        console.print("Downloading all sequences")
        sequences = iilabs3d_bench_seq + iilabs3d_calib_seq_imu_intrinsic + iilabs3d_calib_seq_wheel_odom + iilabs3d_calib_seq_extrinsic
    elif sequence == "bench":
        console.print("Downloading all benchmark sequences")
        sequences = iilabs3d_bench_seq
    elif sequence == "calib":
        console.print("Downloading all calibration sequences")
        sequences = iilabs3d_calib_seq_imu_intrinsic + iilabs3d_calib_seq_wheel_odom + iilabs3d_calib_seq_extrinsic
    elif sequence == "calib_imu":
        console.print("Downloading all IMU intrinsic calibration sequences")
        sequences = iilabs3d_calib_seq_imu_intrinsic
    elif sequence == "calib_wheel_odom":
        console.print("Downloading all wheel odometry calibration sequences")
        sequences = iilabs3d_calib_seq_wheel_odom
    elif sequence == "calib_extrinsic":
        console.print("Downloading all extrinsic calibration sequences")
        sequences = iilabs3d_calib_seq_extrinsic
    elif sequence in (iilabs3d_bench_seq + iilabs3d_calib_seq_imu_intrinsic + iilabs3d_calib_seq_wheel_odom + iilabs3d_calib_seq_extrinsic):
        sequences = [sequence]
    else:
        console.log(f"[red]Error: '{sequence}' is not a valid sequence.")
        raise typer.Abort()

    # Determine if any sequence requires a sensor
    requires_sensor = any(seq in (iilabs3d_bench_seq + iilabs3d_calib_seq_extrinsic) for seq in sequences)
    
    # Handle sensors
    sensors = []
    if requires_sensor and sensor == None:
        # Prompt user to confirm downloading all sensors
        confirm = typer.confirm("No sensor specified. Download data for all sensors?")
        if not confirm:
            console.log("[red]Aborting download.")
            raise typer.Abort()
        sensor = "all"
    elif sensor == None:
        sensor = "all"

    if sensor == "all":
        sensors = iilabs3d_lidar_sensors
    elif sensor in iilabs3d_lidar_sensors:
        sensors = [sensor]
    else:
        console.log(f"[red]Error: '{sensor}' is not a valid sensor.")
        raise typer.Abort()

    # Create output directory if needed
    dataset_dir.mkdir(parents=True, exist_ok=True)
    
    # Download files
    if requires_sensor:
        console.print(f"Downloading [bold]{len(sequences)}[/] sequence(s) for [bold]{len(sensors)}[/] sensor(s) to '{dataset_dir}'")
    else:
        console.print(f"Downloading [bold]{len(sequences)}[/] sequence(s) to '{dataset_dir}'")
    download_files(sensors, sequences, dataset_dir)

@app.command("convert",
             help="Convert ROS 1 bag file(s) from to ROS 2 format")
def convert(
    input_dir: Annotated[Path, typer.Argument(
        help="Input bag or directory containing multiple bags", 
        show_default=False
    )],
    threads: bool = typer.Option(
        False, "--threads",
        help="Use multiple threads for concurrent conversion of multiple bag files"
    )
) -> None:
    console.print(f"Converting all ROS 1 bag files from '{input_dir}' to ROS 2 bag format") 
    convert_bags(input_dir, use_threads=threads)

@app.command("eval",
             help="Evaluate trajectory accuracy by comparing ground truth and odometry data. Calculates Absolute Trajectory Error (ATE), Relative Translational Error (RTE), and Relative Rotational Error (RRE). Both trajectories must be in the same reference frame (robot frame: base_link). If they are not, use the 'correct-frame' command to transform the odometry data. ")
def eval(
    ground_truth: Annotated[Path, typer.Argument(
        help="Path to the ground truth TUM file.", 
        show_default=False
    )],
    odometry: Annotated[Path, typer.Argument(
        help="Path to the odometry TUM file.", 
        show_default=False
    )],
) -> None:
    compute_metrics(ground_truth, odometry)

def complete_ref_frame(incomplete: str) -> Sequence[str]:
    return [frame for frame in iilabs3d_ref_frames if frame.startswith(incomplete)]

@app.command("correct-frame", 
             help="Correct trajectory reference frame to base_link")
def correct_frame(
    trajectory: Annotated[Path, typer.Argument(
        help="Path to TUM trajectory file", 
        show_default=False
    )],
    ref_frame: Annotated[str, typer.Argument(
        help="Original reference frame", 
        show_default=False, 
        autocompletion=complete_ref_frame
    )],
    sensor: Annotated[Optional[str], typer.Option(
        help="LiDAR sensor name", 
        show_default=False, 
        autocompletion=complete_sensor
    )] = None,
) -> None:
    if ref_frame not in iilabs3d_ref_frames:
        console.log(f"[red]Error: Invalid reference frame '{ref_frame}'")
        raise typer.Abort()
     
    if ref_frame == "lidar":
        if not sensor:
            console.log("[red]Error: Sensor name required for lidar frame correction")
            raise typer.Abort()
        elif sensor not in iilabs3d_lidar_sensors:
            console.log(f"[red]Error: Unknown sensor '{sensor}'")
            raise typer.Abort()

    correct_ref_frame(trajectory, ref_frame, sensor)
  
if __name__ == "__main__":
    app()