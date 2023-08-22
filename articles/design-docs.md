# Design Documents
The **Technical Design Document** (**"Design Doc"**) may be seen as the blueprint that specifies how a software system should be built.

While it may not define exact implementation details, it should be seen as a place where all questions that may arise during the implementation phase are already answered.

There is no one-size-fits-all template that will work for all design docs, but here follows some points to give ideas of what to consider when writing your design doc.

## Functional Design
**Functional** requirements deal with those parts of the solution that define what a system or system component must do.

We can further divide these functional requirements into two sub-sections; **User** and **System** requirements.

### User Requirements
**User Requirement** are functionalities directly interacted-with by the end user. Remember that in this context the term "user" may refer to a human or a machine. Both require an interface. The interface differs based on the type of user.

- Humans require a Graphical User Interface (GUI) which is typically a mobile or web app, ar a computer application of some variety.
- Machines require an Application Programming Interface (API), or some other method for data exchange.

I find that it is often times useful to design and define the interface before getting to the system requirements. Sometimes the user requirements will dictate certain decisions to be made when designing the system requirements.

Ultimately your system will be consumed by a user, it helps to make sure that the user can consume it in the intended way, so it is worthwhile having these "what" details bedded-down before dealing with the "how".

Design your interface first, discuss this with your consumers and adapt as necessary before designing your technical implementation.

#### The Interface
##### UI/UX
As a backend engineer, I will admit that I do not know too much about designing a great User Interface or Experience. Were this left to me we would still be experiencing the Internet in Times New Roman.

UI/UX is a specialist field, usually handled by designers. Their work product will include wireframes or similar mock-ups that can be referenced in your design doc.

##### API
I'll deal with two API variants here; gRPC nad REST
###### gRPC
There may be better ways of doing it, but I would usually simply include the protocol buffer structure in my design doc.
For example:
```protobuf
syntax = "proto3";

package helloworld;

// The greeting service definition.
service Greeter {
  // Sends a greeting
  rpc SayHello (HelloRequest) returns (HelloReply) {}

  rpc SayHelloStreamReply (HelloRequest) returns (stream HelloReply) {}
}

// The request message containing the user's name.
message HelloRequest {
  string name = 1;
}

// The response message containing the greetings
message HelloReply {
  string message = 1;
}
```
_Adapted from https://github.com/grpc/grpc/blob/master/examples/protos/helloworld.proto_

###### REST
When designing REST API interfaces, [OpenAPI](https://spec.openapis.org/oas/latest.html) can be very helpful. This enables you to design a very detailed API in a single YAML document ([have a look at this example](https://github.com/swagger-api/swagger-petstore/blob/master/src/main/resources/openapi.yaml)). Your spec can then be explored in the [Swagger Editor](https://swagger.io/tools/swagger-editor/).

### System Requirements
**System** requirements deal with those things that the user does not care about; will a microservices architecture be implemented? What database store should be used? In what language and framework will the solution be implemented?

Discuss how the implementation logic should flow. This is the most difficult section to define, as there is no template for this. No two implementations are the same.

Some points worth discussing:

#### Design Pattern
Discuss the design pattern that t he implementation might follow. Think MVC (Model-View-Controller), remembering that "View" might be an ApI interface rather than a GUI.

#### Asynchronous vs Synchronous processes
Will certain processes be handled asynchronously, employing event-based architecture to do so?

#### Tests
Define what tests are required.
- Unit tests
- Integration tests
- Load testing

#### Architecture
- Monolith or Microservice?

## Non-Functional
**Non-functional** requirements are specifications that define the operation of a system, rather than its specific behaviors.

Despite that name, _non-functional_ details are every bit as important as _functional_ equivalents.

### DevOps/Platform
- What platform will the system run on?
  - Cloud
  - Kubernetes
  - Bare metal (on prem or hosted)

### DataOps/Storage
- How will state be stored?
  - relational database (MySQL/Postgres/...)
  - document store (Redis/Mongo/...)
- Is event streaming required (Kafka/PubSub/...)
- Is a Content Delivery Network (CDN) required for the storage and serving of media?

### Scalability
- Is caching of data required?
  - Local (memory)
  - Distributed (Memcached/Redis/...)
  - edge (Cloudflare/Cloudfront/Fastly/...)
- Resource requirements?
  - how much CPU and Memory per host?
- How should the system scale?
  - Horizontally (e.g. add more pods or VNs)
  - Vertically (increase resources)

### Observability
- How are logs and metrics to be
  - collected (Graphite/Prometheus/Logstash...)?
  - and viewed (Grafana/Kibana/...)
- How should these be stored? And for how long?
- How will alerting be done? On what metrics and at which values?
