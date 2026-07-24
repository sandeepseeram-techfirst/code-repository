## Streaming & Messaging

In Microservices architecture, services need to communicate with one another and keep each other in the loop. Each time a service does something, it sends a message about that particular event.

**Streaming and messaging tools enable service-to-service communication by transporting messages (i.e. events) between systems.** Individual services connect to the messaging service to either publish events, read messages from other services, or both. This dynamic creates an environment where individual apps are either publishers, meaning they write events, or subscribers that read events, or more likely both.

**As services proliferate, application environments become increasingly complex, making the management of communication between apps more challenging. A streaming or messaging platform provides a central place to publish and read all the events that occur within a system, allowing applications to work together without necessarily knowing anything about one another.**


## Message Busses & Streaming Technologies for Choreography

Different infrastructure layers support event-driven choreography depending on whether you need point-to-point queues, publish-sub streaming logs, or serverless event routers:

* **Event Routers / Pub-Sub:** Amazon EventBridge (serverless event bus with content-based filtering), Amazon SNS/SQS.

* **Distributed Message Brokers & Streams:** Apache Kafka, Amazon MSK, RabbitMQ, or ActiveMQ used alongside distributed frameworks like MassTransit or Camunda Platform 8 connectors.

* **Streaming Queues:** Enterprise tools like IBM MQ Streaming Queues allow near-identical message duplication to secondary targets (like a data lake or analytics pipeline) without disrupting the primary queue flow.