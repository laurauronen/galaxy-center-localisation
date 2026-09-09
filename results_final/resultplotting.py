import os 
import json 
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

plt.rcParams.update({'text.usetex': True,'font.size':24, 'font.family':'serif'})

def stats(data, val):
    empirical_p = sum(d <= val for d in data) / len(data)
    
    mean = np.mean(data)
    std_dev = np.std(data)
    effective_z = (val - mean) / std_dev

    median_ratio = val / np.median(data)

    print(f"""r: {val:.4f}
Empirical p-value: {empirical_p*100:.4f} % 
Effective z-score: {effective_z:.4f}
Median ratio: {median_ratio:.4f}""")

    return empirical_p, effective_z, median_ratio

def violins2(data1, data2, data3, data4, data5, data6, 
            prob1, prob2, prob3, prob4, prob5, prob6,
            r1, r2, r3, r4, r5, r6,
            filename='plot.png'):
    
    fig, axes = plt.subplots(1, 2, figsize=(20, 10), sharey=True)
    plt.rcParams.update({'text.usetex': True,'font.size':30, 'font.family':'serif'})

    p1, q1 = np.percentile(data1, [5, 95])
    datainner1 = [d for d in data1 if p1 <= d <= q1]
    p2, q2 = np.percentile(data2, [5, 95])
    datainner2 = [d for d in data2 if p2 <= d <= q2]
    p3, q3 = np.percentile(data3, [5, 95])
    datainner3 = [d for d in data3 if p3 <= d <= q3]
    p4, q4 = np.percentile(data4, [5, 95])
    datainner4 = [d for d in data4 if p4 <= d <= q4]
    p5, q5 = np.percentile(data5, [5, 95])
    datainner5 = [d for d in data5 if p5 <= d <= q5]
    p6, q6 = np.percentile(data6, [5, 95])
    datainner6 = [d for d in data6 if p6 <= d <= q6]

    ax = axes[0]
    ax.set_title('Uniform prior', fontsize=24)
    vp = ax.violinplot([data1, data2, data3],
                       showmeans=True, showextrema=True, points=1000)
    colors = [
    'navy',
    'slateblue',
    'dodgerblue'
    ]
    ip = ax.violinplot([datainner1, datainner2, datainner3],
                       showmeans=False, showextrema=False, widths=0.4, points=1000)
    ax.axhline(y = 0.0, color='k', linewidth=1)

    for i, body in enumerate(vp['bodies']):
        body.set_facecolor(colors[i])
        body.set_alpha(0.5)
        body.set_edgecolor(colors[i])
        body.set_linewidth(2)

    for i, body in enumerate(ip['bodies']):
        body.set_facecolor('white')
        body.set_alpha(0.7)
        body.set_linewidth(2)

    vp['cmeans'].set_color(colors)
    vp['cbars'].set_color(colors)
    vp['cmins'].set_color(colors)
    vp['cmaxes'].set_color(colors)

    rs = [r1, r2, r3]
    vals = [prob1, prob2, prob3]

    for i, (r, va) in enumerate(zip(rs, vals)):
        ax.scatter(i+1-0.002, r, marker='d', s=200, color=colors[i], zorder=3)
        ax.text(i+1-0.1, -0.015, f'{va*100:.2f}\%', color=colors[i])

    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(
    [r'Small', 
     r'Average', 
     r'Large'],
    #rotation=45,        # angle
    #ha='right'          # horizontal alignment
)
    ax.set_ylabel(r'$r_{10}$ (arcsec)')
    ax.set_ylim(-0.02, 0.2)
    ax.tick_params(axis='both', direction='out', length=10, width=1)

    ax = axes[1]
    ax.set_title(r'Gaussian prior', fontsize=24)
    vp = ax.violinplot([data4, data5, data6], 
                       showmeans=True, showextrema=True, points=1000)
    #colors = [
    #'coral',
    #'gold',
    #'mediumvioletred',
    #]
    ip = ax.violinplot([datainner4, datainner5, datainner6], 
                       showmeans=False, showextrema=False, widths=0.4, points=1000)
    ax.axhline(y = 0.0, color='k', linewidth=1)

    for i, body in enumerate(vp['bodies']):
        body.set_facecolor(colors[i])
        body.set_alpha(0.5)
        body.set_edgecolor(colors[i])
        body.set_linewidth(2)
    for i, body in enumerate(ip['bodies']):
        body.set_facecolor('white')
        body.set_alpha(0.7)
        body.set_linewidth(3)

    vp['cmeans'].set_color(colors)
    vp['cbars'].set_color(colors)
    vp['cmins'].set_color(colors)
    vp['cmaxes'].set_color(colors)
    rs = [r4, r5, r6]
    vals = [prob4, prob5, prob6]

    for i, (r, va) in enumerate(zip(rs, vals)):
        ax.scatter(i+1-0.002, r, marker='d', s=200, color=colors[i], zorder=3)
        ax.text(i+1-0.2, -0.015, f'{va*100:.2f}\%', color=colors[i])
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(
     [r'Small', 
     r'Average', 
     r'Large'],
    #rotation=45,        # angle
    #ha='right'          # horizontal alignment
)
    ax.set_ylim(-0.02, 0.2)
    ax.tick_params(axis='both', direction='out', length=10, width=1)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.show()

