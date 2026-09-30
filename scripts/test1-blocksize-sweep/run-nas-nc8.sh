#!/bin/bash
# 検証1 再取得: NAS nconnect=8 + lfsr, ブロックサイズ sweep
# - random (randread/randwrite): 4k, 8k, 16k, 32k  (lfsr あり)
# - sequential (read/write):     64k, 128k, 256k, 512k (lfsr なし)
# - 3 iterations, iter2-3 の平均を採用（iter1 はキャッシュウォームアップ）
# - 合計 48 テスト × 135 秒 ≈ 約 1 時間 48 分
cd /root/fio-ontap
NS=utubo-test
SSH_OPTS="-o StrictHostKeyChecking=no -o PreferredAuthentications=password -o ConnectTimeout=10"
RUNTIME=120
RAMP=10
SIZE="450G"
FILENAME="/myvol/testfile"
ITERATIONS=3

NAS_IP=192.168.x.56
NAS_FIO="/usr/local/bin/fio"
OUTDIR="/root/fio-ontap/test1-nc8-lfsr-nas"

RAND_BLOCK_SIZES="4k 8k 16k 32k"
SEQ_BLOCK_SIZES="64k 128k 256k 512k"

echo "============================================"
echo "=== 検証1 NAS nconnect=8 + lfsr 再取得 ==="
echo "=== $(date) ==="
echo "============================================"

# NAS VM が起動しているか確認
echo ""
echo "--- NAS VM 状態確認 ---"
NAS_STATUS=$(oc get vmi rhel10-ontap-nas -n $NS -o jsonpath='{.status.phase}' 2>/dev/null)
if [ "$NAS_STATUS" != "Running" ]; then
  echo "ERROR: NAS VM is not running (status: $NAS_STATUS)"
  echo "  virtctl start rhel10-ontap-nas -n $NS で起動して下さい"
  exit 1
fi
echo "NAS VM: Running"

NAS_NODE=$(oc get vmi rhel10-ontap-nas -n $NS -o jsonpath='{.status.nodeName}' 2>/dev/null)
echo "NAS VM on: $NAS_NODE"

# nconnect=8 が有効か確認
echo ""
echo "--- nconnect 確認 ---"
MOUNT_LINE=$(oc debug node/$NAS_NODE --quiet -- chroot /host sh -c "cat /proc/mounts | grep trident_pvc | grep nfs | head -1" 2>/dev/null)
if echo "$MOUNT_LINE" | grep -q "nconnect=8"; then
  echo "OK: nconnect=8 が有効です"
  echo "  $MOUNT_LINE" | grep -o 'nconnect=[0-9]*'
else
  echo "WARNING: nconnect=8 が検出できません"
  echo "  mount line: $MOUNT_LINE"
  echo "  続行しますか？ (y/N)"
  read -r ans
  [ "$ans" != "y" ] && exit 1
fi

# /myvol マウント確認
echo ""
echo "--- /myvol マウント確認 ---"
MYVOL=$(sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$NAS_IP "df /myvol 2>/dev/null | tail -1" 2>/dev/null)
if echo "$MYVOL" | grep -q myvol; then
  echo "OK: /myvol mounted"
else
  echo "ERROR: /myvol がマウントされていません"
  exit 1
fi

# 出力ディレクトリ作成
mkdir -p "$OUTDIR"

# テストマトリクス構築
declare -a TESTS=()

# Random patterns (with lfsr): 4k, 8k, 16k, 32k
for bs in $RAND_BLOCK_SIZES; do
  for rw in randread randwrite; do
    TESTS+=("$bs:$rw:lfsr")
  done
done

# Sequential patterns (without lfsr): 64k, 128k, 256k, 512k
for bs in $SEQ_BLOCK_SIZES; do
  for rw in read write; do
    TESTS+=("$bs:$rw:nolfsr")
  done
done

