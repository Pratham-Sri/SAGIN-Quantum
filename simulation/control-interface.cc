#include "control-interface.h"

#include "ns3/core-module.h"
#include "ns3/mobility-module.h"

#include <iostream>
#include <thread>
#include <cstring>

#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>

using namespace ns3;

ControlInterface::ControlInterface()
{
    server_fd = -1;
    client_fd = -1;
    connected = false;
    m_newCommand = false;
    routeId = 0;
}

void ControlInterface::AttachUav(
    Ptr<ConstantVelocityMobilityModel> uav)
{
    m_uav = uav;
}

void ControlInterface::Start()
{
    std::cout << "Starting control interface server..." << std::endl;

    std::thread serverThread(
        &ControlInterface::ListenLoop,
        this);

    serverThread.detach();
}

bool ControlInterface::IsConnected()
{
    return connected;
}

int ControlInterface::GetRouteId()
{
    return routeId;
}

void ControlInterface::ListenLoop()
{
    std::cout << "Control server thread running" << std::endl;

    struct sockaddr_in address;
    int opt = 1;

    server_fd = socket(AF_INET, SOCK_STREAM, 0);

    if(server_fd < 0)
    {
        std::cerr << "Failed to create socket" << std::endl;
        return;
    }

    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR,
               &opt, sizeof(opt));

    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(9001);

    if(bind(server_fd, (struct sockaddr*)&address,
            sizeof(address)) < 0)
    {
        std::cerr << "Bind failed on port 9001" << std::endl;
        close(server_fd);
        return;
    }

    listen(server_fd, 3);

    std::cout << "Waiting for RL agent on port 9001..." << std::endl;

    socklen_t addrlen = sizeof(address);

    client_fd = accept(server_fd,
        (struct sockaddr*)&address,
        &addrlen);

    if(client_fd < 0)
    {
        std::cerr << "Accept failed" << std::endl;
        close(server_fd);
        return;
    }

    std::cout << "Controller connected" << std::endl;
    connected = true;

    char buffer[2048];

    while(true)
    {
        int valread = read(client_fd, buffer, sizeof(buffer) - 1);

        if(valread <= 0)
        {
            std::cout << "Controller disconnected" << std::endl;
            connected = false;
            break;
        }

        buffer[valread] = '\0';

        /* Parse multiple commands separated by newlines */
        char* line = strtok(buffer, "\n");

        while(line != nullptr)
        {
            double dx, dy;
            int rid;

            if(sscanf(line, "MOVE %lf %lf", &dx, &dy) == 2)
            {
                m_uav->SetVelocity(Vector(dx, dy, 0));
            }
            else if(sscanf(line, "ROUTE %d", &rid) == 1)
            {
                if(rid >= 0 && rid <= 5)
                {
                    routeId = rid;
                }
                else
                {
                    std::cerr << "Invalid route ID: " << rid << std::endl;
                }
            }
            /* Backward compatibility with OFFLOAD command */
            else if(sscanf(line, "OFFLOAD %d", &rid) == 1)
            {
                routeId = (rid == 0) ? 0 : 1;
            }

            m_newCommand = true;
            line = strtok(nullptr, "\n");
        }
    }

    close(client_fd);
    close(server_fd);
}

void ControlInterface::SendState(const std::string &msg)
{
    if(client_fd > 0 && connected)
    {
        ssize_t sent = send(client_fd, msg.c_str(), msg.size(), MSG_NOSIGNAL);
        if(sent < 0)
        {
            std::cerr << "Failed to send state to controller" << std::endl;
            connected = false;
        }
    }
}

void ControlInterface::WaitForCommand()
{
    m_newCommand = false;
    while(!m_newCommand && connected)
    {
        usleep(100);
    }
}
