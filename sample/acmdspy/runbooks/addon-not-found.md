# The ACM addons are installed several hours after the cluster is imported

## Description

The ACM addOns(`application-manager`, `cert-policy-controller`, `config-policy-controller`,
`governance-policy-framework`, `search-collector`) managed by the `KlusterletAddonConfig` are installed in the managed
cluster after several hours of the cluster importion. You can check with command below:

```shell
oc get managedclusteraddon -n <cluster-name> -o <addon-name>
```

and no `application-manager`, `cert-policy-controller`, `config-policy-controller`, `governance-policy-framework`,
`search-collector` return.

We expect these addons should be installed in several minutes after the cluster is imported.

## Meaning

These ACM addons are not successfully installed in clusters.

## Impact

Once the issue happens, the addon does not function properly. For instance, all policy and application related resources
will not be processed.

## Diagnosis

Check if the `KlusterletAddonConfig` with name `<cluster-name>` and namespace `<cluster-name>` exists on the hub cluster.

```shell
oc get klusterletaddonconfig -n <cluster-name> <cluster-name>
```

If the KlusterletAddonConfig is not found, check if there are other `KlusterletAddonConfig` resources in the cluster namespace.

```shell
oc get klusterletaddonconfig -n <cluster-name> -ojsonpath='{.items[].metadata.name}'
```

If the name of the KlusterletAddonConfig resource is not the same as the cluster name, you need recreate the KlusterletAddonConfig resource with cluster name to resolve this problem.

If the KlusterletAddonConfig is found, check the `spec.<addon-name>.enabled` field, the `enabled` field should be true, e.g.

```yaml
apiVersion: agent.open-cluster-management.io/v1
kind: KlusterletAddonConfig
metadata:
  name: <cluster-name>
  namespace: <cluster-name>
spec:
  applicationManager:
    enabled: true
```

Note: You should replace the `<cluster-name>` in the above code block with the name of the managed cluster