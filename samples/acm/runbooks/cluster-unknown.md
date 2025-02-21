# The Status of Cluster(ManagedCluster) Is Unknown

## Description

The ManagedCluster on the hub cluster has a condition of type `ManagedClusterConditionAvailable` with a `status` of `Unknown`.
You are able to check the status of this condition with command line below,

```bash
oc get managedcluster <cluster-name> -o jsonpath="{.status.conditions[?(@.type==\"ManagedClusterConditionAvailable\")]}" --context <hub-cluster-context>
```

## Meaning

When the klusterlet registration agent starts running on the managed cluster, it updates a Lease resource in the cluster namespace on the hub cluster every `N` seconds, where `N` is configured in the `spec.leaseDurationSeconds` of the `ManagedCluster`. If the Lease resource is not updated in the past `5 * N` seconds, the `status` of the `ManagedClusterConditionAvailable` condition for this managed cluster will be set to `Unknown`. Once the klusterlet registration agent connects back to the hub cluster and continues to update the Lease resource, the `ManagedCluster` will become available automatically.

## Impact

Once this issue happens,

- Usually both the `klusterlet` agent and add-on agents cannot connect to the hub cluster. Changes on `ManifestWorks` and other add-on specific resources on the hub cluster can not be pulled to the managed cluster;

- The status of the `Available` condition of all ManagedClusterAddOns for this managed cluster will be set to `Unknown` as well;

## Diagnosis

The diagnostic instructions may follow two paths: klusterlet resources and controllers

### klusterlet resource(CR)

(1) check the CR resource on the managed cluster

```bash
# Klusterlet CR
oc get klusterlet klusterlet --context <managed-cluster-context>
```

If the above resources is missing, that means the cluster isn't joining to hub cluster. And you can try to join the cluster to hub.

If they all exists, check the status of the klusterlet

(2) check the status of klusterlet resource on the managed cluster

```bash
oc get klusterlet klusterlet --context <managed-cluster-context>  -oyaml
```

The status maybe contain the information why the klusterlet registration agent (`deploy/klusterlet-registration-agent -n open-cluster-management-agent`) cann't update the cluster lease in the hub. 

A common issue is an invalid secret `secret/hub-kubeconfig-secret -n open-cluster-management-agent --context <managed-cluster-context>` on the managed cluster used to connect to the hub cluster. However, it's essential to first identify the root cause when the Klusterlet registration and Klusterlet agent are not functioning as expected.

If there are no obvious error in the klusterlet status, consider other potential causes for the unknown status.

### klusterlet controllers

The **related controllers** about this issue include:

- **klusterlet controller**(`deploy/klusterlet -n open-cluster-management`):  reconciles the customize resource(CR) klusterlet. And is responsible for creating the **klusterlet registration agent controller**(`deploy/klusterlet-registration-agent -n open-cluster-management-agent`).

- **klusterlet registration agent controller**(`deploy/klusterlet-registration-agent -n open-cluster-management-agent`): which updates the cluster lease on the hub cluster.

(1) Check if the existence of the klusterlet registration below on the managed cluster.

```bash
# get the deployment
oc -n open-cluster-management-agent get deploy/klusterlet-registration-agent --context <managed-cluster-context>
```

The unknown status is caused by the `klusterlet registration agent` instance not running, or there may be internal issues preventing it from updating the managed cluster on the hub. We need to explore further with the following two cases:

If the pod instance of the deployment is present, go to (2) try to check its logs to see if any errors are preventing the creation of the klusterlet registration agent.
If the the pod instance of the deployment is not present, go to (3) check the klusterlet agent which is responsible create the registration agent.

(2) If there is an instance of the klusterlet registration agent running on the managed cluster, check its log on it.

```bash
oc -n open-cluster-management-agent logs -l app=klusterlet-registration-agent --context <managed-cluster-context>
```

If the `klusterlet-registration-agent` deployment is not found, then go to the next step to check the klusterlet controller instance. Which is responsible to create the klusterlet registration agent!

(3) Check the `klusterlet controller` instance(deployment and pod)

```bash
# the deployment
oc -n open-cluster-management get deploy/klusterlet --context <managed-cluster-context>
```

If the `klusterlet` controller instance isn't running, this is why the klusterlet registration agent instance is not operational! Then get the deployment detail(like `oc describe deploy/klusterlet ...`) of the klusterlet controller to find why the instance hasn't running and return the result.

If the `klusterlet` controller(pod) exists, check the logs of the klusterlet controller.

(4) If there is an instance of the `klusterlet` controller running on the managed cluster, check its logs on the managed cluster.

```bash
oc -n open-cluster-management logs -l app=klusterlet --context <managed-cluster-context>
```

If the klusterlet controller is running and no errors are found in the klusterlet log, consider other potential causes for the unknown status.