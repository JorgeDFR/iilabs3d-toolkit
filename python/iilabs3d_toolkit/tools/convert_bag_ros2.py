import os
import yaml
from pathlib import Path
from rosbags import convert
from rich.live import Live
from rich.console import Group
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
from concurrent.futures import ThreadPoolExecutor, as_completed

from iilabs3d_toolkit.tools.console import console

TYPE_MAPPINGS = {
    "sdpo_drivers_interfaces/msg/MotRefArrayROS1": "sdpo_drivers_interfaces/msg/MotRefArray",
    "sdpo_drivers_interfaces/msg/MotEncArrayROS1": "sdpo_drivers_interfaces/msg/MotEncArray",
}

# Latch configuration for /tf_static
LATCH = """
- history: 3
  depth: 0
  reliability: 1
  durability: 1
  deadline:
    sec: 2147483647
    nsec: 4294967295
  lifespan:
    sec: 2147483647
    nsec: 4294967295
  liveliness: 1
  liveliness_lease_duration:
    sec: 2147483647
    nsec: 4294967295
  avoid_ros_namespace_conventions: false
""".strip()

def update_metadata(metadata_path: Path):
    """Update the message types and QoS settings in the metadata.yaml file after verifying expected keys exist."""
    if metadata_path.is_file():
        with open(metadata_path, 'r') as file:
            metadata = yaml.safe_load(file)
        
        # Verify the expected keys are in the metadata.
        if ("rosbag2_bagfile_information" in metadata and 
            "topics_with_message_count" in metadata["rosbag2_bagfile_information"]):
            
            topics = metadata["rosbag2_bagfile_information"]["topics_with_message_count"]
            for topic in topics:
                if "topic_metadata" in topic:
                    topic_metadata = topic["topic_metadata"]
                    
                    # Update message type if a mapping exists.
                    if "type" in topic_metadata:
                        topic_type = topic_metadata["type"]
                        if topic_type in TYPE_MAPPINGS:
                            topic_metadata["type"] = TYPE_MAPPINGS[topic_type]
                    
                    # Update offered QoS for /tf_static if the topic exists.
                    if "name" in topic_metadata and topic_metadata["name"] == "/tf_static":
                        topic_metadata["offered_qos_profiles"] = LATCH
        else:
            console.log(f"Metadata file '{metadata_path}' does not contain expected keys. No updates applied.")
        
        # Write the updated metadata back to the file.
        with open(metadata_path, 'w') as file:
            yaml.dump(metadata, file, default_flow_style=False)

def get_bag_file_paths(input_folder: Path):
    """
    Walk through the input folder and return a list of tuples:
    (input_bag_path, corresponding_output_bag_path)
    """
    bag_paths = []
    for root, _, files in os.walk(input_folder):
        for file in files:
            if file.endswith(".bag"):
                input_bagpath = Path(root) / file
                output_bagpath = input_bagpath.parent / (input_bagpath.stem + "_ros2")
                bag_paths.append((input_bagpath, output_bagpath))
    return bag_paths

def process_bag_file(args):
    """
    Process a single ROS 1 bag file:
      - Create the output directory.
      - Convert the bag file to ROS 2.
      - Update the metadata if needed.
    """
    bagpath, new_bagpath = args
    new_bagpath.parent.mkdir(parents=True, exist_ok=True)
    try:
        convert.convert(bagpath, new_bagpath)
        metadata_path = new_bagpath / "metadata.yaml"
        update_metadata(metadata_path)
    except Exception as e:
        console.log(f"Error processing {bagpath}: {e}")
        return None
    return new_bagpath

def convert_bags(input_dir: Path, use_threads: bool = False) -> None:
    """Convert ROS 1 bag files to ROS 2 format with detailed progress tracking."""
    
    # Gather bag files to convert
    if input_dir.is_dir():
        bag_files = get_bag_file_paths(input_dir)
    else:
        bag_files = [(input_dir, input_dir.parent / (input_dir.stem + "_ros2"))]

    # Filter out already existing ROS 2 bag files
    existing_files = [dst for _, dst in bag_files if dst.exists()]
    num_existing = len(existing_files)

    if num_existing > 0:
        console.print(f"[bold yellow]{num_existing} bag file(s) already converted. Skipping them.")
        bag_files = [(src, dst) for src, dst in bag_files if not dst.exists()]

    if not bag_files:
        console.log("[bold red]No bag files found.")
        return

    total_files = len(bag_files)
    console.rule(f"[bold green]Found {total_files} bag file(s) for conversion.")

    overall_progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        transient=False
    )
    active_progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    )
    group = Group(overall_progress, active_progress)
    live = Live(group) 

    with live:
        overall_task = overall_progress.add_task("Overall Progress", total=total_files)

        if use_threads:
            num_workers = os.cpu_count() or 4
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = {}
                for bag in bag_files:
                    bagpath, new_bagpath = bag
                    task_id = active_progress.add_task(f"Converting {bagpath.name}", total=None)
                    future = executor.submit(process_bag_file, bag)

                    def create_callback(tid):
                        def _callback(_):
                            active_progress.remove_task(tid)
                            overall_progress.update(overall_task, advance=1)
                        return _callback
                    
                    future.add_done_callback(create_callback(task_id))
                    futures[future] = bag

                for future in as_completed(futures):
                    future.result()

        else:
            for bag in bag_files:
                bagpath, _ = bag
                task_id = active_progress.add_task(f"Converting {bagpath.name}", total=None)

                process_bag_file(bag)

                active_progress.remove_task(task_id)
                overall_progress.update(overall_task, advance=1)
    
    
    console.print(":tada: [bold green]All conversions completed!")