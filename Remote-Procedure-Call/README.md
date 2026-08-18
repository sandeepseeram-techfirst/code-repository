## Remote Procedure Call [RPC] WORKSHOP

 *Remote Procedure Call (RPC) is a particular technique enabling applications to talk to each other. It's one way of structuring app communication.*

* Modern apps are composed of numerous individual services that must communicate in order to collaborate. RPC is one option for handling the communication between applications.

* RPC provides a tightly coupled and highly opinionated way of handling communication between services. It allows for bandwidth-efficient communications and many programming languages enable RPC interface implementations.

**Remote Procedure Call (RPC)** is a communication pattern that lets a program invoke a function on another process or machine as if it were a local function call. The developer writes *result = service.GetUser(id);* 
RPC handles locating the remote service, serializing the request, sending it over the network, and returning the response.