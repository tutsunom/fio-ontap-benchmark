import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.size'] = 11
plt.rcParams['figure.dpi'] = 150

iodepths = [1, 2, 4, 8, 16, 32, 64, 128]

# iter2-3 averages (with drop_caches)
san_randread_iops = [2926, 7039, 13012, 20174, 36928, 60598, 82667, 80860]
san_randread_lat  = [344.1, 283.3, 306.0, 395.2, 432.1, 527.0, 773.1, 1591.1]

nas_randread_iops = [2211, 5231, 9458, 14662, 23909, 36698, 41880, 41990]
nas_randread_lat  = [453.9, 380.8, 421.4, 544.3, 667.9, 870.8, 1527.0, 3047.0]

san_randwrite_iops = [2152, 4109, 9211, 16093, 26642, 30155, 36810, 43911]
san_randwrite_lat  = [462.4, 487.4, 432.5, 495.7, 599.2, 1110.4, 1795.0, 2913.8]

nas_randwrite_iops = [1969, 3560, 6895, 12481, 21151, 29879, 34672, 34779]
nas_randwrite_lat  = [505.4, 559.6, 578.4, 639.4, 755.0, 1069.6, 1844.5, 3678.9]

SAN_COLOR = '#2196F3'
NAS_COLOR = '#FF9800'

# Convert latency to ms
san_rr_lat_ms = [v / 1000 for v in san_randread_lat]
nas_rr_lat_ms = [v / 1000 for v in nas_randread_lat]
san_rw_lat_ms = [v / 1000 for v in san_randwrite_lat]
nas_rw_lat_ms = [v / 1000 for v in nas_randwrite_lat]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

for ax, title, san_iops, nas_iops, san_lat, nas_lat in [
    (ax1, 'Random Read', san_randread_iops, nas_randread_iops, san_rr_lat_ms, nas_rr_lat_ms),
    (ax2, 'Random Write', san_randwrite_iops, nas_randwrite_iops, san_rw_lat_ms, nas_rw_lat_ms),
]:
    ax.plot(san_iops, san_lat, 'o-', color=SAN_COLOR, label='ontap-san', linewidth=2, markersize=7)
    ax.plot(nas_iops, nas_lat, 's-', color=NAS_COLOR, label='ontap-nas', linewidth=2, markersize=7)

    for i, iod in enumerate(iodepths):
        ax.annotate(str(iod), (san_iops[i], san_lat[i]),
                    textcoords='offset points', xytext=(8, 4), fontsize=8, color=SAN_COLOR)
        ax.annotate(str(iod), (nas_iops[i], nas_lat[i]),
                    textcoords='offset points', xytext=(8, -10), fontsize=8, color=NAS_COLOR)

    ax.set_title(f'{title} — IOPS vs Latency')
    ax.set_xlabel('IOPS')
    ax.set_ylabel('Latency (ms)')
    ax.legend()
    ax.grid(alpha=0.3)

fig.suptitle('4k Random IO — Hockey Stick Curve (iodepth 1-128, lower-right = better)',
             fontsize=12, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.94])

outdir = './output'
fig.savefig(f'{outdir}/fio-chart-hockey-stick.png', bbox_inches='tight')
plt.close(fig)
print('Created fio-chart-hockey-stick.png')
