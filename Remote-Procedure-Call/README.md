## Remote Procedure Call [RPC] WORKSHOP

 *Remote Procedure Call (RPC) is a particular technique enabling applications to talk to each other. It's one way of structuring app communication.*

* Modern apps are composed of numerous individual services that must communicate in order to collaborate. RPC is one option for handling the communication between applications.

* RPC provides a tightly coupled and highly opinionated way of handling communication between services. It allows for bandwidth-efficient communications and many programming languages enable RPC interface implementations.

**Remote Procedure Call (RPC)** is a communication pattern that lets a program invoke a function on another process or machine as if it were a local function call. The developer writes *result = service.GetUser(id);* 
RPC handles locating the remote service, serializing the request, sending it over the network, and returning the response.

Client app
   │  GetUser(user_id)
   ▼
Client stub ── marshal request ──► network ──► Server stub
                                                  │ unmarshal
                                                  ▼
                                            Server procedure
                                                  │ return value
Server stub ── marshal response ──► network ──► Client stub
   ▼
Client app receives result


### RPC follows a client-server request/response model:

1. Client calls a local stub — The application calls a generated proxy function that looks like the real remote method.

2. Marshalling — The client stub converts the method name and arguments into a wire-format message, such as Protocol Buffers, JSON, or another serialization format.

3. Network transport — The RPC runtime sends the request to the server, commonly over TCP/HTTP/HTTP2.

4. Server stub unmarshals — The server receives the message, deserializes the arguments, identifies the target method, and invokes the actual implementation.

5. Execution and reply — The server executes the procedure and serializes the return value or error into a response message.

6. Client resumes — The client stub deserializes the response and returns the result to the caller. In synchronous RPC, the client typically blocks until the reply arrives or a timeout occurs.