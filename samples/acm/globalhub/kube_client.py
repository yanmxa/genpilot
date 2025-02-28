from kubernetes import client, config
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from tools import KubectlExecutor


def kube_api_client(
    kube_config_file: str = None, context: str = None
) -> client.ApiClient:
    """
    Connect to Kubernetes in the following order:
    1. Explicit kubeconfig file and context.
    2. KUBECONFIG environment variable or default kubeconfig.
    3. In-cluster configuration.

    Returns:
        client.ApiClient: A Kubernetes generic API client for OpenAPI client library builds.
    """
    try:
        if kube_config_file:
            kube_client_config = config.new_client_from_config(
                config_file=kube_config_file, context=context
            )
            print(
                f"Connected to Kubernetes cluster using kubeconfig: {kube_config_file} and context: {context or 'default'}"
            )
            return kube_client_config

        kube_config_env = os.getenv("KUBECONFIG")
        kube_client_config = config.new_client_from_config(
            config_file=kube_config_env, context=context
        )
        print(
            f"Connected to Kubernetes cluster using KUBECONFIG: {kube_config_env or '~/.kube/config'} and context: {context or 'default'}"
        )
        return kube_client_config

    except Exception as e:
        raise RuntimeError(f"Failed to connect to Kubernetes cluster: {e}")


from sample.globalhub.kafka_conn import (
    get_kafka_credentials_by_secret,
    check_kafka_connectivity,
    consume_messages,
)

current_dir = os.path.dirname(os.path.realpath(__file__))

if __name__ == "__main__":

    # Namespace and secret details
    # kubeconfig_path = "/tmp/demo-hub-a"
    # namespace = "multicluster-global-hub-agent"
    # secret_name = "transport-config"

    executor = KubectlExecutor.from_yaml(
        os.path.join(current_dir, "cluster-options.yaml")
    )

    global_hub_config = executor.get_cluster("global-hub")
    managed_hub_config = executor.get_cluster("managed-hub-a")
    print(global_hub_config)

    secret_name = "transport-config"

    # global hub
    kube_client = client.CoreV1Api(
        api_client=kube_api_client(kube_config_file=global_hub_config.kubeconfig)
    )
    kafka_config = get_kafka_credentials_by_secret(
        secret_name, global_hub_config.namespace, kube_client
    )

    print("Kafka Configuration:")
    print(f"Bootstrap Server: {kafka_config.bootstrap_server}")
    print(f"CA Cert: {kafka_config.ca_cert}")
    print(f"Client Cert: {kafka_config.client_cert}")
    print(f"Client Key: {kafka_config.client_key}")
    print(f"Spec Topic: {kafka_config.spec_topic}")
    print(f"Status Topic: {kafka_config.status_topic}")

    # Check Kafka connectivity
    if check_kafka_connectivity(kafka_config):
        print("Success to connect to Kafka transport.")
        # Consume messages from the specified topic
        # topic = kafka_config.status_topic or "default-topic"
        # consume_messages(kafka_config, topic)
    else:
        print("Failed to connect to Kafka transport.")

    # consume_messages(kafka_config, "gh-status.demo-hub-a")
