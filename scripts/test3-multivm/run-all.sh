#!/bin/bash
# 検証3 LFSR re-run: 3VM/6VM × SAN/NAS
cd /root/fio-ontap
NS=utubo-test
SSH_OPTS="-o StrictHostKeyChecking=no -o PreferredAuthentications=password -o ConnectTimeout=10"
FIO="/usr/bin/fio"
RUNTIME=120
RAMP_TIME=10
SIZE="80G"
FILENAME="/myvol/testfile"
ITERATIONS=3
IODEPTHS="1 4 16 64"
PATTERNS="randread randwrite"
NODES=("wk-01.cluster.example.com" "wk-02.cluster.example.com" "wk-03.cluster.example.com")

echo "============================================"
echo "=== 検証3 LFSR re-run ==="
echo "=== $(date) ==="
echo "============================================"

drop_caches_all() {
  for node in "${NODES[@]}"; do
    oc debug node/$node --quiet -- chroot /host sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches' 2>/dev/null &
  done
  wait
  sleep 2
}

start_vms_and_wait() {
  local storage=$1
  local count=$2
  echo "Starting $count ${storage} VMs..."
  for idx in $(seq 1 $count); do
    oc patch vm "fio-${storage}-${idx}" -n $NS --type merge -p '{"spec":{"runStrategy":"Always"}}' 2>/dev/null
  done

  # Wait for Running phase
  for attempt in $(seq 1 60); do
    local running=0
    for idx in $(seq 1 $count); do
      local phase=$(oc get vmi "fio-${storage}-${idx}" -n $NS -o jsonpath='{.status.phase}' 2>/dev/null)
      [ "$phase" = "Running" ] && running=$((running + 1))
    done
    if [ $running -ge $count ]; then
      echo "  All $count VMs running"
      break
    fi
    echo "  $running/$count running... (attempt $attempt)"
    sleep 10
  done

  # Wait for all VMs to have IPs
  echo "  Waiting for IP addresses..."
  for attempt in $(seq 1 30); do
    local got_ips=0
    for idx in $(seq 1 $count); do
      local ip=$(oc get vmi "fio-${storage}-${idx}" -n $NS -o jsonpath='{.status.interfaces[0].ipAddress}' 2>/dev/null)
      [ -n "$ip" ] && got_ips=$((got_ips + 1))
    done
    if [ $got_ips -ge $count ]; then
      echo "  All $count VMs have IPs"
      break
    fi
    echo "  $got_ips/$count have IPs... (attempt $attempt)"
    sleep 10
  done

  # Wait for SSH to be ready
  echo "  Waiting for SSH..."
  sleep 20
  for idx in $(seq 1 $count); do
    local ip=$(oc get vmi "fio-${storage}-${idx}" -n $NS -o jsonpath='{.status.interfaces[0].ipAddress}' 2>/dev/null)
    for try in $(seq 1 10); do
      if sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$ip "echo OK" >/dev/null 2>&1; then
        echo "  fio-${storage}-${idx} ($ip) SSH ready"
        break
      fi
      sleep 5
    done
  done
}

stop_vms() {
  local storage=$1
  local count=$2
  echo "Stopping $count ${storage} VMs..."
  for idx in $(seq 1 $count); do
    oc patch vm "fio-${storage}-${idx}" -n $NS --type merge -p '{"spec":{"runStrategy":"Halted"}}' 2>/dev/null
  done
  for attempt in $(seq 1 30); do
    local still_running=0
    for idx in $(seq 1 $count); do
      local phase=$(oc get vmi "fio-${storage}-${idx}" -n $NS -o jsonpath='{.status.phase}' 2>/dev/null)
      [ -n "$phase" ] && still_running=$((still_running + 1))
    done
    if [ $still_running -eq 0 ]; then
      echo "  All VMs stopped"
      break
    fi
    sleep 5
  done
}

ensure_san_mount() {
  local ip=$1
  local mount_info=$(sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$ip "df /myvol 2>/dev/null | tail -1" 2>/dev/null)
  if echo "$mount_info" | grep -q vdb; then
    echo "    vdb OK"
  else
    sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$ip "sudo mkdir -p /myvol && sudo mount /dev/vdb /myvol" 2>/dev/null
    mount_info=$(sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$ip "df /myvol 2>/dev/null | tail -1" 2>/dev/null)
    if echo "$mount_info" | grep -q vdb; then
      echo "    vdb mounted"
    else
      echo "    WARNING: vdb mount FAILED"
    fi
  fi
}

