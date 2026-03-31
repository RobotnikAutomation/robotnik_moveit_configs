from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription,GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, EnvironmentVariable, PythonExpression
from launch_ros.actions import PushRosNamespace
from launch.conditions import IfCondition
import os

from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    declared_args = [
        DeclareLaunchArgument('robot_id', default_value=EnvironmentVariable('ROBOT_ID', default_value='robot')),
    ]

    moveit = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('rbkairos_moveit_config'), 'launch/', 'robotnik_moveit.launch.py')
        ),
        launch_arguments={
            'namespace': LaunchConfiguration('robot_id'),
        }.items(),
    )

    group = GroupAction([
        PushRosNamespace(LaunchConfiguration('robot_id')),
        moveit,
    ])

    return LaunchDescription(declared_args + [group])