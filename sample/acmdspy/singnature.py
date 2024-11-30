import dspy


class KubeEngineer(dspy.Signature):
    """A Kubernetes engineer. Try to explicitly identify the cluster name, resource type, name, and namespace from the task to perform actions in the cluster using tools or kubectl commands."""

    task: str = dspy.InputField()
    headings: list[str] = dspy.OutputField()
    entities: list[dict[str, str]] = dspy.OutputField(
        desc="a list of entities and their metadata"
    )
