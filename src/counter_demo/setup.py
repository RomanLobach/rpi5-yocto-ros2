from glob import glob

from setuptools import find_packages, setup

package_name = 'counter_demo'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Lobach',
    maintainer_email='r.lobach@inch.health',
    description='Publisher/subscriber counter demo with a start/stop service',
    license='MIT',
    entry_points={
        'console_scripts': [
            'counter_publisher = counter_demo.counter_publisher:main',
            'counter_subscriber = counter_demo.counter_subscriber:main',
        ],
    },
)
