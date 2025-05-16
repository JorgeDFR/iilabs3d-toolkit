<div align="center">
    <h1>IILABS 3D Toolkit</h1>
    <h3>
        <a href="https://jorgedfr.github.io/3d_lidar_slam_benchmark_at_iilab/">Project Site</a> 
        |
        <a href="https://rdm.inesctec.pt/dataset/nis-2025-001">Dataset Page</a>
        <!-- | 
        <a href="TODO">Preprint</a> -->
    </h3>
    <a href=""><img src=https://github.com/JorgeDFR/iilabs3d-toolkit/actions/workflows/python.yml/badge.svg /></a>
    <a href="https://pypi.org/project/iilabs3d-toolkit/"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/iilabs3d-toolkit"/></a>
    <a href=""><img alt="PyPI - Downloads" src="https://img.shields.io/pypi/dm/iilabs3d-toolkit"/></a>
    <br />
    <br />
    <a href="https://github.com/JorgeDFR/iilabs3d-toolkit"><img src="https://raw.githubusercontent.com/JorgeDFR/iilabs3d-toolkit/refs/heads/main/docs/figs/iilabs3d_image.png"/></a>
</div>

This toolkit provides a set of utilities to work with the [IILABS 3D Dataset](https://rdm.inesctec.pt/dataset/nis-2025-001). It enables you to list available dataset sequences and sensors, download sequences along with sensor data, convert ROS 1 bag files to ROS 2 format, evaluate trajectories using accuracy metrics, and correct trajectory reference frames.

**With this version, it is possible to do:**

- **List Sequences and Sensors:** Easily view all available dataset sequences (benchmark, calibration, etc.) and 3D LiDAR sensors.
- **Download Data:** Download sequences and sensor data with a single command.
- **Bag File Conversion:** Convert ROS 1 bag files to ROS 2 format using the [rosbags](https://gitlab.com/ternaris/rosbags) Python library.
- **Trajectory Evaluation:** Calculate accuracy metrics between ground truth and odometry trajectories using the [evo](https://github.com/MichaelGrupp/evo) Python library.
- **Reference Frame Correction:** Adjust trajectory reference frames to the reference frame of the ground-truth data (`base_link`).

## Installation

To install the **IILABS 3D Toolkit**, run the following command:

```shell
pip install iilabs3d-toolkit
```

You can also install autocompletion for the package by typing:

```shell
iilabs3d --install-completion
```
>**Note**: You need to restart your shell for the autocompletion to take effect.

## Usage

To see all the available commands type:

```shell
iilabs3d --help
```

![iilabs3d_help_cli](https://raw.githubusercontent.com/JorgeDFR/iilabs3d-toolkit/refs/heads/main/docs/figs/iilabs3d_help_cli.png)

### Listing Commands
#### List Available Sequences

You can list the available sequences in the IILABS 3D dataset by typing:

```shell
iilabs3d list-sequences
```

![iilabs3d_list-sequences_cli](https://raw.githubusercontent.com/JorgeDFR/iilabs3d-toolkit/refs/heads/main/docs/figs/iilabs3d_list-sequences_cli.png)

#### List Available Sensors

The IILABS 3D dataset provides all the sequences for different 3D LiDAR sensors, such as the Livox Mid 360, Velodyne VLP-16, etc. You can list the available 3D LiDAR sensors present in the IILABS 3D dataset by typing:

```shell
iilabs3d list-sensors
```

![iilabs3d_list-sensors_cli](https://raw.githubusercontent.com/JorgeDFR/iilabs3d-toolkit/refs/heads/main/docs/figs/iilabs3d_list-sensors_cli.png)

### Data Download

Once you've chosen your sequence and sensor, you can download it with the following command:

```shell
iilabs3d download <output_directory> <sequence_name> <sensor_name>
```

For instance, you could download all benchmark sequences for all sensors as follows:

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

![iilabs3d_download_cli](https://raw.githubusercontent.com/JorgeDFR/iilabs3d-toolkit/refs/heads/main/docs/figs/iilabs3d_download_cli.png)

### Bag File Conversion

The dataset sequences are provided in ROS 1 bag format. We offer a convenient tool to convert them to ROS 2 format, making use of the [rosbags](https://gitlab.com/ternaris/rosbags) open-source Python library to perform the conversion. To convert a bag or a sequence of bags, type:

```shell
iilabs3d convert <input_bag_or_directory> [--threads]
```
>**Note**: We provide a option `--threads` to allow concurrent conversion of multiple bag files.

![iilabs3d_convert_cli](https://raw.githubusercontent.com/JorgeDFR/iilabs3d-toolkit/refs/heads/main/docs/figs/iilabs3d_convert_cli.png)

### Trajectory Evaluation

After downloading the desired sequence and retrieving the odometry trajectory using a SLAM algorithm, you can calculate the accuracy metrics using both the ground-truth and the odometry trajectories in TUM file format. In this toolkit we use the [evo](https://github.com/MichaelGrupp/evo) open-source Python library for metric computation. Therefore, to calculate the metrics you can type:

```shell
iilabs3d eval <ground_truth.tum> <odometry.tum>
```

![iilabs3d_eval_cli](https://raw.githubusercontent.com/JorgeDFR/iilabs3d-toolkit/refs/heads/main/docs/figs/iilabs3d_eval_cli.png)

If you don't have the odometry trajectory in a tum file format, you can use the evo script to make a conversion from different formats. for example, if your odometry trajectory is provided as a ROS 1 bag file, you can run:

```shell
evo_traj bag <bag_file_name> <topic_name> --save_as_tum
```

To check all the available supported formats, please refer to the official evo documentation.

### Reference Frame Correction

Since the ground-truth data is provided in the robot `base_link` frame it is important to have the odometry trajectory data in the same reference frame when calculating the accuracy metrics. As such, we provide a command to make the required correction using the transformations retrieved from the CAD models of the robot. The supported reference frames are `base_footprint`, `imu`, and `lidar`, where the last one requires the specification of the 3D LiDAR sensor to be considered (e.g. `livox_mid_360`). To perform this correction type:

```shell
iilabs3d correct-frame <trajectory.tum> <ref_frame> [--sensor <sensor_name>]
```

![iilabs3d_correct-frame_cli](https://raw.githubusercontent.com/JorgeDFR/iilabs3d-toolkit/refs/heads/main/docs/figs/iilabs3d_correct-frame_cli.png)

## License

Distributed under the _BSD 3-Clause License_.
See [LICENSE](/LICENSE) for more information.

## References

If you use _iilabs3d-toolkit_ in a work that leads to a scientific publication, we would appreciate it if you would kindly cite the IILABS 3D dataset in your manuscript:

J.D. Ribeiro, R.B. Sousa, J.G. Martins, A.S. Aguiar, F.N. Santos and H.M. Sobreira, "IILABS 3D: iilab Indoor LiDAR-based SLAM Dataset" [Dataset], INESC TEC, 2025, DOI: [10.25747/VHNJ-WM80](https://doi.org/10.25747/VHNJ-WM80).

## Contacts

If you have any questions or you want to know more about this work, please contact one of the contributors of this package:

- Jorge Diogo Ribeiro ([github](https://github.com/JorgeDFR/),
  [gitlab](https://gitlab.inesctec.pt/jorge.d.ribeiro),
  [mail](mailto:jorge.d.ribeiro@inesctec.pt))
- Ricardo B. Sousa ([github](https://github.com/sousarbarb/),
  [gitlab](https://gitlab.inesctec.pt/ricardo.b.sousa),
  [mail](mailto:ricardo.b.sousa@inesctec.pt))
- Héber Miguel Sobreira ([github](https://github.com/HeberSobreira),
  [gitlab](https://gitlab.inesctec.pt/heber.m.sobreira),
  [mail](mailto:heber.m.sobreira@inesctec.pt))

## Acknowledgements

- [CRIIS - Centre for Robotics in Industry and Intelligent Systems](https://www.inesctec.pt/en/centres/criis/) from
  [INESC TEC - Institute for Systems and Computer Engineering, Technology and Science](https://www.inesctec.pt/en/)
- [Faculty of Engineering, University of Porto (FEUP)](https://sigarra.up.pt/feup/en/)

## Funding

This work is co-financed by Component 5 - Capitalisation and Business
Innovation, integrated in the Resilience Dimension of the Recovery and
Resilience Plan within the scope of the Recovery and Resilience Mechanism (MRR)
of the [European Union (EU)](https://european-union.europa.eu/index_en), framed
in the [Next Generation EU](https://next-generation-eu.europa.eu/index_en), for
the period 2021-2026, within project
[GreenAuto](https://preprod.transparencia.gov.pt/pt/fundos-europeus/prr/beneficiarios-projetos/projeto/02/C05-i01.02/2022.PC644867037-00000013/),
with reference 54.