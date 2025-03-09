import copy
from pathlib import Path
from evo.core import sync, metrics
from evo.tools import file_interface

from rich.table import Table
from rich.panel import Panel

from iilabs3d_toolkit.tools.console import console

MAX_TIME_SYNC_DIFF = 0.01
DELTA = 10
DELTA_UNIT = metrics.Unit.meters

def compute_metrics(gt_tum_path: Path, odom_tum_path: Path):
    gt_traj = file_interface.read_tum_trajectory_file(str(gt_tum_path))
    odom_traj = file_interface.read_tum_trajectory_file(str(odom_tum_path))

    traj_ref, traj_est = sync.associate_trajectories(gt_traj, odom_traj, MAX_TIME_SYNC_DIFF)
    traj_est_aligned = copy.deepcopy(traj_est)
    traj_est_aligned.align(traj_ref, correct_scale=False, correct_only_scale=False)

    # ATE
    ate_metric = metrics.APE(metrics.PoseRelation.translation_part)
    ate_metric.process_data((traj_ref, traj_est_aligned))
    ate_stat = ate_metric.get_statistic(metrics.StatisticsType.rmse)

    # RTE
    rte_metric = metrics.RPE(metrics.PoseRelation.translation_part, DELTA, DELTA_UNIT, all_pairs=True)
    rte_metric.process_data((traj_ref, traj_est))
    rte_stat = (rte_metric.get_statistic(metrics.StatisticsType.mean) / DELTA) * 100  # %

    # RRE
    rre_metric = metrics.RPE(metrics.PoseRelation.rotation_angle_deg, DELTA, metrics.Unit.meters, all_pairs=True)
    rre_metric.process_data((traj_ref, traj_est))
    rre_stat = rre_metric.get_statistic(metrics.StatisticsType.mean) / DELTA  # deg/m

    # Create adaptive table
    results_table = Table(
        box=None,
        show_header=False,
        expand=True,
        pad_edge=False,
        row_styles=["none"],
    )
    
    # Configure adaptive columns
    results_table.add_column(style="bold cyan", min_width=20)
    results_table.add_column(style="bold green", justify="right", min_width=12)
    results_table.add_column(style="italic bright_black", min_width=30)

    # Add rows
    results_table.add_row(
        "Absolute Trajectory Error (ATE)", 
        f"{ate_stat:.3f} m", 
        "RMSE of absolute position errors"
    )
    results_table.add_row(
        "Relative Translation Error (RTE)", 
        f"{rte_stat:.2f}%", 
        f"Mean over {DELTA}m intervals"
    )
    results_table.add_row(
        "Relative Rotation Error (RRE)", 
        f"{rre_stat:.3f} °/m", 
        f"Mean over {DELTA}m intervals"
    )

    # Create panel with parameter info
    panel = Panel(
        results_table,
        title="[bold]SLAM Evaluation Metrics[/]",
        subtitle=f"[dim]Δ = {DELTA}m | Time sync tolerance = {MAX_TIME_SYNC_DIFF}s",
        border_style="bright_white",
        expand=False
    )
    
    console.print(panel)