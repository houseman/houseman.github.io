# Asynchronous events

We are building a simple messaging application, that can be used to send text and media to one or more contacts.

![A very simple messaging service](https://i.imgur.com/KIFlvjf.png)

Messages are relayed through a server.
- Sender creates a text or media Message, destined for one or more Recipients
- Service
  - receives Message
  - sends an acknowledgement of receipt to Sender
  - places Message text or media in data store
  - looks up Recipients unique identifier
  - looks up current IP address for Recipients
  - sends Message notification to Recipient devices
- Recipient
  - downloads Message from data store
  - sends acknowledgement of receipt to Service
- Service
  - sends acknowledgement of delivery to Sender
  - deletes Message from data store
- Recipient
  - reads Message
  - sends acknowledgement of read to Service
- Service
  - sends acknowledgement of read to Sender

```mermaid
sequenceDiagram
    actor Sender
    box A Very Simple Messaging Service
    participant Service
    participant DS as Data Store
    participant DB as Database
    end
    actor Recipient

    note over Sender: creates a Message to Recipients
    Sender->>+Service: sends Message
    Service-->>-Sender: ack receipt
    Service->>+DS: store Message
    DS-->>-Service: ack stored
    Service->>+DB: finds Recipients
    DB-->>-Service: ack data
    Service->>+Recipient: notify of Message
    Recipient-->>-Service: ack
    Recipient->>+DS: request Message
    DS-->>-Recipient: Message
    Recipient->>+Service: ack Message received
    Service-->>-Recipient: ack
    Service->>+Sender: ack Message delivered
    Sender-->>-Service: ack
    Service->>+DS: delete Message
    DS-->>-Service: ack
    note over Recipient: reads message
    Recipient->>+Service: ack Message read
    Service-->>-Recipient: ack received
    Service->>+Sender: ack Message read
    Sender-->>-Service: ack received
```
As can be seen from the above, many steps are involved in the transmission of a message!