TOTAL=$((${#TESTS[@]} * ITERATIONS))
COUNT=0

echo ""
echo "=== テストマトリクス: ${#TESTS[@]} パターン × $ITERATIONS iter = $TOTAL テスト ==="
echo "=== 推定所要時間: 約 $((TOTAL * 135 / 60)) 分 ==="
echo ""

for iter in $(seq 1 $ITERATIONS); do
  echo ""
  echo "########################################"
  echo "### Iteration $iter / $ITERATIONS  $(date)"
  echo "########################################"

  for test_spec in "${TESTS[@]}"; do
    IFS=':' read -r bs rw lfsr_flag <<< "$test_spec"
    COUNT=$((COUNT + 1))
    echo ""
    echo "=== [$COUNT/$TOTAL] iter=$iter bs=$bs rw=$rw ($lfsr_flag) === $(date +%H:%M:%S)"

    # Drop caches on compute node
    oc debug node/$NAS_NODE --quiet -- chroot /host sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches' 2>/dev/null
    sleep 2

    # Build fio command
    LFSR_OPT=""
    if [ "$lfsr_flag" = "lfsr" ]; then
      LFSR_OPT="--random_generator=lfsr"
    fi

    sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$NAS_IP \
      "sudo $NAS_FIO \
        --name=test \
        --ioengine=libaio \
        --direct=1 \
        --bs=$bs \
        --rw=$rw \
        --size=$SIZE \
        --numjobs=1 \
        --iodepth=1 \
        --runtime=$RUNTIME \
        --time_based \
        --ramp_time=$RAMP \
        --startdelay=5 \
        --filename=$FILENAME \
        $LFSR_OPT \
        --output-format=json" > "$OUTDIR/fio-${bs}-${rw}-iter${iter}.json" 2>/dev/null

    # Extract and display metrics
    if [ "$rw" = "read" ] || [ "$rw" = "randread" ]; then
      KEY="read"
    else
      KEY="write"
    fi
    python3 -c "
import json, sys
try:
    with open('$OUTDIR/fio-${bs}-${rw}-iter${iter}.json') as f:
        d = json.load(f)
    j = d['jobs'][0]['$KEY']
    print('  IOPS: %.0f  Lat: %.1f us  BW: %.1f MiB/s' % (j['iops'], j['lat_ns']['mean']/1000, j['bw']/1024))
except Exception as e:
    print('  ERROR: %s' % e, file=sys.stderr)
" 2>/dev/null
  done
done

echo ""
echo "============================================"
echo "=== 完了: $(date) ==="
echo "=== 結果: $OUTDIR ==="
echo "============================================"

# サマリ出力
echo ""
echo "=== iter2-3 平均サマリ ==="
python3 -c "
import json, os, glob

outdir = '$OUTDIR'
results = {}

for f in sorted(glob.glob(os.path.join(outdir, 'fio-*-iter[23].json'))):
    basename = os.path.basename(f)
    parts = basename.replace('.json','').split('-')
    # fio-4k-randread-iter2.json -> bs=4k, rw=randread, iter=2
    bs = parts[1]
    rw = parts[2]
    key = f'{bs}-{rw}'

    try:
        with open(f) as fh:
            d = json.load(fh)
        job = d['jobs'][0]
        if 'read' in rw:
            iops = job['read']['iops']
            bw = job['read']['bw'] / 1024
        else:
            iops = job['write']['iops']
            bw = job['write']['bw'] / 1024
    except:
        continue

    if key not in results:
        results[key] = []
    results[key].append((iops, bw))

print(f\"{'Pattern':<20} {'IOPS':>10} {'BW (MiB/s)':>12}\")
print('-' * 44)
for key in sorted(results.keys()):
    vals = results[key]
    avg_iops = sum(v[0] for v in vals) / len(vals)
    avg_bw = sum(v[1] for v in vals) / len(vals)
    print(f'{key:<20} {avg_iops:>10.0f} {avg_bw:>12.1f}')
"
