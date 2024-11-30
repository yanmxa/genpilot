import re
import os
import yaml
from typing import Optional
from pydantic import BaseModel, Field
import subprocess


class ClusterConfig(BaseModel):
    """
    A Pydantic model for validating and storing cluster configuration.
    """

    name: str = Field(..., description="The name of the cluster")
    kubeconfig: Optional[str] = Field(
        None, description="Path to the kubeconfig file for the cluster"
    )
    context: Optional[str] = Field(None, description="Context name for the cluster")
    namespace: Optional[str] = Field(None, description="Namespace for the cluster")

    @property
    def resolved_kubeconfig(self) -> str:
        """
        Resolves the kubeconfig path, ensuring a valid file or fallback.

        Returns:
            str: Resolved kubeconfig path.
        """
        if self.kubeconfig and os.path.exists(self.kubeconfig):
            return self.kubeconfig
        raise FileNotFoundError(
            f"Kubeconfig file '{self.kubeconfig}' does not exist or is not provided."
        )

    @property
    def resolved_context(self) -> str:
        """
        Resolves the context, ensuring it is not None.

        Returns:
            str: Resolved context.
        """
        if self.context:
            return self.context
        raise ValueError(f"Context is not provided for cluster '{self.name}'.")


class KubectlExecutor:
    """
    A class to manage multiple Kubernetes clusters by dynamically adding
    --kubeconfig and --context options to kubectl commands.
    """

    def __init__(self, default_kubeconfig: str = None, default_context: str = None):
        """
        Initialize the ClusterManager.

        Args:
            default_kubeconfig (str): Path to the default kubeconfig file.
            default_context (str): Default context name for the default kubeconfig.
        """
        self.default_kubeconfig = (
            default_kubeconfig
            or os.getenv("KUBECONFIG")
            or os.path.expanduser("~/.kube/config")
        )
        if not os.path.exists(self.default_kubeconfig):
            raise FileNotFoundError(
                f"Default kubeconfig '{self.default_kubeconfig}' does not exist."
            )
        self.default_context = default_context or None
        self._cluster_registry = {}

    def register_cluster(self, cluster: ClusterConfig):
        """
        Register a cluster using its configuration.

        Args:
            cluster (ClusterConfig): A validated cluster configuration object.
        """
        self._cluster_registry[cluster.name] = cluster

    @classmethod
    def from_yaml(
        cls, yaml_path: str, default_kubeconfig: str = None, default_context: str = None
    ):
        """
        Create a MultiKubeConfig instance from a YAML file.

        Args:
            yaml_path (str): Path to the YAML file containing cluster configurations.
            default_kubeconfig (str): Path to the default kubeconfig file.
            default_context (str): Default context name for the default kubeconfig.

        Returns:
            MultiKubeConfig: An instance of MultiKubeConfig initialized with the clusters from the YAML file.
        """
        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"YAML file '{yaml_path}' does not exist.")

        with open(yaml_path, "r") as yaml_file:
            config = yaml.safe_load(yaml_file)

        clusters = config.get("clusters", [])
        if not isinstance(clusters, list):
            raise ValueError("Invalid YAML format: 'clusters' must be a list.")

        instance = cls(
            default_kubeconfig=default_kubeconfig, default_context=default_context
        )

        for cluster_data in clusters:
            # print(cluster_data)
            cluster = ClusterConfig(
                name=cluster_data.get("name"),
                kubeconfig=cluster_data.get("kubeconfig", None),
                context=cluster_data.get("context", None),
                namespace=cluster_data.get("namespace", None),
            )
            instance.register_cluster(cluster)

        return instance

    def kubectl_cmd(
        self,
        cluster_name: str,
        command: str,
        input: str = None,
        timeout: float = 10,
    ) -> str:
        """
        Run the kubectl command within the specified cluster and return the final output.

        Args:
          cluster_name (str): The name of the cluster to access. the default value is 'default'
          command (str): The kubectl command to execute (e.g., "kubectl get pods").
          input: Input to be passed to the command (str or bytes). Useful for commands like `apply -f -`.
          timeout (int): Timeout for the command execution in seconds.

        Returns:
            str: The output of the command execution.

        Raises:
          subprocess.CalledProcessError: If the command fails.
          subprocess.TimeoutExpired: If the command exceeds the given timeout.

        Examples:
            1. Run a simple kubectl command:
                output = kubectl_command("cluster1", "kubectl get pods -n default")

            2. Apply a manifest from stdin:
                manifest = '''
                apiVersion: v1
                kind: Pod
                metadata:
                  name: nginx
                spec:
                  containers:
                  - name: nginx
                    image: nginx:latest
                '''
                output = kubectl_command("cluster1", "kubectl apply -f -", input=manifest)

            3. Patch a deployment with a JSON patch:
                patch = '{"spec": {"replicas": 3}}'
                output = kubectl_command("cluster1", "kubectl patch deployment nginx --type=merge -p", input=patch)

            4. Use a timeout to limit execution:
                output = kubectl_command("cluster1", "kubectl get pods -n default", timeout=10)
        """
        cluster_config: ClusterConfig = self._cluster_registry.get(cluster_name, None)
        # Use cluster-specific configuration or fallback to default
        kubeconfig = (
            cluster_config.kubeconfig if cluster_config else self.default_kubeconfig
        )
        context = cluster_config.context if cluster_config else self.default_context
        adapt_kubectl = self.override_kubectl_command(command, kubeconfig, context)
        try:
            output = subprocess.run(
                adapt_kubectl,
                shell=True,
                check=True,
                input=input,
                timeout=float(timeout),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            ).stdout.decode()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            return f"{adapt_kubectl}: \n{error.stdout.decode()}"
        return output

    def list_clusters(self):
        """
        List all registered clusters.

        Returns:
            dict: A dictionary of registered clusters and their configurations.
        """
        return self._cluster_registry

    def get_cluster(self, cluster_name) -> ClusterConfig:
        return self._cluster_registry.get(cluster_name, None)

    def append_kubectl_command(
        self, kubectl_command: str, kubeconfig: str = None, context: str = None
    ) -> str:
        """
        Prepares a `kubectl` command by appending `--kubeconfig` and `--context` only if they
        are not already present in the command.

        Args:
            kubectl_command (str): The original kubectl command.
            kubeconfig (str): Path to the kubeconfig file. If provided and not already present, adds `--kubeconfig`.
            context (str): Kubernetes context name. If provided and not already present, adds `--context`.

        Returns:
            str: The updated kubectl command with the appropriate parameters.
        """
        # Check if the command already contains --kubeconfig or --context
        if kubeconfig and "--kubeconfig" not in kubectl_command:
            kubectl_command += f" --kubeconfig {kubeconfig}"

        if context and "--context" not in kubectl_command:
            kubectl_command += f" --context {context}"

        return kubectl_command.strip()

    def override_kubectl_command(
        self, kubectl_command: str, kubeconfig: str = None, context: str = None
    ) -> str:
        """
        Prepares a `kubectl` command by explicitly appending or ignoring `--kubeconfig` and `--context`
        based on customer input.

        Args:
            kubectl_command (str): The original kubectl command.
            kubeconfig (str): Path to the kubeconfig file. If provided, adds `--kubeconfig` to the command.
            context (str): Kubernetes context name. If provided, adds `--context` to the command.

        Returns:
            str: The updated kubectl command with the appropriate parameters.
        """

        if kubeconfig:
            kubectl_command = re.sub(r"--kubeconfig\s+\S+", "", kubectl_command)
            kubectl_command += f" --kubeconfig {kubeconfig}"

        if context:
            kubectl_command = re.sub(r"--context\s+\S+", "", kubectl_command)
            kubectl_command += f" --context {context}"

        return kubectl_command.strip()
