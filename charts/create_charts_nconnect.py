import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

plt.rcParams['font.size'] = 11
plt.rcParams['figure.dpi'] = 150

# === Test 1 Data: Block Size Sweep (LFSR, iter2-3 average, iodepth=1) ===
bs_labels = ['4k', '8k', '16k', '32k', '64k', '128k', '256k']
x = np.arange(len(bs_labels))

san = {
    'randread':  {'iops': [4370, 4297, 3046, 1929, 1412, 1265, 913],
                  'lat':  [227.6, 233.2, 328.4, 516.7, 705.8, 788.5, 1093.5]},
    'randwrite': {'iops': [2147, 1762, 1657, 1524, 1325, 919, 672],
                  'lat':  [463.5, 565.3, 601.2, 653.8, 752.3, 1085.0, 1485.4]},
    'read':      {'bw': [18.8, 34.1, 48.3, 82.5, 142.5, 239.7, 398.2],
                  'lat': [207.1, 228.0, 321.6, 377.3, 436.7, 519.7, 626.2]},
    'write':     {'bw': [8.3, 14.5, 27.6, 50.6, 89.1, 118.4, 177.0],
                  'lat': [467.7, 535.0, 563.2, 615.7, 699.3, 1053.3, 1410.2]},
}

nas = {
    'randread':  {'iops': [1737, 1752, 1499, 1375, 1141, 987, 655],
                  'lat':  [573.3, 571.1, 665.0, 724.9, 874.0, 1010.8, 1523.6]},
    'randwrite': {'iops': [1623, 1608, 1537, 1156, 987, 860, 670],
                  'lat':  [613.8, 620.5, 648.6, 862.4, 1011.0, 1160.6, 1490.0]},
    'read':      {'bw': [10.1, 19.6, 36.1, 58.1, 106.5, 177.6, 259.2],
                  'lat': [384.0, 396.4, 430.8, 535.8, 585.0, 702.1, 962.6]},
    'write':     {'bw': [7.8, 15.2, 27.2, 38.7, 65.0, 111.8, 179.7],
                  'lat': [499.7, 512.5, 572.2, 804.5, 959.7, 1116.0, 1389.0]},
}

# === Test 2 Data: iodepth Sweep (LFSR, 4k random, iter2-3 average) ===
depths = [1, 2, 4, 8, 16, 32, 64, 128]
depth_labels = ['1', '2', '4', '8', '16', '32', '64', '128']

san_depth = {
    'randread':  {'iops': [4394, 10275, 21302, 38704, 65668, 106533, 136682, 135911],
                  'lat':  [226.6, 193.8, 186.9, 206.0, 243.2, 299.9, 467.9, 941.1]},
    'randwrite': {'iops': [2240, 4628, 9513, 16387, 26607, 36975, 42132, 42771],
                  'lat':  [444.3, 430.5, 419.0, 487.0, 600.2, 864.6, 1518.6, 2992.6]},
}

nas_depth = {
    'randread':  {'iops': [1804, 4072, 8190, 15606, 25724, 58893, 108739, 121113],
                  'lat':  [552.2, 489.7, 487.1, 511.5, 621.0, 542.5, 587.8, 1056.1]},
    'randwrite': {'iops': [1970, 3874, 7569, 13556, 23655, 34686, 41759, 42824],
                  'lat':  [505.3, 514.4, 526.8, 588.7, 675.1, 921.2, 1531.7, 2988.5]},
}

# NAS nconnect=1 (LFSR, iter2-3 average)
nas_nc1_depth = {
    'randread':  {'iops': [1796, 4152, 8081, 15152, 24247, 36535, 50807, 48758],
                  'lat':  [555.0, 480.3, 493.4, 526.7, 658.5, 874.3, 1259.2, 2623.8]},
    'randwrite': {'iops': [1986, 3545, 6765, 12301, 20756, 30471, 36840, 37253],
                  'lat':  [501.3, 562.3, 589.3, 648.3, 769.3, 1048.3, 1736.3, 3433.3]},
}

# === Test 3 Data: Multi-VM (LFSR, 4k random, iter2-3 average) ===
test3_depths = [1, 4, 16, 64]
test3_labels = ['1', '4', '16', '64']

