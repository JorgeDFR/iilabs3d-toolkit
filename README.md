# IILABS 3D Toolkit

This kit contains utilities to work with the **IILABS 3D Dataset**. It includes functionality to list available dataset sequences, download them, and convert bag files between ROS1 and ROS2 formats.

# Install

To install the **IILABS 3D Toolkit**, run the following command:

```shell
pip install iilabs3d-toolkit
```

You can also install autocompletion for the package by typing:

```shell
iilabs3d --install-completion
```
>**Note**: You need to restart your shell for the autocompletion to take effect.

# Usage

## List Available Sequences

You can list the available sequences in the IILABS 3D dataset by typing:
```shell
iilabs3d list-sequences
```

TODO: "You should see something similar to this:"

## List Available Sensors

The IILABS 3D dataset provides all the sequences for diferent 3D LiDAR sensors , such as the Livox Mid 360, Velodyne VLP-16, etc. You can list the available 3D LiDAR sensors present in the IILABS 3D dataset by typing:
```shell
iilabs3d list-sensors
```

TODO: "You should see something similar to this:"

## Download Sequences

Once you've chosen your sequence and sensor, you can download it with the following command:

iilabs3d download <save_directory> <sequence_name> <sensor_name>

For instance, you could save benchmark sequences fro all sensors as follows:
```shell
iilabs3d download ~/data bench all
```
>**Note**: The sequence will be saved at `<save_directory>/iilabs3d-dataset/<sequence_prefix>/<sequence_name>`. For example:

```shell
data
  - iilabs3d-dataset
    - benchmark
      - livox_mid-360
        - calib_livox_mid-360.yaml
        - elevator
          - *.bag
          - ground_truth.tum
        - loop
          - *.bag
          - ground_truth.tum
        ...
      - ouster_os1-64
        - calib_ouster_os1-64.yaml
        - elevator
          - *.bag
          - ground_truth.tum
        - loop
          - *.bag
          - ground_truth.tum
        ...
      ...
```

## Convert Format

The dataset sequences are provided in ROS1 bag format. We offer a convenient tool to convert them to ROS2 fotmat. To convert a bag or a sequence of bags, type:

```shell
iilabs3d convert <input_directory/input_bag>
```