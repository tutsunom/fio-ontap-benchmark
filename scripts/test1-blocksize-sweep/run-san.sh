#!/bin/bash
# 検証1 SAN 再測定 (3 iter, ループ順変更): for bs → for rw → for iter
exec > /root/fio-ontap/test1-san-redo4.log 2>&1

NS=utubo-test
VM=rhel10-ontap-san
SAN_IP=192.168.x.55
SSH_OPTS="-o StrictHostKeyChecking=no -o PreferredAuthentications=password -o ConnectTimeout=10"
FIO="/usr/local/bin/fio"
RUNTIME=120
RAMP=10
SIZE=450G
FILENAME=/myvol/testfile
BLOCK_SIZES="4k 8k 16k 32k 64k 128k 256k"
ITERATIONS=3

NODE=$(oc get vmi $VM -n $NS -o jsonpath='{.status.nodeName}' 2>/dev/null)
echo "VM node: $NODE"

# Verify mount
sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$SAN_IP "sudo mount /dev/vdb /myvol 2>/dev/null; df -h /myvol; ls -lh $FILENAME" 2>/dev/null

echo "============================================"
echo "=== 検証1 SAN 再測定 (ループ順変更) ==="
echo "=== $(date) ==="
echo "============================================"

OUTDIR="/root/fio-ontap/test1-san-redo4"
mkdir -p "$OUTDIR"

TOTAL=$((7 * 4 * ITERATIONS))
COUNT=0

for bs in $BLOCK_SIZES; do
    for rw in randread randwrite read write; do
        for iter in $(seq 1 $ITERATIONS); do
            COUNT=$((COUNT + 1))
            echo ""
            echo "=== [$COUNT/$TOTAL] bs=$bs rw=$rw iter=$iter === $(date +%H:%M:%S)"

            oc debug node/$NODE --quiet -- chroot /host sh -c "sync; echo 3 > /proc/sys/vm/drop_caches" 2>/dev/null
            sleep 2

            LFSR_OPT=""
            if [ "$rw" = "randread" ] || [ "$rw" = "randwrite" ]; then
                LFSR_OPT="--random_generator=lfsr"
            fi

            sshpass -p <PASSWORD> ssh $SSH_OPTS cloud-user@$SAN_IP \
                "sudo $FIO \
                    --name=test \
                    --ioengine=libaio \
                    --direct=1 \
                    --bs=${bs} \
                    --rw=${rw} \
                    --iodepth=1 \
                    --numjobs=1 \
                    --size=${SIZE} \
                    --runtime=${RUNTIME} \
                    --ramp_time=${RAMP} \
                    --startdelay=5 \
                    --time_based \
                    --filename=${FILENAME} \
                    ${LFSR_OPT} \
                    --output-format=json" > "$OUTDIR/fio-${bs}-${rw}-iter${iter}.json" 2>/dev/null

            if [ "$rw" = "read" ] || [ "$rw" = "write" ]; then
                rw_key=$rw
            elif [ "$rw" = "randread" ]; then
                rw_key="read"
            else
                rw_key="write"
            fi

            python3 -c "
import json
with open('$OUTDIR/fio-${bs}-${rw}-iter${iter}.json') as f:
    d = json.load(f)
j = d['jobs'][0]['${rw_key}']
print('  IOPS: %.0f  Lat: %.1f us  BW: %.1f MiB/s' % (j['iops'], j['lat_ns']['mean']/1000, j['bw']/1024))
" 2>/dev/null
        done

        # パターンごとの iter2-3 平均を即表示
        python3 -c "
import json, os
outdir = '/root/fio-ontap/test1-san-redo4'
rw = '${rw}'
bs = '${bs}'
key = 'read' if rw in ['randread', 'read'] else 'write'
iops_list = []
for i in [2, 3]:
    fp = '%s/fio-%s-%s-iter%d.json' % (outdir, bs, rw, i)
    if os.path.exists(fp):
        with open(fp) as f:
            data = json.load(f)
        iops_list.append(data['jobs'][0][key]['iops'])
if iops_list:
    print('  >> iter2-3 avg: %.0f IOPS' % (sum(iops_list)/len(iops_list)))
" 2>/dev/null
    done

    # BS ごとのサマリ
    echo ""
    echo "=== BS=$bs サマリ (iter2-3 avg) ==="
    python3 -c "
import json, os
outdir = '/root/fio-ontap/test1-san-redo4'
bs = '${bs}'
for rw in ['randread', 'randwrite', 'read', 'write']:
    key = 'read' if rw in ['randread', 'read'] else 'write'
    iops_list = []
    lat_list = []
    bw_list = []
    for i in [2, 3]:
        fp = '%s/fio-%s-%s-iter%d.json' % (outdir, bs, rw, i)
        if os.path.exists(fp):
            with open(fp) as f:
                data = json.load(f)
            j = data['jobs'][0][key]
            iops_list.append(j['iops'])
            lat_list.append(j['lat_ns']['mean'] / 1000)
            bw_list.append(j['bw'] / 1024)
    if iops_list:
        print('  %10s: %6.0f IOPS  %7.1f us  %7.1f MiB/s' % (rw, sum(iops_list)/len(iops_list), sum(lat_list)/len(lat_list), sum(bw_list)/len(bw_list)))
" 2>/dev/null
done

echo ""
echo "============================================"
echo "=== 完了: $(date) ==="
echo "============================================"

# 全体サマリ + 検証2比較
echo ""
echo "=== 全体 iter2-3 平均サマリ ==="
python3 << 'PYEOF'
import json, os
outdir = "/root/fio-ontap/test1-san-redo4"
bss = ["4k", "8k", "16k", "32k", "64k", "128k", "256k"]
test2 = {"randread": 4394, "randwrite": 2240}
for rw in ["randread", "randwrite", "read", "write"]:
    key = "read" if rw in ["randread", "read"] else "write"
    print("\n%s:" % rw)
    print("%6s  %8s  %10s  %10s" % ("BS", "IOPS", "Lat(us)", "BW(MiB/s)"))
    print("-" * 42)
    for bs in bss:
        iops_list = []
        lat_list = []
        bw_list = []
        for i in [2, 3]:
            fp = "%s/fio-%s-%s-iter%d.json" % (outdir, bs, rw, i)
            if os.path.exists(fp):
                with open(fp) as f:
                    data = json.load(f)
                j = data["jobs"][0][key]
                iops_list.append(j["iops"])
                lat_list.append(j["lat_ns"]["mean"] / 1000)
                bw_list.append(j["bw"] / 1024)
        if iops_list:
            print("%6s  %8.0f  %10.1f  %10.1f" % (bs, sum(iops_list)/len(iops_list), sum(lat_list)/len(lat_list), sum(bw_list)/len(bw_list)))
    if rw in test2:
        fp4k = "%s/fio-4k-%s-iter2.json" % (outdir, rw)
        fp4k3 = "%s/fio-4k-%s-iter3.json" % (outdir, rw)
        il = []
        for fp in [fp4k, fp4k3]:
            if os.path.exists(fp):
                with open(fp) as f:
                    data = json.load(f)
                il.append(data["jobs"][0][key]["iops"])
        if il:
            avg = sum(il)/len(il)
            print("\n  4k vs 検証2: %.0f / %d = %.2fx" % (avg, test2[rw], avg/test2[rw]))
PYEOF
