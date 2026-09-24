import socket
import os

from confluent_kafka import Consumer


def env_int(name: str, default: int) -> int:
    value = os.getenv(name, str(default))
    return int(value)


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    normalized = value.strip().lower()

    if normalized in {"1", "true", "yes", "on"}:
        return True

    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(
        f"Invalid boolean value for {name}: {value}"
    )


class KafkaRebalanceLabConsumer:
    def __init__(
            self,
            bootstrap_servers: str,
            group_id: str,
            topic: str,
    ):
        self.topic = topic

        self.consumer = Consumer(
            {
                "bootstrap.servers": bootstrap_servers,
                "group.id": group_id,

                "auto.offset.reset": os.getenv(
                    "KAFKA_AUTO_OFFSET_RESET",
                    "earliest",
                ),

                "enable.auto.commit": env_bool(
                    "KAFKA_ENABLE_AUTO_COMMIT",
                    False,
                ),

                "enable.auto.offset.store": env_bool(
                    "KAFKA_ENABLE_AUTO_OFFSET_STORE",
                    False,
                ),

                "heartbeat.interval.ms": env_int(
                    "KAFKA_HEARTBEAT_INTERVAL_MS",
                    3_000,
                ),

                "session.timeout.ms": env_int(
                    "KAFKA_SESSION_TIMEOUT_MS",
                    10_000,
                ),

                "max.poll.interval.ms": env_int(
                    "KAFKA_MAX_POLL_INTERVAL_MS",
                    60_000,
                ),

                "group.protocol": "classic",
            }
        )

        self.instance_id = socket.gethostname()

    def on_assign(self, consumer, partitions):
        print(
            f"[{self.instance_id}] "
            "PARTITIONS ASSIGNED:",
            [
                f"{partition.topic}:{partition.partition}"
                for partition in partitions
            ],
        )

    def on_revoke(self, consumer, partitions):
        print(
            f"[{self.instance_id}] "
            "PARTITIONS REVOKED:",
            [
                f"{partition.topic}:{partition.partition}"
                for partition in partitions
            ],
        )

    def on_lost(self, consumer, partitions):
        print(
            f"[{self.instance_id}] "
            "PARTITIONS LOST:",
            [
                f"{partition.topic}:{partition.partition}"
                for partition in partitions
            ],
        )

    def run(self):
        self.consumer.subscribe(
            [self.topic],
            on_assign=self.on_assign,
            on_revoke=self.on_revoke,
            on_lost=self.on_lost,
        )

        try:
            while True:
                message = self.consumer.poll(1.0)

                if message is None:
                    continue

                if message.error():
                    print(
                        f"[{self.instance_id}] "
                        f"KAFKA ERROR: {message.error()}"
                    )
                    continue

                print(
                    f"[{self.instance_id}] "
                    f"MESSAGE: "
                    f"partition={message.partition()} "
                    f"offset={message.offset()} "
                    f"value={message.value()!r}"
                )

        finally:
            self.consumer.close()


def main():
    consumer = KafkaRebalanceLabConsumer(
        bootstrap_servers="kafka:29092",
        group_id="kafka-rebalance-lab",
        topic="kafka-rebalance-lab",
    )

    consumer.run()


if __name__ == "__main__":
    main()
