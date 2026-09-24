import socket

from confluent_kafka import Producer, TopicPartition


class KafkaTransactionalProducer:
    def __init__(
        self,
        bootstrap_servers: str,
        name: str,
    ):
        transactional_id = (
            f"{name}-{socket.gethostname()}"
        )

        self.producer = Producer({
            "bootstrap.servers": bootstrap_servers,
            "enable.idempotence": True,
            "acks": "all",
            "transactional.id": transactional_id,
        })

        self.producer.init_transactions()

    def forward_with_offset(
        self,
        topic: str,
        key: str,
        value: bytes,
        headers: list[tuple[str, bytes]],
        source_message,
        consumer,
    ):
        self.producer.begin_transaction()

        try:
            self.producer.produce(
                topic=topic,
                key=key,
                value=value,
                headers=headers,
            )

            offset = TopicPartition(
                source_message.topic(),
                source_message.partition(),
                source_message.offset() + 1,
            )

            self.producer.send_offsets_to_transaction(
                [offset],
                consumer.consumer_group_metadata(),
            )

            self.producer.commit_transaction()

        except Exception:
            self.producer.abort_transaction()
            raise

    def close(self):
        self.producer.flush()