san_3vm = {
    'randread':  {'iops': [7460, 30888, 83059, 102983],
                  'lat':  [400.3, 387.5, 577.9, 1893.9]},
    'randwrite': {'iops': [6649, 24010, 43230, 50355],
                  'lat':  [449.9, 500.6, 1111.5, 3847.7]},
}
san_6vm = {
    'randread':  {'iops': [14869, 61645, 162501, 207877],
                  'lat':  [401.6, 388.2, 593.1, 1859.2]},
    'randwrite': {'iops': [13986, 46829, 85962, 99924],
                  'lat':  [427.2, 512.0, 1118.4, 3864.7]},
}
nas_3vm = {
    'randread':  {'iops': [5584, 23079, 71570, 108122],
                  'lat':  [543.7, 527.5, 669.6, 1829.3]},
    'randwrite': {'iops': [5395, 20065, 50608, 70838],
                  'lat':  [609.0, 645.1, 956.7, 3150.7]},
}
nas_6vm = {
    'randread':  {'iops': [10707, 41563, 92993, 115976],
                  'lat':  [572.6, 591.5, 1033.4, 3329.9]},
    'randwrite': {'iops': [10238, 33754, 65814, 73809],
                  'lat':  [640.7, 756.8, 1474.8, 5372.4]},
}

SAN_COLOR = '#2563EB'
NAS_COLOR = '#DC2626'
NAS_NC1_COLOR = '#AAAAAA'
BAR_WIDTH = 0.35

outdir = './output'

# =====================================================
# Chart 1: Random IO — IOPS (Bar chart, 2 panels)
# =====================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

for ax, rw, title in [(ax1, 'randread', 'Random Read'), (ax2, 'randwrite', 'Random Write')]:
    b1 = ax.bar(x - BAR_WIDTH/2, san[rw]['iops'], BAR_WIDTH,
                label='ontap-san (iSCSI)', color=SAN_COLOR)
    b2 = ax.bar(x + BAR_WIDTH/2, nas[rw]['iops'], BAR_WIDTH,
                label='ontap-nas (NFS, nconnect=8)', color=NAS_COLOR)
    ax.set_title(f'{title} — IOPS', fontsize=13, fontweight='bold')
    ax.set_xlabel('Block Size')
    ax.set_ylabel('IOPS')
    ax.set_xticks(x)
    ax.set_xticklabels(bs_labels)
    ax.legend(fontsize=9)
    ax.grid(axis='y', alpha=0.3)

    for bar_group in [b1, b2]:
        for bar in bar_group:
            h = bar.get_height()
            ax.annotate(f'{h:,.0f}', xy=(bar.get_x() + bar.get_width()/2, h),
                        xytext=(0, 3), textcoords='offset points',
                        ha='center', va='bottom', fontsize=7)

