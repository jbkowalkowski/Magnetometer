
#include <iostream>
#include <string>
#include <vector>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>
#include <termios.h>
#include <errno.h>

using std::cerr, std::cout;
using std::vector, std::string;

int main(int argc, char* argv[])
{
    termios tty;

    int port = open("/dev/ttyUSB0",O_RDWR);

    if(tcgetattr(port, &tty)!=0)
    {
        cerr << "bad tcgetattr " << errno << " " << strerror(errno) << "\n";
        return -1;
    }

    tty.c_cflag &= ~PARENB;
    tty.c_cflag &= ~CSTOPB;
    tty.c_cflag &= ~CSIZE;
    tty.c_cflag |= ~CS8;
    tty.c_cflag &= ~CRTSCTS;
    tty.c_cflag |= CREAD|CLOCAL;
    tty.c_lflag &= ~ICANON;
    tty.c_lflag &= ~ECHO;
    tty.c_lflag &= ~ECHOE;
    tty.c_lflag &= ~ECHONL;
    tty.c_lflag &= ~ISIG;
    tty.c_iflag &= ~(IXON|IXOFF|IXANY);
    tty.c_iflag &= ~(IGNBRK|BRKINT|PARMRK|ISTRIP|INLCR|IGNCR|ICRNL);
    tty.c_oflag &= ~OPOST;
    tty.c_oflag &= ~ONLCR;
    tty.c_cc[VTIME] = 10;
    tty.c_cc[VMIN] = 0;

    cfsetispeed(&tty, B9600);
    cfsetospeed(&tty, B9600);

    if(tcsetattr(port, TCSANOW, &tty)!=0)
    {
        cerr << "bad tcsetattr " << errno << " " << strerror(errno) << "\n";
        return -1;
    }

    cerr << "configured port\n";

    vector<string> cmds = {
        "0I\r\n",
        "0WC00B00\r\n",
        "01\r\n",
        "0WC02B02\r\n",
        "01\r\n",
        "0WC01B00\r\n",
        "01\r\n",
        "0WC08B11\r\n",
        "0sd\r\n"
    };

    //char cmd_1[] = "01\r";
    //char cmd_2[] = "0WC02B00\r";
    //char cmd_3[] = "0sd\r";

    for( auto& it:cmds)
    {
       if(write(port, it.c_str(), it.length())==-1) { cerr << strerror(errno) << "\n"; } 
    }

    //if(write(port, cmd_1, sizeof(cmd_1))==-1) { cerr << strerror(errno) << "\n"; }
    //if(write(port, cmd_2, sizeof(cmd_2))==-1) { cerr << strerror(errno) << "\n"; }
    //if(write(port, cmd_3, sizeof(cmd_3))==-1) { cerr << strerror(errno) << "\n"; }

    cerr << "wrote commands\n";

    unsigned char buf[500]; 

    size_t pos = 0;
    for(int i=0;i<11;++i)
    {
        auto sz = read(port, &buf[pos], sizeof(buf));
        if(sz<0) { cerr << "read failed: " << strerror(errno) << "\n"; continue; }
        pos+=sz;
        cerr << pos << "/" << sz << ".";
    }
    cerr <<"\n";
 
    for(int i=0; i< pos;++i)
    {
        cout << std::dec << i << ": " << std::hex << (unsigned)buf[i] << "  |  " << buf[i] << "\n";
    }
    //buf[pos]='\n';
    //cout << buf;

    return 0;
}