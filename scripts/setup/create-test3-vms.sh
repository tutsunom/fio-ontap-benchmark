#!/bin/bash
# 検証3用 VM 作成スクリプト
# SAN 6台 + NAS 6台 = 12台（各ノード2台ずつ）

NS="utubo-test"
WORKERS=("wk-01.cluster.example.com" "wk-02.cluster.example.com" "wk-03.cluster.example.com")

create_vm() {
  local name=$1
  local sc=$2       # storageClassName
  local node=$3     # target node
  local datadisk_size=$4

  echo "Creating VM: $name (sc=$sc, node=$node, datadisk=$datadisk_size)"

  cat <<EOF | oc apply -f -
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  labels:
    app: $name
  name: $name
  namespace: $NS
spec:
  dataVolumeTemplates:
  - metadata:
      name: ${name}-rootdisk
    spec:
      sourceRef:
        kind: DataSource
        name: rhel10
        namespace: openshift-virtualization-os-images
      storage:
        resources:
          requests:
            storage: 30Gi
        storageClassName: ontap-san
  - metadata:
      name: ${name}-datadisk
    spec:
      source:
        blank: {}
      storage:
        resources:
          requests:
            storage: $datadisk_size
        storageClassName: $sc
  runStrategy: RerunOnFailure
  template:
    metadata:
      labels:
        kubevirt.io/domain: $name
    spec:
      nodeSelector:
        kubernetes.io/hostname: $node
      domain:
        cpu:
          cores: 4
        devices:
          disks:
          - disk:
              bus: virtio
            name: rootdisk
          - disk:
              bus: virtio
            name: datadisk
          - disk:
              bus: virtio
            name: cloudinitdisk
          interfaces:
          - bridge: {}
            name: nic0
        machine:
          type: q35
        memory:
          guest: 8Gi
      networks:
      - multus:
          networkName: default/vlan242-linuxbr
        name: nic0
      volumes:
      - dataVolume:
          name: ${name}-rootdisk
        name: rootdisk
      - dataVolume:
          name: ${name}-datadisk
        name: datadisk
      - cloudInitNoCloud:
          userData: |
            #cloud-config
            user: cloud-user
            password: redhat
            chpasswd:
              expire: false
            ssh_pwauth: true
            ssh_authorized_keys:
              - $(cat /root/.ssh/id_ed25519.pub)
        name: cloudinitdisk
EOF
}

echo "=== Creating 検証3 VMs ==="

# SAN VMs: fio-san-{1..6} on wk-01 through wk-03 (2 per node)
for i in 1 2; do
  for j in 0 1 2; do
    idx=$(( (j * 2) + i ))
    create_vm "fio-san-${idx}" "ontap-san" "${WORKERS[$j]}" "100Gi"
  done
done

# NAS VMs: fio-nas-{1..6} on wk-01 through wk-03 (2 per node)
for i in 1 2; do
  for j in 0 1 2; do
    idx=$(( (j * 2) + i ))
    create_vm "fio-nas-${idx}" "ontap-nas" "${WORKERS[$j]}" "100Gi"
  done
done

echo ""
echo "=== Waiting for VMs to be ready ==="
for prefix in san nas; do
  for idx in $(seq 1 6); do
    name="fio-${prefix}-${idx}"
    echo -n "Waiting for $name... "
    oc wait vm/$name -n $NS --for=jsonpath='{.status.printableStatus}'=Running --timeout=600s 2>/dev/null
  done
done

echo ""
echo "=== Waiting 60s for VMs to fully boot ==="
sleep 60

echo ""
echo "=== VM IPs ==="
for prefix in san nas; do
  for idx in $(seq 1 6); do
    name="fio-${prefix}-${idx}"
    ip=$(oc get vmi $name -n $NS -o jsonpath='{.status.interfaces[0].ipAddress}' 2>/dev/null)
    node=$(oc get vmi $name -n $NS -o jsonpath='{.status.nodeName}' 2>/dev/null)
    echo "$name: IP=$ip  Node=$node"
  done
done

echo ""
echo "=== All VMs created ==="
