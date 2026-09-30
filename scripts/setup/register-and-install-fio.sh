#!/bin/bash
NS=utubo-test
SSH_OPTS="-o StrictHostKeyChecking=no -o PreferredAuthentications=password -o ConnectTimeout=10"

for prefix in san nas; do
  for idx in $(seq 1 6); do
    name="fio-${prefix}-${idx}"
    ip=$(oc get vmi "$name" -n $NS -o jsonpath="{.status.interfaces[0].ipAddress}" 2>/dev/null)
    echo "=== $name ($ip) ==="

    # Check if fio already installed
    if sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$ip "which fio" 2>/dev/null | grep -q fio; then
      echo "  fio already installed, skipping"
      continue
    fi

    # Register
    echo "  Registering..."
    sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$ip \
      "sudo subscription-manager register --org=<ORG_ID> --activationkey=<ACTIVATION_KEY> 2>&1 | tail -2"

    # Install fio
    echo "  Installing fio..."
    sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$ip \
      "sudo dnf install -y fio 2>&1 | tail -3"

    # Verify
    fio_path=$(sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$ip "which fio" 2>/dev/null)
    echo "  fio: $fio_path"
    echo ""
  done
done

echo "=== All done ==="
