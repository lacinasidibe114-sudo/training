from setuptools import find_packages, setup

package_name = 'learn'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sidibe',
    maintainer_email='lacinasidibe114@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [ 
            'simple_publisher = learn.simple_publisher:main',
            'simple_subscriber = learn.simple_subscriber:main',
            'camera = learn.camera:main',
            'camera_qos = learn.camera_qos:main',

            'simple_subscriber_camera = learn.simple_subscriber_camera:main',
            'simple_service_server = learn.simple_service_server:main',
            'simple_service_client = learn.simple_service_client:main',
            "cmd = learn.cmd:main",
            "test = learn.test:main",      
            "test_su = learn.test_su:main",
            "test_con = learn.test_con:main",
            "enregistrer = learn.enregistrer:main", 
            "moteur_brigde = learn.moteur_brigde:main",
            'simple_action_server = learn.simple_action_server:main',
            "simple_lifecycle = learn.simple_lifecycle:main"




            




        ],
    },
)