fig.suptitle('IOPS: ontap-san vs ontap-nas (nconnect=8) — iodepth=1, LFSR', fontsize=14, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(f'{outdir}/fio-chart-iops.png', bbox_inches='tight')
plt.close(fig)
print('Created fio-chart-iops.png')

# =====================================================
# Chart 2: Sequential IO — Throughput (Bar chart, 2 panels)
# =====================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

for ax, rw, title in [(ax1, 'read', 'Sequential Read'), (ax2, 'write', 'Sequential Write')]:
    b1 = ax.bar(x - BAR_WIDTH/2, san[rw]['bw'], BAR_WIDTH,
                label='ontap-san (iSCSI)', color=SAN_COLOR)
    b2 = ax.bar(x + BAR_WIDTH/2, nas[rw]['bw'], BAR_WIDTH,
                label='ontap-nas (NFS, nconnect=8)', color=NAS_COLOR)
    ax.set_title(f'{title} — Throughput (MiB/s)', fontsize=13, fontweight='bold')
    ax.set_xlabel('Block Size')
    ax.set_ylabel('MiB/s')
    ax.set_xticks(x)
    ax.set_xticklabels(bs_labels)
    ax.legend(fontsize=9)
    ax.grid(axis='y', alpha=0.3)

    for bar_group in [b1, b2]:
        for bar in bar_group:
            h = bar.get_height()
            ax.annotate(f'{h:,.0f}', xy=(bar.get_x() + bar.get_width()/2, h),
                        xytext=(0, 3), textcoords='offset points',
                        ha='center', va='bottom', fontsize=7)

fig.suptitle('Throughput: ontap-san vs ontap-nas (nconnect=8) — iodepth=1, LFSR', fontsize=14, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(f'{outdir}/fio-chart-bandwidth.png', bbox_inches='tight')
plt.close(fig)
print('Created fio-chart-bandwidth.png')

# =====================================================
# Chart 3: Random IO — Latency (Line chart, 2 panels)
# =====================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

for ax, rw, title in [(ax1, 'randread', 'Random Read'), (ax2, 'randwrite', 'Random Write')]:
    san_ms = [v / 1000 for v in san[rw]['lat']]
    nas_ms = [v / 1000 for v in nas[rw]['lat']]
    ax.plot(bs_labels, san_ms, 'o-', color=SAN_COLOR, label='ontap-san (iSCSI)', linewidth=2, markersize=7)
    ax.plot(bs_labels, nas_ms, 's-', color=NAS_COLOR, label='ontap-nas (NFS, nconnect=8)', linewidth=2, markersize=7)
    ax.set_title(f'{title} — Avg Latency', fontsize=13, fontweight='bold')
    ax.set_xlabel('Block Size')
    ax.set_ylabel('Latency (ms)')
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)

fig.suptitle('Average Latency: ontap-san vs ontap-nas (nconnect=8, ms) — Random IO, iodepth=1, LFSR',
             fontsize=13, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(f'{outdir}/fio-chart-latency.png', bbox_inches='tight')
plt.close(fig)
print('Created fio-chart-latency.png')

# =====================================================
# Chart 4: iodepth — IOPS comparison (Line chart, 2 panels)
# =====================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

for ax, rw, title in [(ax1, 'randread', '4k Random Read'), (ax2, 'randwrite', '4k Random Write')]:
    ax.plot(depth_labels, san_depth[rw]['iops'], 'o-', color=SAN_COLOR,
            linewidth=2.5, markersize=8, label='ontap-san (iSCSI)')
    ax.plot(depth_labels, nas_depth[rw]['iops'], 's-', color=NAS_COLOR,
            linewidth=2.5, markersize=8, label='ontap-nas (NFS, nconnect=8)')
    ax.plot(depth_labels, nas_nc1_depth[rw]['iops'], 'x--', color=NAS_NC1_COLOR,
            linewidth=1.5, markersize=7, label='ontap-nas (NFS, nconnect=1)')

    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('iodepth')
    ax.set_ylabel('IOPS')
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f'{v/1000:,.0f}k'))
    ax.legend(fontsize=9, loc='upper left')
    ax.grid(alpha=0.3)

    for i, d in enumerate(depths):
        ax.annotate(f'{san_depth[rw]["iops"][i]/1000:.0f}k',
                    (depth_labels[i], san_depth[rw]['iops'][i]),
                    textcoords='offset points', xytext=(8, -12), fontsize=7.5, color=SAN_COLOR)
        ax.annotate(f'{nas_depth[rw]["iops"][i]/1000:.0f}k',
                    (depth_labels[i], nas_depth[rw]['iops'][i]),
                    textcoords='offset points', xytext=(8, 6), fontsize=7.5, color=NAS_COLOR)

fig.suptitle('IOPS by iodepth — 4k Random I/O (LFSR)', fontsize=15, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(f'{outdir}/fio-chart-iodepth-iops.png', bbox_inches='tight')
plt.close(fig)
print('Created fio-chart-iodepth-iops.png')

# =====================================================
# Chart 5: Hockey Stick Curve (IOPS vs Latency, 2 panels)
# =====================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

for ax, rw, title in [(ax1, 'randread', '4k Random Read'), (ax2, 'randwrite', '4k Random Write')]:
    san_lat_ms = [v / 1000 for v in san_depth[rw]['lat']]
    nas_lat_ms = [v / 1000 for v in nas_depth[rw]['lat']]
    nas_nc1_lat_ms = [v / 1000 for v in nas_nc1_depth[rw]['lat']]

    ax.plot(san_depth[rw]['iops'], san_lat_ms,
            'o-', color=SAN_COLOR, linewidth=2.5, markersize=9,
            label='ontap-san (iSCSI)', zorder=5)
    ax.plot(nas_depth[rw]['iops'], nas_lat_ms,
            's-', color=NAS_COLOR, linewidth=2.5, markersize=9,
            label='ontap-nas (NFS, nconnect=8)', zorder=5)
    ax.plot(nas_nc1_depth[rw]['iops'], nas_nc1_lat_ms,
            'x--', color=NAS_NC1_COLOR, linewidth=1.5, markersize=7,
            label='ontap-nas (NFS, nconnect=1)', zorder=3)

    for i, d in enumerate(depths):
        ax.annotate(f'{d}', (san_depth[rw]['iops'][i], san_lat_ms[i]),
                    textcoords='offset points', xytext=(10, -5),
                    fontsize=8.5, color=SAN_COLOR, fontweight='bold')
        ax.annotate(f'{d}', (nas_depth[rw]['iops'][i], nas_lat_ms[i]),
                    textcoords='offset points', xytext=(-5, 10),
                    fontsize=8.5, color=NAS_COLOR, fontweight='bold')

    ax.set_title(title, fontsize=14, fontweight='bold', pad=12)
    ax.set_xlabel('IOPS', fontsize=12)
    ax.set_ylabel('Average Latency (ms)', fontsize=12)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f'{v/1000:,.0f}k'))
    ax.legend(fontsize=10, loc='upper left')
    ax.grid(True, alpha=0.3)

