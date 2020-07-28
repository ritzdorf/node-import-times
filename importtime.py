import sys
import argparse
import re
import statistics
import matplotlib.pyplot as plt
import numpy as np


class LogEntry:

    def __init__(self, number, txs, mgas, ms):
        self.number = number
        self.txs = txs
        self.mgas = mgas
        self.ms = ms


def compute_averages(entries):
    atxs = statistics.mean(e.txs for e in entries)
    amgas = statistics.mean(e.mgas for e in entries)
    ams = statistics.mean(e.ms for e in entries)
    amgasps = sum(e.mgas * e.ms for e in entries) / sum(e.ms for e in entries) 
    return atxs, amgas, ams, amgasps 


parser = argparse.ArgumentParser(description='Analyse Ethereum client log files for import times')
parser.add_argument('-g', '--geth', action='store_true',
                        help='geth mode')
parser.add_argument('-p', '--parity', action='store_true',
                        help='parity mode')
parser.add_argument('-v', '--verbose', action='count',
                        help='Verbose mode')
parser.add_argument('logfile', help='logfile to parse')
args = parser.parse_args()


if (not args.parity and not args.geth) or (args.parity and args.geth):
    parser.print_help()
    sys.exit(1)

try:
    f = open(args.logfile)
except FileNotFoundError:
    print("[!] Error: %s couldn't be opened." %(args.logfile))    
    sys.exit(1)


print("[+] Reading data from %s" %(args.logfile))

name = ""
if args.geth:
    name = "geth"
elif args.parity:
    name = "parity"


verbose = False
if args.verbose and args.verbose >= 1:
	verbose = True

if args.parity:
    prog = re.compile("Imported #(\d+) .* \((\d+) txs, ([0-9.]+) Mgas, (\d+) ms")
else:
    prog = re.compile("Imported new chain segment\s+ blocks=(\d+)\s+txs=(\d+)\s+mgas=([0-9.]+)\s+elapsed=([0-9\.]+m?s).* number=(\d+)")

entries = []
for line in f:
    match = prog.search(line)
    if not match:
        continue

    if args.parity:
        if "another" in line:
            continue
        number, txs, mgas, ms = match.groups()
    elif args.geth:
        blocks, txs, mgas, ms, number = match.groups()
        if int(blocks) != 1:
            continue
        # Check if time was measured in seconds
        if not ms.endswith('ms'):
            ms = float(ms[:-1]) * 1000
        else:
            ms = float(ms[:-2])


    entries.append(LogEntry(int(number), int(txs), float(mgas), float(ms)))

blocknums = list(e.number for e in entries)
print("[+] Processed %i blocks (in range %i - %i)" %(len(entries), min(blocknums), max(blocknums)))

atxs, amgas, ams, amgasps = compute_averages(entries)
print("[+] Averages:")
print("[++] Average Txs: %.2f" %(atxs))
print("[++] Average Mgas: %.2f" %(amgas))
print("[++] Average ms: %.2f" %(ams))
print("[++] Average (weighted) mgasps: %.2f" %(amgasps))

times = list(e.ms for e in entries)
print("[+] Extremes:")
print("[++] Shortest time: %.2f" %(min(times)))
print("[++] Longest time: %.2f" %(max(times)))

print("[+] Percentiles:")
print("[++]  5th Percentiles: %.2f" %(np.percentile(times,  5)))
print("[++] 25th Percentiles: %.2f" %(np.percentile(times, 25)))
print("[++] 50th Percentiles: %.2f" %(np.percentile(times, 50)))
print("[++] 75th Percentiles: %.2f" %(np.percentile(times, 75)))
print("[++] 90th Percentiles: %.2f" %(np.percentile(times, 90)))
print("[++] 95th Percentiles: %.2f" %(np.percentile(times, 95)))
print("[++] 99th Percentiles: %.2f" %(np.percentile(times, 99)))

if verbose:
    print("[++] 25 Longest running transactions: " + str(sorted(zip(times, blocknums))[-1:-25:-1]))

fig, axs = plt.subplots(1, 2, tight_layout=True)
axs[1].boxplot(times)
#axs[1].set_yscale('symlog')

axs[0].set_title("%s Time Distribution" %(name))
axs[1].set_title("%i Transactions" %(len(entries)))

axs[0].hist(times, bins=100, orientation='horizontal', density=True, cumulative=True, histtype="step", label="times")
axs[0].set_xlim((0,1))
axs[0].set_ylabel("Import Processing time (ms)")
#axs[0].set_yscale('symlog')
plt.savefig("times_%s.png" %(name))

plt.clf()

txs = list(e.txs for e in entries)
plt.scatter(txs, times)
plt.xlabel("Number of Transactions in Block")
plt.ylabel("Import Processing time (ms)")
plt.savefig("scatter_%s.png" %(name))
