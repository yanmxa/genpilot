import tempfile
import os
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from kubernetes import client, config
import base64
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class KafkaConfig(BaseModel):
    bootstrap_server: str = Field(alias="bootstrap.server")
    status_topic: Optional[str] = Field(default=None, alias="topic.status")
    spec_topic: Optional[str] = Field(default=None, alias="topic.spec")
    cluster_id: Optional[str] = Field(default=None, alias="cluster.id")
    ca_cert: Optional[str] = Field(default=None, alias="ca.crt")
    client_cert: Optional[str] = Field(default=None, alias="client.crt")
    client_key: Optional[str] = Field(default=None, alias="client.key")
    ca_secret_name: Optional[str] = Field(default=None, alias="ca.secret")
    client_secret_name: Optional[str] = Field(default=None, alias="client.secret")

    @field_validator("ca_cert", "client_cert", "client_key", mode="before")
    def decode_base64(cls, value):
        if value:
            return base64.b64decode(value).decode("utf-8")
        return value


# Function to fetch Kafka configuration from Kubernetes Secret
def get_kafka_credentials_by_secret(
    secret_name: str, namespace: str, kube_client: client.CoreV1Api
) -> KafkaConfig:
    try:
        secret = kube_client.read_namespaced_secret(secret_name, namespace)
        if "kafka.yaml" not in secret.data:
            raise ValueError(
                f"The `kafka.yaml` key is missing in the secret: {secret_name}"
            )

        kafka_yaml = base64.b64decode(secret.data["kafka.yaml"]).decode("utf-8")

        # Parse YAML into KafkaConfig
        import yaml

        kafka_config_dict = yaml.safe_load(kafka_yaml)

        kafka_config = KafkaConfig(**kafka_config_dict)

        # Populate additional credentials from secrets if needed
        parse_credentials(namespace, kube_client, kafka_config)

        return kafka_config

    except Exception as e:
        raise RuntimeError(f"Error retrieving Kafka credentials: {e}")


# Function to populate credentials from referenced secrets
def parse_credentials(
    namespace: str, kube_client: client.CoreV1Api, kafka_config: KafkaConfig
):
    # Retrieve CA cert from secret if specified
    if kafka_config.ca_secret_name:
        ca_secret = kube_client.read_namespaced_secret(
            kafka_config.ca_secret_name, namespace
        )
        if "ca.crt" not in ca_secret.data:
            raise ValueError(
                f"The CA cert is missing in the secret: {kafka_config.ca_secret_name}"
            )
        kafka_config.ca_cert = base64.b64decode(ca_secret.data["ca.crt"]).decode(
            "utf-8"
        )

    # Retrieve client cert and key from secret if specified
    if kafka_config.client_secret_name:
        client_secret = kube_client.read_namespaced_secret(
            kafka_config.client_secret_name, namespace
        )
        if "tls.crt" not in client_secret.data or "tls.key" not in client_secret.data:
            raise ValueError(
                f"The client cert or key is missing in the secret: {kafka_config.client_secret_name}"
            )
        kafka_config.client_cert = base64.b64decode(
            client_secret.data["tls.crt"]
        ).decode("utf-8")
        kafka_config.client_key = base64.b64decode(
            client_secret.data["tls.key"]
        ).decode("utf-8")

        if not kafka_config.client_cert or not kafka_config.client_key:
            raise ValueError(
                f"The client cert or key must not be empty: {kafka_config.client_secret_name}"
            )


def create_kafka_consumer(
    kafka_config: KafkaConfig, topic: str, group_id: str
) -> KafkaConsumer:
    """
    Create a Kafka consumer using kafka-python with dynamically created temporary files for certificates.
    """
    # Create temporary files for the certificates
    ca_cert_file = tempfile.NamedTemporaryFile(delete=False)
    client_cert_file = tempfile.NamedTemporaryFile(delete=False)
    client_key_file = tempfile.NamedTemporaryFile(delete=False)

    try:
        # Write certificate content to temporary files
        ca_cert_file.write(kafka_config.ca_cert.encode("utf-8"))
        client_cert_file.write(kafka_config.client_cert.encode("utf-8"))
        client_key_file.write(kafka_config.client_key.encode("utf-8"))

        # Close the files to flush content
        ca_cert_file.close()
        client_cert_file.close()
        client_key_file.close()

        # Configure Kafka consumer
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=kafka_config.bootstrap_server,
            security_protocol="SSL",
            ssl_cafile=ca_cert_file.name,
            ssl_certfile=client_cert_file.name,
            ssl_keyfile=client_key_file.name,
            group_id=group_id,
            auto_offset_reset="earliest",
        )

        return consumer

    except Exception as e:
        # Clean up temporary files in case of error
        os.unlink(ca_cert_file.name)
        os.unlink(client_cert_file.name)
        os.unlink(client_key_file.name)
        raise RuntimeError(f"Failed to create Kafka consumer: {e}")


def check_kafka_connectivity(kafka_config: KafkaConfig) -> bool:
    """
    Check Kafka connectivity by creating a KafkaConsumer and attempting to fetch metadata.
    """
    try:
        # Create a KafkaConsumer
        consumer = create_kafka_consumer(
            kafka_config, "__consumer_offsets", "connectivity-check"
        )

        # Attempt to fetch metadata for a test topic
        consumer.partitions_for_topic("__consumer_offsets")

        # Close the consumer after successful metadata retrieval
        consumer.close()
        return True
    except KafkaError as e:
        print(f"Kafka connectivity check failed: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during Kafka connectivity check: {e}")
        return False


def consume_messages(kafka_config: KafkaConfig, topic: str):
    """
    Consume messages from a Kafka topic using kafka-python.
    """
    consumer = create_kafka_consumer(kafka_config, topic, "message-consumer")
    print(f"Listening for messages on topic: {topic}")

    try:
        for message in consumer:
            print(
                f"Received message: {message.value.decode('utf-8')} on topic {message.topic}"
            )
    except KeyboardInterrupt:
        print("Consumer interrupted by user.")
    finally:
        consumer.close()


if __name__ == "__main__":
    # Load Kubernetes configuration
    config.load_kube_config()

    # Kubernetes client for secrets
    kube_client = client.CoreV1Api()

    # Namespace and secret details
    namespace = "multicluster-global-hub-agent"
    secret_name = "transport-config"

    # Fetch Kafka credentials
    kafka_config = get_kafka_credentials_by_secret(secret_name, namespace, kube_client)

    print("Kafka Configuration:")
    print(f"Bootstrap Server: {kafka_config.bootstrap_server}")
    print(f"CA Cert: {kafka_config.ca_cert}")
    print(f"Client Cert: {kafka_config.client_cert}")
    print(f"Client Key: {kafka_config.client_key}")

    # Check Kafka connectivity
    if check_kafka_connectivity(kafka_config):
        print("Success to connect to Kafka transport.")
        # Consume messages from the specified topic
        # topic = kafka_config.status_topic or "default-topic"
        # consume_messages(kafka_config, topic)
    else:
        print("Failed to connect to Kafka transport.")