run_and_collect() {
  local storage=$1
  local vm_count=$2
  local outdir="/root/fio-ontap/test3-lfsr-${storage}-${vm_count}vm"
  mkdir -p "$outdir"

  # Get IPs and ensure mounts
  local ips=()
  for idx in $(seq 1 $vm_count); do
    local ip=$(oc get vmi "fio-${storage}-${idx}" -n $NS -o jsonpath='{.status.interfaces[0].ipAddress}' 2>/dev/null)
    ips+=("$ip")
    echo "  VM$idx: $ip"
    if [ "$storage" = "san" ]; then
      ensure_san_mount "$ip"
    fi
  done

  # Verify testfiles
  for i in $(seq 0 $((vm_count - 1))); do
    local ip=${ips[$i]}
    local tf=$(sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$ip "ls -lh $FILENAME 2>/dev/null" 2>/dev/null)
    echo "  VM$((i+1)) testfile: $tf"
  done

  local total=$((2 * 4 * ITERATIONS))
  local count=0

  for iter in $(seq 1 $ITERATIONS); do
    echo "--- Iteration $iter / $ITERATIONS ---"
    for rw in $PATTERNS; do
      for depth in $IODEPTHS; do
        count=$((count + 1))
        echo ""
        echo "=== [$count/$total] ${vm_count}VM ${storage} iter=$iter rw=$rw iodepth=$depth === $(date +%H:%M:%S)"
        drop_caches_all

        local pids=()
        for i in $(seq 0 $((vm_count - 1))); do
          local ip=${ips[$i]}
          local vm_idx=$((i + 1))
          sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$ip \
            "sudo $FIO --name=test --ioengine=libaio --direct=1 --bs=4k \
              --rw=$rw --size=$SIZE --numjobs=1 --iodepth=$depth \
              --runtime=$RUNTIME --time_based --ramp_time=$RAMP_TIME \
              --startdelay=5 --filename=$FILENAME \
              --random_generator=lfsr \
              --output-format=json" > "$outdir/fio-vm${vm_idx}-iodepth${depth}-${rw}-iter${iter}.json" 2>/dev/null &
          pids+=($!)
        done
        for pid in "${pids[@]}"; do wait $pid; done

        local total_iops=0
        local rw_key="read"; [ "$rw" = "randwrite" ] && rw_key="write"
        for vm_idx in $(seq 1 $vm_count); do
          local f="$outdir/fio-vm${vm_idx}-iodepth${depth}-${rw}-iter${iter}.json"
          local iops=$(python3 -c "import json; d=json.load(open('$f')); print(int(d['jobs'][0]['${rw_key}']['iops']))" 2>/dev/null || echo 0)
          total_iops=$((total_iops + iops))
        done
        echo "  Total IOPS: $total_iops"
      done
    done
  done
}

# VMs are already running from previous attempt
echo ""
echo "###################################"
echo "### SAN Tests ###"
echo "###################################"

# Check if VMs already running
SAN_RUNNING=$(oc get vmi -n $NS -l kubevirt.io/domain=fio-san-1 -o jsonpath='{.items[0].status.phase}' 2>/dev/null)
if [ "$SAN_RUNNING" != "Running" ]; then
  start_vms_and_wait "san" 6
else
  echo "SAN VMs already running, waiting for SSH..."
  sleep 10
fi

echo ""
echo "### SAN 3VM ###"
run_and_collect "san" 3
echo ""
echo "### SAN 6VM ###"
run_and_collect "san" 6
stop_vms "san" 6

echo ""
echo "###################################"
echo "### NAS Tests ###"
echo "###################################"
start_vms_and_wait "nas" 6
echo ""
echo "### NAS 3VM ###"
run_and_collect "nas" 3
echo ""
echo "### NAS 6VM ###"
run_and_collect "nas" 6
stop_vms "nas" 6

echo ""
echo "============================================"
echo "=== 検証3 LFSR complete at $(date) ==="
echo "============================================"
