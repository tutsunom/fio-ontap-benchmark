#!/bin/bash
# 検証3用 VM セットアップ（datadisk format, mount, fio確認）

NS="utubo-test"
SSH_OPTS="-o StrictHostKeyChecking=no -o PreferredAuthentications=password -o ConnectTimeout=10"

setup_vm() {
  local name=$1
  local ip=$2

  echo "=== Setting up $name ($ip) ==="

  # Wait for SSH
  for retry in $(seq 1 30); do
    if sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$ip "echo ok" 2>/dev/null; then
      break
    fi
    echo "  Waiting for SSH ($retry/30)..."
    sleep 10
  done

  # Check if datadisk needs formatting
  local fstype=$(sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$ip "lsblk -no FSTYPE /dev/vdb" 2>/dev/null)
  if [ -z "$fstype" ]; then
    echo "  Formatting /dev/vdb..."
    sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$ip "sudo mkfs.xfs /dev/vdb" 2>/dev/null
  else
    echo "  /dev/vdb already formatted ($fstype)"
  fi

  # Mount
  sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$ip "
    sudo mkdir -p /myvol
    if ! mountpoint -q /myvol; then
      sudo mount /dev/vdb /myvol
    fi
    grep -q '/myvol' /etc/fstab || echo '/dev/vdb /myvol xfs defaults 0 0' | sudo tee -a /etc/fstab
  " 2>/dev/null

  # Check fio
  local fio_path=$(sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$ip "which fio 2>/dev/null" 2>/dev/null)
  if [ -z "$fio_path" ]; then
    echo "  Installing fio..."
    sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$ip "sudo dnf install -y fio" 2>/dev/null
  else
    echo "  fio already installed ($fio_path)"
  fi

  # Verify
  local df_out=$(sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$ip "df -h /myvol | tail -1" 2>/dev/null)
  echo "  Disk: $df_out"
  echo "  Done: $name"
  echo ""
}

echo "=== Setting up 検証3 VMs ==="

for prefix in san nas; do
  for idx in $(seq 1 6); do
    name="fio-${prefix}-${idx}"
    ip=$(oc get vmi $name -n $NS -o jsonpath='{.status.interfaces[0].ipAddress}' 2>/dev/null)
    if [ -n "$ip" ]; then
      setup_vm "$name" "$ip"
    else
      echo "WARN: $name has no IP, skipping"
    fi
  done
done

echo "=== All VMs set up ==="
