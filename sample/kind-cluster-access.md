
You can interact with all clusters (hub and managed) using the `KUBECONFIG` environment variable by switching contexts to access different clusters.

Each of these clusters is created using KinD. To access the hub cluster, use the `kind-hub` context.

For managed clusters, switch to the corresponding context in the format `kind-<ManagedCluster>`. For example, to retrieve all pods on `cluster1`, use the following command:

```bash
kubectl get pods -A --context kind-cluster1
```

**You should alway specify which context the to access the cluster when give the task to engineer!!!**