fig.suptitle('IOPS vs Latency — Hockey Stick Curve (LFSR)\nontap-san (iSCSI) vs ontap-nas (NFS)',
             fontsize=15, fontweight='bold', y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(f'{outdir}/fio-chart-hockey-stick.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('Created fio-chart-hockey-stick.png')

# =====================================================
# Chart 6: Multi-VM Scalability (3VM vs 6VM, 4 panels)
# =====================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
t3x = np.arange(len(test3_labels))
bw = 0.35

for row, rw, rw_title in [(0, 'randread', 'Random Read'), (1, 'randwrite', 'Random Write')]:
    for col, (s_data, n_data, vm_label) in enumerate([
        (san_3vm, nas_3vm, '3VM'),
        (san_6vm, nas_6vm, '6VM'),
    ]):
        ax = axes[row][col]
        b1 = ax.bar(t3x - bw/2, s_data[rw]['iops'], bw,
                     label='ontap-san (iSCSI)', color=SAN_COLOR)
        b2 = ax.bar(t3x + bw/2, n_data[rw]['iops'], bw,
                     label='ontap-nas (NFS, nc8)', color=NAS_COLOR)
        ax.set_title(f'{rw_title} — {vm_label}', fontsize=13, fontweight='bold')
        ax.set_xlabel('iodepth')
        ax.set_ylabel('Total IOPS')
        ax.set_xticks(t3x)
        ax.set_xticklabels(test3_labels)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f'{v/1000:,.0f}k'))
        ax.legend(fontsize=8)
        ax.grid(axis='y', alpha=0.3)

        for bar_group in [b1, b2]:
            for bar in bar_group:
                h = bar.get_height()
                ax.annotate(f'{h/1000:.0f}k', xy=(bar.get_x() + bar.get_width()/2, h),
                            xytext=(0, 3), textcoords='offset points',
                            ha='center', va='bottom', fontsize=7)

fig.suptitle('Multi-VM Parallel I/O — ontap-san vs ontap-nas (LFSR)', fontsize=15, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(f'{outdir}/fio-chart-multivm.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('Created fio-chart-multivm.png')

# =====================================================
# Chart 7: Multi-VM Scalability — 3VM→6VM scale factor
# =====================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

for ax, rw, title in [(ax1, 'randread', 'Random Read'), (ax2, 'randwrite', 'Random Write')]:
    san_scale = [s6/s3 for s3, s6 in zip(san_3vm[rw]['iops'], san_6vm[rw]['iops'])]
    nas_scale = [n6/n3 for n3, n6 in zip(nas_3vm[rw]['iops'], nas_6vm[rw]['iops'])]

    ax.plot(test3_labels, san_scale, 'o-', color=SAN_COLOR, linewidth=2.5, markersize=8,
            label='ontap-san (iSCSI)')
    ax.plot(test3_labels, nas_scale, 's-', color=NAS_COLOR, linewidth=2.5, markersize=8,
            label='ontap-nas (NFS, nc8)')
    ax.axhline(y=2.0, color='gray', linestyle='--', alpha=0.5, label='Ideal (2.0x)')

    for i in range(len(test3_labels)):
        ax.annotate(f'{san_scale[i]:.2f}x', (test3_labels[i], san_scale[i]),
                    textcoords='offset points', xytext=(8, -12), fontsize=9, color=SAN_COLOR)
        ax.annotate(f'{nas_scale[i]:.2f}x', (test3_labels[i], nas_scale[i]),
                    textcoords='offset points', xytext=(8, 8), fontsize=9, color=NAS_COLOR)

    ax.set_title(f'{title} — 3VM→6VM Scale Factor', fontsize=13, fontweight='bold')
    ax.set_xlabel('iodepth')
    ax.set_ylabel('Scale Factor (6VM / 3VM)')
    ax.set_ylim(0.5, 2.5)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)

fig.suptitle('Multi-VM Scalability: 3VM → 6VM (LFSR)', fontsize=14, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(f'{outdir}/fio-chart-multivm-scale.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('Created fio-chart-multivm-scale.png')

print('\nAll charts generated successfully.')
