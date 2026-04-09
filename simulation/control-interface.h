#ifndef CONTROL_INTERFACE_H
#define CONTROL_INTERFACE_H

#include "ns3/mobility-module.h"

class ControlInterface
{

public:

    ControlInterface();

    void AttachUav(ns3::Ptr<ns3::ConstantVelocityMobilityModel> uav);

    void Start();

    void SendState(const std::string &msg);

    bool IsConnected();

    void WaitForCommand();

    /* Route selection (0=UAV, 1=MasterSat, 2-5=SlaveSats) */
    int GetRouteId();

private:

    ns3::Ptr<ns3::ConstantVelocityMobilityModel> m_uav;

    int server_fd;
    int client_fd;

    bool connected;
    bool m_newCommand;

    int routeId;

    void ListenLoop();

};

#endif
