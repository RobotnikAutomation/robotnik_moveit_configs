from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import Command, FindExecutable
from launch.substitutions import PathJoinSubstitution
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare
import os
import yaml


def load_yaml(package_path, relative_path):
    full_path = os.path.join(package_path, relative_path)
    with open(full_path, "r") as f:
        return yaml.safe_load(f)


def generate_launch_description():
    moveit_config_pkg = get_package_share_directory("rbkairos_moveit_config")

    srdf_path = os.path.join(moveit_config_pkg, "config", "rbkairos_plus.srdf")
    rviz_config_path = os.path.join(moveit_config_pkg, "config", "moveit.rviz")

    with open(srdf_path, "r") as f:
        robot_description_semantic_content = f.read()

    # Define the path to the xacro file using the package
    xacro_file = PathJoinSubstitution([
        FindPackageShare("robotnik_description"),
        "robots",
        "rbkairos",
        "rbkairos_plus.urdf.xacro"
    ])

    # Create robot description using xacro
    robot_description = {
        "robot_description": ParameterValue(
            Command([
                FindExecutable(name="xacro"),
                " ",
                xacro_file,
                " ",
                "namespace:=robot",
                " ",
                "prefix:=robot_",
                " ",
                "gazebo_ignition:=true",
                " ",
                "ur_type:=ur10e",
            ]),
            value_type=str,
        )
    }

    robot_description_semantic = {
        "robot_description_semantic": ParameterValue(
            Command([
                FindExecutable(name="xacro"), " ", srdf_path, " ",
                "namespace:=robot_", # Make sure this value matches what the SRDF expects
            ]),
            value_type=str,
        )
    }

    robot_description_kinematics = {
        "robot_description_kinematics": load_yaml(moveit_config_pkg, "config/kinematics.yaml")
    }

    joint_limits_yaml = {
        "robot_description_planning": load_yaml(moveit_config_pkg, "config/joint_limits.yaml")
    }

    use_sim_time = {"use_sim_time": True}

    ompl_yaml = {
        "ompl": {
            "planning_plugins": ["ompl_interface/OMPLPlanner"],
            "request_adapters": [
                "default_planning_request_adapters/ResolveConstraintFrames",
                "default_planning_request_adapters/ValidateWorkspaceBounds",
                "default_planning_request_adapters/CheckStartStateBounds",
                "default_planning_request_adapters/CheckStartStateCollision",
            ],
            "response_adapters": [
                "default_planning_response_adapters/AddTimeOptimalParameterization",
            ],
            "start_state_max_bounds_error": 0.1,
            **load_yaml(moveit_config_pkg, "config/ompl_planning.yaml"),
        }
    }

    pilz_industrial_motion_planner_yaml = {
        "pilz_industrial_motion_planner": {
            "default_planner_config": "PTP",
            **load_yaml(moveit_config_pkg, "config/pilz_industrial_motion_planner_planning.yaml"),
        },
        "robot_description_planning": {
            **load_yaml(moveit_config_pkg, "config/pilz_cartesian_limits.yaml"),
        }
    }
    

    planning_pipeline_config = {
        "planning_pipelines": ["pilz_industrial_motion_planner"],#, "chomp", "pilz_industrial_motion_planner", "stomp"],
        "default_planning_pipeline": "pilz_industrial_motion_planner",
    }

    controllers_yaml = load_yaml(moveit_config_pkg, "config/moveit_controllers.yaml")

    trajectory_execution = {
        "moveit_manage_controllers": False,
        "trajectory_execution.allowed_execution_duration_scaling": 1.2,
        "trajectory_execution.allowed_goal_duration_margin": 0.5,
        "trajectory_execution.allowed_start_tolerance": 0.01,
    }

    planning_scene_monitor_parameters = {
        "publish_planning_scene": True,
        "publish_geometry_updates": True,
        "publish_state_updates": True,
        "publish_transforms_updates": True,
        "publish_robot_description": True,
        "publish_robot_description_semantic": True,
    }

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        # namespace="robot",
        output="screen",
        remappings=[("/joint_states", "/robot/joint_states")],
        parameters=[
            use_sim_time,
            robot_description,
            robot_description_semantic,
            robot_description_kinematics,
            joint_limits_yaml,
            # ompl_yaml,
            pilz_industrial_motion_planner_yaml,
            controllers_yaml,
            planning_pipeline_config,
            trajectory_execution,
            planning_scene_monitor_parameters,
        ],
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        # namespace="robot",
        output="screen",
        arguments=["-d", rviz_config_path],
        remappings=[("/joint_states", "/robot/joint_states")],
        parameters=[
            use_sim_time,
            robot_description,
            robot_description_semantic,
            robot_description_kinematics,
            joint_limits_yaml,
            # ompl_yaml,
            pilz_industrial_motion_planner_yaml,
        ],
    )



    return LaunchDescription([
        move_group_node,
        rviz_node,
    ])