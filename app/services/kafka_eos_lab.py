from confluent_kafka import Consumer, Producer, TopicPartition


INPUT_TOPIC = "kafka-eos-input"
OUTPUT_TOPIC = "kafka-eos-output"
GROUP_ID = "kafka-eos-lab"

consumer = Consumer({
    "bootstrap.servers": "kafka:29092",
    "group.id": GROUP_ID,
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
    "isolation.level": "read_committed",
})

producer = Producer({
    "bootstrap.servers": "kafka:29092",
    "transactional.id": "kafka-eos-lab-producer",
})

def main():
    consumer.subscribe([INPUT_TOPIC])

    producer.init_transactions()

    try:
        while True:

            message = consumer.poll(1.0)

            if message is None:
                continue

            if message.error():
                print(f"KAFKA ERROR: {message.error()}")
                continue

            value = message.value().decode("utf-8")

            result = f"processed: {value}"

            producer.begin_transaction()

            producer.produce(
                topic=OUTPUT_TOPIC,
                key=message.key(),
                value=result.encode("utf-8"),
            )

            offsets = [
                TopicPartition(
                    message.topic(),
                    message.partition(),
                    message.offset() + 1,
                )
            ]

            producer.send_offsets_to_transaction(
                offsets,
                consumer.consumer_group_metadata(),
            )

            producer.commit_transaction()

            print("TRANSACTION COMMITTED")

    finally:
        consumer.close()


if __name__ == "__main__":
    main()

