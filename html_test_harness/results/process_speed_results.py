from csv import reader
import statistics


def open_series(name):
    with open(f"{name}.csv") as fh:
        csv_file = reader(fh)

        return list(csv_file)


def compare(baseline, series, position=1):
    for base_stats, stats in zip(baseline, series):
        base_stat = int(base_stats[position])
        stat = int(stats[position])

        diff = stat - base_stat
        yield diff / base_stat


def percent(value):
    value *= 100

    pre = '+' if value > 0 else ''

    return f"{pre}{value:.02f}%"

def compare_series(baseline, series):
    FIRST_LOAD = 1
    COMPLETE = 2

    stats = {
        'first_load': list(compare(baseline, series, FIRST_LOAD)),
        'complete': list(compare(baseline, series, COMPLETE))
    }

    for name, values in stats.items():
        print(name)
        print(
            "\t",
            'Min', percent(min(values)),
            'Median', percent(statistics.median(values)),
            'Mean', percent(statistics.mean(values)),
            'Max', percent(max(values)),
            'StDev', percent(statistics.stdev(values))
        )


baseline = open_series('baseline')
pywb = open_series('pywb')

compare_series(baseline, pywb)