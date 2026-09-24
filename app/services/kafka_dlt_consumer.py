import time

from confluent_kafka import Consumer, Producer


class KafkaDLTConsumer:
    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        topic: str,
        dlt_topic: str,
        max_retries: int,
        retry_delay: float,
    ):
        self.topic = topic
        self.dlt_topic = dlt_topic
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.consumer = Consumer(
            {
                "bootstrap.servers": bootstrap_servers,
                "group.id": group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
            }
        )

        self.producer = Producer(
            {
                "bootstrap.servers": bootstrap_servers,
            }
        )

    def process_message(self, message):
        value = message.value().decode()

        print(
            f"PROCESSING: "
            f"partition={message.partition()} "
            f"offset={message.offset()} "
            f"value={value!r}"
        )

        if value == "FAIL":
            raise RuntimeError("TEST PROCESSING ERROR")

        print("PROCESSING SUCCESS")

    def send_to_dlt(self, message, error: Exception):
        self.producer.produce(
            topic=self.dlt_topic,
            key=message.key(),
            value=message.value(),
            headers=[
                ("x-original-topic", message.topic()),
                (
                    "x-original-partition",
                    str(message.partition()),
                ),
                (
                    "x-original-offset",
                    str(message.offset()),
                ),
                (
                    "x-error",
                    str(error),
                ),
            ],
        )

        self.producer.flush()

    def run(self):
        self.consumer.subscribe([self.topic])

        try:
            while True:
                message = self.consumer.poll(1.0)

                if message is None:
                    continue

                if message.error():
                    print(
                        f"KAFKA ERROR: {message.error()}"
                    )
                    continue

                retry_count = 0

                while True:
                    try:
                        self.process_message(message)
                        break

                    except Exception as exc:
                        retry_count += 1

                        print(
                            f"PROCESSING ERROR: "
                            f"attempt={retry_count} "
                            f"error={exc}"
                        )

                        if retry_count > self.max_retries:
                            self.send_to_dlt(
                                message,
                                exc,
                            )

                            print(
                                "MESSAGE SENT TO DLT"
                            )
                            break

                        time.sleep(
                            self.retry_delay
                        )

                self.consumer.commit(
                    message=message
                )

        finally:
            self.consumer.close()
            self.producer.flush()


def main():
    consumer = KafkaDLTConsumer(
        bootstrap_servers="kafka:29092",
        group_id="kafka-dlt-lab",
        topic="kafka-dlt-lab",
        dlt_topic="kafka-dlt-lab.dlq",
        max_retries=3,
        retry_delay=1.0,
    )

    consumer.run()


if __name__ == "__main__":
    main()