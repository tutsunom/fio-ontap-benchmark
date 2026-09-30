import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.size'] = 11
plt.rcParams['figure.dpi'] = 150

iodepth_labels = ['1', '2', '4', '8', '16', '32', '64', '128']
x = np.arange(len(iodepth_labels))

san_randread  = [2926, 7039, 13012, 20174, 36928, 60598, 82667, 80860]
nas_randread  = [2211, 5231, 9458, 14662, 23909, 36698, 41880, 41990]

san_randwrite = [2152, 4109, 9211, 16093, 26642, 30155, 36810, 43911]
nas_randwrite = [1969, 3560, 6895, 12481, 21151, 29879, 34672, 34779]

SAN_COLOR = '#2196F3'
NAS_COLOR = '#FF9800'
BAR_WIDTH = 0.35

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

ax1.bar(x - BAR_WIDTH/2, san_randread, BAR_WIDTH, label='ontap-san', color=SAN_COLOR)
ax1.bar(x + BAR_WIDTH/2, nas_randread, BAR_WIDTH, label='ontap-nas', color=NAS_COLOR)
ax1.set_title('Random Read — IOPS by iodepth')
ax1.set_xlabel('iodepth')
ax1.set_ylabel('IOPS')
ax1.set_xticks(x)
ax1.set_xticklabels(iodepth_labels)
ax1.legend()
ax1.grid(axis='y', alpha=0.3)

ax2.bar(x - BAR_WIDTH/2, san_randwrite, BAR_WIDTH, label='ontap-san', color=SAN_COLOR)
ax2.bar(x + BAR_WIDTH/2, nas_randwrite, BAR_WIDTH, label='ontap-nas', color=NAS_COLOR)
ax2.set_title('Random Write — IOPS by iodepth')
ax2.set_xlabel('iodepth')
ax2.set_ylabel('IOPS')
ax2.set_xticks(x)
ax2.set_xticklabels(iodepth_labels)
ax2.legend()
ax2.grid(axis='y', alpha=0.3)

fig.suptitle('4k Random IO — IOPS by iodepth (iter2-3 avg, drop_caches)', fontsize=13, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.94])

outdir = './output'
fig.savefig(f'{outdir}/fio-chart-iodepth-iops.png', bbox_inches='tight')
plt.close(fig)
print('Created fio-chart-iodepth-iops.png')
