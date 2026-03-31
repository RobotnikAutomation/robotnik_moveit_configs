import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.conditions import IfCondition
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():

    # Command-line arguments
    db_arg = DeclareLaunchArgument(
        "db", default_value="False", description="Database flag"
    )

    moveit_config = (
        MoveItConfigsBuilder("rbkairos_plus", package_name="rbkairos_moveit_config")
        .robot_description(
            file_path="config/rbkairos_plus.urdf.xacro",
        )
        .robot_description_semantic(file_path="config/rbkairos_plus.srdf")
        .planning_scene_monitor(
            publish_robot_description=True, publish_robot_description_semantic=True
        )
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .planning_pipelines(
            pipelines=["pilz_industrial_motion_planner"],
        )
        .to_moveit_configs()
    )

    # Start the actual move_group node/action server
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_config.to_dict()],
        # remappings=[
        #         ('/joint_states', '/robot/joint_states'),
        #     ],
        arguments=["--ros-args", "--log-level", "info"],
    )

    # RViz
    rviz_config_arg = DeclareLaunchArgument(
    "rviz_config",
    default_value=PathJoinSubstitution([
        FindPackageShare("rbkairos_moveit_config"), "config", "moveit.rviz"
    ]),
    description="RViz configuration file (found inside rbkairos_moveit_config/config/ by default)",
    )

    # rviz_config_arg = DeclareLaunchArgument(
    #     "rviz_config",
    #     default_value="moveit.rviz",
    #     description=""
    # )
    # rviz_base = LaunchConfiguration("rviz_config", description="Path to RViz2 config file")
    # rviz_config = PathJoinSubstitution(
    #     [FindPackageShare("rbkairos_moveit_config"), "launch", rviz_base]
    # )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        # arguments=["-d", rviz_config],
        arguments=["-d", LaunchConfiguration("rviz_config")],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.planning_pipelines,
            moveit_config.robot_description_kinematics,
            moveit_config.joint_limits,
        ],
    )

    # Warehouse mongodb server
    # db_config = LaunchConfiguration("db")
    # mongodb_server_node = Node(
    #     package="warehouse_ros_mongo",
    #     executable="mongo_wrapper_ros.py",
    #     parameters=[
    #         {"warehouse_port": 33829},
    #         {"warehouse_host": "localhost"},
    #         {"warehouse_plugin": "warehouse_ros_mongo::MongoDatabaseConnection"},
    #     ],
    #     output="screen",
    #     condition=IfCondition(db_config),
    # )

    return LaunchDescription(
        [
            rviz_config_arg,
            db_arg,
            rviz_node,
            move_group_node,
            # mongodb_server_node,
        ]
    )