bestjson = 'best/results.json'
avgjson = 'average/results.json'
worstjson = 'small/results.json'
json5 = 'unc_5/results.json'
json10 = 'unc_10/results.json'
avgreljson = 'rrel/results.json'
bestreljson = 'rrel_best/results.json'
smallreljson = 'rrel_small/results.json'
newbkgunijson = 'newbkg_uni/results.json'
newbkgnormjson = 'newbkg_norm/results.json'
weightedjson = 'weighted_mean/results.json'

best = json.load(open(bestjson))
avg = json.load(open(avgjson))
worst = json.load(open(worstjson))
j5 = json.load(open(json5))
j10 = json.load(open(json10))
bestrel = json.load(open(bestreljson))
avgrel = json.load(open(avgreljson))
smallrel = json.load(open(smallreljson))
newbkguni = json.load(open(newbkgunijson))
newbkgnorm = json.load(open(newbkgnormjson))
weighted = json.load(open(weightedjson))

r_best = best['true_90th_percentile']
data_best = best['all_90th_percentiles']
val_best = best['probability']

r_avg = avg['true_90th_percentile']
data_avg = avg['all_90th_percentiles']
val_avg = avg['probability']

r_worst = worst['true_90th_percentile']
data_worst = worst['all_90th_percentiles']
val_worst = worst['probability']

dat5 = j5['all_90th_percentiles']
true5 = j5['true_90th_percentile']
val5 = j5['probability']

dat10 = j10['all_90th_percentiles']
true10 = j10['true_90th_percentile']
val10 = j10['probability']

data_avgrel = avgrel['all_90th_percentiles']
true_avgrel = avgrel['true_90th_percentile']
val_avgrel = avgrel['probability']

data_bestrel = bestrel['all_90th_percentiles']
true_bestrel = bestrel['true_90th_percentile']
val_bestrel = bestrel['probability']

data_smallrel = smallrel['all_90th_percentiles']
true_smallrel = smallrel['true_90th_percentile']
val_smallrel = smallrel['probability']

data_newuni = newbkguni['all_90th_percentiles']
true_newuni  = newbkguni['true_90th_percentile']
val_newuni  = newbkguni['probability']

data_newnorm = newbkgnorm['all_90th_percentiles']
true_newnorm  = newbkgnorm['true_90th_percentile']
val_newnorm = newbkgnorm['probability']

data_weight = weighted['all_90th_percentiles']
true_weight  = weighted['true_90th_percentile']
val_weight = weighted['probability']

plt.rcParams.update({'text.usetex': True,'font.size':26, 'font.family':'serif'})

violins2(data_worst, data_avg, data_best, data_smallrel, data_avgrel, data_bestrel,
         val_worst, val_avg, val_best, val_smallrel, val_avgrel, val_bestrel,
         r_worst, r_avg, r_best, true_smallrel, true_avgrel, true_bestrel,
         filename='violins_panels.pdf')

from astropy.cosmology import Planck18 as cosmo
def conv_arcsec_to_pc(arcsec, z):
    kpc_per_arcsec = cosmo.kpc_proper_per_arcmin(z).value / 60.0
    return arcsec * kpc_per_arcsec * 1000

z_small = 2.0
z_mid = 1.5
z_big = 0.8

small = conv_arcsec_to_pc(r_worst, z_small)
mid = conv_arcsec_to_pc(r_avg, z_mid)
big = conv_arcsec_to_pc(r_best, z_big)

five = conv_arcsec_to_pc(true5, z_mid)
ten = conv_arcsec_to_pc(true10, z_mid)

smarel = conv_arcsec_to_pc(true_smallrel, z_small)
avrel = conv_arcsec_to_pc(true_avgrel, z_mid)
berel = conv_arcsec_to_pc(true_bestrel, z_big)

uni = conv_arcsec_to_pc(true_newuni, z_mid)
norm = conv_arcsec_to_pc(true_newnorm, z_mid)
wei = conv_arcsec_to_pc(true_weight, z_mid)

with open('summary_table.txt', 'w') as f:
    f.write("Case \t r_10 (arcsec) \t r_10 (pc) \t p-value (%) \n")
    f.write(f"Worst \t {r_worst:.5f} \t {small:.2f} \t {val_worst*100:.4f} \n")
    f.write(f"Average \t {r_avg:.5f} \t {mid:.2f} \t {val_avg*100:.4f} \n")
    f.write(f"Best \t {r_best:.5f} \t {big:.2f} \t {val_best*100:.4f} \n")
    f.write(f"Gaussian Worst \t {true_smallrel:.5f} \t {smarel:.2f} \t {val_smallrel*100:.4f} \n")
    f.write(f"Gaussian Average \t {true_avgrel:.5f} \t {avrel} \t {val_avgrel*100:.4f} \n")
    f.write(f"Gaussian Best \t {true_bestrel:.5f} \t {berel:.2f} \t {val_bestrel*100:.4f} \n")
    f.write(f"Uncertainty 5 \t {true5:.5f} \t {five:.2f} \t {val5*100:.4f} \n")
    f.write(f"Uncertainty 10 \t {true10:.5f} \t {ten:.2f} \t {val10*100:.4f} \n")
    f.write(f"New bkg, Uni \t {true_newuni:.5f} \t {uni:.2f} \t {val_newuni*100:.4f} \n")
    f.write(f"New bkg, Norm \t {true_newnorm:.5f} \t {norm:.2f} \t {val_newnorm*100:.4f} \n")
    f.write(f"Weighted \t {true_weight:.5f} \t {wei:.2f} \t {val_weight*100:.4f} \n")
f.close()