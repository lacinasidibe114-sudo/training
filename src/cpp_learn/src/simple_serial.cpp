#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msgs/String.hpp>
#include <libserial/SerialPort.h>

class Transmitter : public rclcpp::Node 
{

    public :

    Transmitter() : Node("transmitter"){

        declare_parameter ("port", "/dev/ttyUSB0");
        port = get_paramter("port").as_string();
        sub = create-subcription<std_msgs::msg::String>("transmitter" , 10 , std::bind(&Transmitter::callback, this, std::placeholders::_1));

        arduino.open(port); 
        arduino.SetBaudRate(LibSerial::BaudRate::BAUD_115200);



    }

    Transmitter::~Transmitter() {
        arduino.Close();
    }

    private :
        rclcpp::Subscription<std_msgs::msg::String>::SharedPtr sub;
        LibSerial::SerialPort arduino;
        std::string port;


    void callback(const std_msgs::msg::String::SharedPtr msg) {
        RCLCPP_INFO(this->get_logger(), "Received: '%s'", msg->data.c_str());
        arduino.Write(msg->data);
    }

}

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<Transmitter>());
    rclcpp::shutdown();
    return 0;
}