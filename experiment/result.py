import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math
import sys
from to_precision import std_notation, sci_notation

project_root = os.path.dirname(os.path.dirname(__file__))
experiment_dir = os.path.dirname(__file__)
plots_dir = os.path.join(experiment_dir, "plots")
os.makedirs(plots_dir, exist_ok=True)

pd.set_option("display.max_rows", None, "display.max_columns", None, 'display.width', None)
round_to_n = lambda x, n: x if x == 0 else round(x, -int(math.floor(math.log10(abs(x)))) + (n - 1))


def _parse_map_size(size):
    if size == '21x35':
        return 'S'
    else:
        return 'L'


def parse_map_size(df: pd.DataFrame):
    arr = df['size'].unique()
    if len(arr) != 1:
        return ''
    return _parse_map_size(arr[0])


def parse_methods(df: pd.DataFrame):
    edf_df = df[(df['scheduler'] == 'edf') & (df['window'] == 0)]
    flex_df = df[(df['scheduler'] == 'flex') & (df['window'] == 0)]
    window_df = df[(df['scheduler'] == 'flex') & (df['window'] == 20)]
    return edf_df, flex_df, window_df


def parse_branch_and_bound(df: pd.DataFrame):
    sort_df = df[(df['bound'] == True) & (df['sort'] == True)].set_index(['agent', 'task_per_agent', 'seed'])
    bound_df = df[(df['bound'] == True) & (df['sort'] == False)].set_index(['agent', 'task_per_agent', 'seed'])
    no_df = df[(df['bound'] == False) & (df['sort'] == False)].set_index(['agent', 'task_per_agent', 'seed'])
    new_bound_df = bound_df.join(sort_df, on=['agent', 'task_per_agent', 'seed'], lsuffix='_bound', rsuffix='_sort')
    new_no_df = no_df.join(sort_df, on=['agent', 'task_per_agent', 'seed'], lsuffix='_no', rsuffix='_sort')
    return sort_df, new_bound_df, new_no_df


def parse_dummy_path(df: pd.DataFrame):
    reserve_dynamic_df = df[df['reserve_all'] == False].set_index(['agent', 'task_per_agent', 'seed'])
    reserve_all_df = df[df['reserve_all'] == True].set_index(['agent', 'task_per_agent', 'seed'])
    new_df = reserve_dynamic_df.join(reserve_all_df, on=['agent', 'task_per_agent', 'seed'], lsuffix='_dynamic',
                                     rsuffix='_all')
    return new_df


def parse_control_variable(df: pd.DataFrame, control_variable: str):
    on_df = df[df[control_variable] == True].set_index(['agent', 'task_per_agent', 'seed'])
    off_df = df[df[control_variable] == False].set_index(['agent', 'task_per_agent', 'seed'])
    new_df = on_df.join(off_df, on=['agent', 'task_per_agent', 'seed'], lsuffix='_on', rsuffix='_off')
    return new_df


# for each (agent, task_per_agent), draw phi as x, success rate as y
def plot_phi_vs_success(df, agent, task_per_agent):
    cond = (df['agent'] == agent) & (df['task_per_agent'] == task_per_agent) & (df['time_ms'] >= 0) & \
           (df['bound'] == True) & (df['sort'] == True) & (df['mlabel'] == True) & (df['reserve_all'] == False)
    new_df = df[cond]
    map_size = parse_map_size(new_df)
    filename = 'SR-%s-M-%d-N-%d.png' % (map_size, agent, task_per_agent)
    title = 'Success Rate: %s Map, M=%d, N=%d' % (map_size, agent, task_per_agent)
    print(filename, title)

    edf_df, flex_df, window_df = parse_methods(new_df)
    plt.figure()
    plt.plot(edf_df['phi'], edf_df['task_success'] / edf_df['task_num'], label="edf", marker="o", linestyle="")
    plt.plot(flex_df['phi'], flex_df['task_success'] / flex_df['task_num'], label="flex", marker="x", linestyle="")
    plt.plot(window_df['phi'], window_df['task_success'] / window_df['task_num'], label="window", marker=".",
             linestyle="")
    plt.xlabel('phi')
    plt.ylabel('success rate')
    plt.legend()
    plt.title(title)
    plt.savefig(os.path.join(plots_dir, filename))
    plt.close()


# for each (agent, task_per_agent), draw phi as x, success rate as y
def plot_phi(df):
    cond = (df['time_ms'] >= 0) & \
           (df['bound'] == True) & (df['sort'] == True) & (df['mlabel'] == True) & (df['reserve_all'] == False)
    new_df = df[cond]
    map_size = parse_map_size(new_df)
    filename = 'SR-%s.png' % map_size
    title = 'Success Rate: %s Map' % map_size
    print(filename, title)

    edf_df, flex_df, window_df = parse_methods(new_df)
    edf_df = edf_df.groupby(['phi'], as_index=False).mean()
    flex_df = flex_df.groupby(['phi'], as_index=False).mean()
    window_df = window_df.groupby(['phi'], as_index=False).mean()
    print("edf", edf_df)
    print("flex", flex_df)
    print("window", window_df)

    plt.figure()
    plt.plot(edf_df['phi'], edf_df['success_rate'], label="edf", marker="o", linestyle="")
    plt.plot(flex_df['phi'], flex_df['success_rate'], label="flex", marker="x", linestyle="")
    plt.plot(window_df['phi'], window_df['success_rate'], label="window", marker=".",
             linestyle="")
    plt.xlabel('phi')
    plt.ylabel('success rate')
    plt.legend()
    plt.title(title)
    plt.savefig(os.path.join(plots_dir, filename))
    plt.close()


# for each (map, phi, k), draw task_num as x, success rate as y
def plot_tasks_vs_success(df, size, phi, k):
    df['ratio'] = df['task_success'] / df['task_num']
    cond = (df['size'] == size) & (df['phi'] == phi) & (df['task_per_agent'] == k) & (df['time_ms'] >= 0) & \
           (df['bound'] == True) & (df['sort'] == True) & (df['mlabel'] == True) & (df['reserve_all'] == False) & \
           (df['scheduler'] == 'flex') & (df['recalc'] == True) & (df['nearest'] == False) & (df['ec'] == False) & \
           (df['retry'] == True)
    new_df = df[cond].copy()
    map_size = parse_map_size(new_df)

    if not map_size:
        return '', ''

    phi_str = str(phi)
    filename = 'SR-%s-PHI-%s-k-%s.png' % (map_size, phi_str.replace('-', 'n'), k)
    title = 'Success Rate: %s Map, Phi=%s, k=%s' % (map_size, phi_str, k)
    print(filename, title)
    new_df = new_df.groupby(['agent', 'task_per_agent', 'scheduler'], as_index=False).mean()

    edf_df, flex_df, window_df = parse_methods(new_df)
    plt.figure()
    # plt.plot(edf_df['task_num'], edf_df['task_success'] / edf_df['task_num'], label="edf", marker="o", linestyle="")
    plt.plot(flex_df['agent'], flex_df['task_success'] / flex_df['task_num'], label="flex", marker="x", linestyle="")
    # plt.plot(window_df['agent'], window_df['task_success'] / window_df['task_num'], label="window", marker=".",
    # linestyle="")
    plt.xlabel('agent number')
    plt.ylabel('success rate')
    plt.legend()
    plt.title(title)
    plt.savefig(os.path.join(plots_dir, filename))
    plt.close()

    print_df = new_df[['agent', 'task_per_agent', 'task_num', 'phi', 'recalc',
                       'task_success', 'ratio', 'time_ms']] \
        .sort_values(['agent', 'task_per_agent'])
    print(print_df)

    ratios = []
    times = []
    for index, row in print_df.iterrows():
        ratios.append(std_notation(row['ratio'], 4))
        times.append(std_notation(row['time_ms'] / 1000, 4))

    ratio_str = '%s & $%d \\times M$ & %s \\\\ \\hline' % (phi, k, ' & '.join(ratios))
    time_str = '%s & $%d \\times M$ & %s \\\\ \\hline' % (phi, k, ' & '.join(times))
    return ratio_str, time_str, print_df


def plot_branch_and_bound(df, size, phi):
    cond = (df['size'] == size) & (df['phi'] == phi) & (df['time_ms'] >= 0) & \
           (df['mlabel'] == True) & (df['reserve_all'] == False) & \
           (df['scheduler'] == 'flex') & (df['window'] == 0) & (df['recalc'] == True) & (df['retry'] == True)
    new_df = df[cond].copy()
    if len(new_df) == 0:
        return []

    map_size = parse_map_size(new_df)
    phi_str = str(phi)
    filename = 'BB-%s-PHI-%s.png' % (map_size, phi_str.replace('-', 'n'))
    title = 'Branch and Bound: %s Map, Phi=%s' % (map_size, phi_str)
    print(filename, title)

    sort_df, bound_df, no_df = parse_branch_and_bound(new_df)
    no_df.reset_index(level=no_df.index.names, inplace=True)
    no_df['ratio'] = no_df['time_ms_no'] / no_df['time_ms_sort']
    no_df = no_df.groupby(['agent', 'task_per_agent'], as_index=False).mean()
    # print(no_df)

    plt.figure()
    plt.plot(sort_df['task_num'], sort_df['task_num'] * 0 + 1, label="branch and bound (baseline) ", linestyle="-")
    # plt.plot(bound_df['task_num_sort'], bound_df['time_ms_bound'] / bound_df['time_ms_sort'], label="only bound", marker="o", linestyle="")
    plt.plot(no_df['task_num_sort'], no_df['time_ms_no'] / no_df['time_ms_sort'], label="no branch and bound",
             marker="x", linestyle="")

    plt.yscale('log')
    plt.xlabel('tasks number')
    plt.ylabel('running time multiplier')
    plt.legend()
    plt.title(title)
    plt.savefig(os.path.join(plots_dir, filename))
    plt.close()

    print_df = no_df[['agent', 'task_per_agent', 'task_num_sort', 'time_ms_no', 'time_ms_sort', 'ratio']] \
        .sort_values(['agent', 'task_per_agent'])
    print(print_df)

    ratio_str = []
    for task_per_agent, group in print_df.groupby('task_per_agent'):
        ratios = []
        for index, row in group.iterrows():
            ratios.append(std_notation(row['ratio'], 4))
        ratio_str.append('%s & $%d \\times M$ & %s \\\\ \\hline' % (phi, task_per_agent, ' & '.join(ratios)))

    return ratio_str


def plot_dummy_path(df, size, phi):
    cond = (df['size'] == size) & (df['phi'] == phi) & (df['time_ms'] >= 0) & \
           (df['bound'] == True) & (df['sort'] == True) & (df['mlabel'] == True) & (df['recalc'] == True) & \
           (df['scheduler'] == 'flex') & (df['window'] == 0) & (df['skip'] == True) & (df['task_bound'] == True) & \
           (df['retry'] == True) & (df['nearest'] == False) & (df['ec'] == False)
    new_df = df[cond].copy()
    # parse_dummy_path(new_df)
    map_size = parse_map_size(new_df)
    phi_str = str(phi)
    filename = 'DP-%s-PHI-%s.png' % (map_size, phi_str.replace('-', 'n'))
    title = 'Dummy Path: %s Map, Phi=%s' % (map_size, phi_str)
    print(filename, title)

    new_df = parse_dummy_path(new_df)
    new_df.reset_index(level=new_df.index.names, inplace=True)
    new_df['ratio'] = new_df['time_ms_all'] / new_df['time_ms_dynamic']
    # new_df['reserve_ratio'] = new_df['reserve_dynamic'] / new_df['task_num_dynamic']
    new_df['reserve_ratio'] = new_df['reserve_dynamic'] / new_df['task_success_dynamic']

    new_df = new_df.groupby(['agent', 'task_per_agent'], as_index=False).mean()
    # print(new_df)

    plt.figure()
    plt.plot(new_df['task_num_dynamic'], new_df['task_num_dynamic'] * 0 + 1, label="dynamic reserve (baseline) ",
             linestyle="-")
    for agent in sorted(new_df['agent'].unique()):
        plot_df = new_df[new_df['agent'] == agent]
        label = "reserve all (N=%d)" % agent
        plt.plot(plot_df['task_num_dynamic'], plot_df['ratio'], label=label, marker="x", linestyle="")

    plt.xlabel('tasks number')
    plt.ylabel('running time multiplier')
    plt.legend()
    plt.title(title)
    plt.savefig(os.path.join(plots_dir, filename))
    plt.close()

    print_df = new_df[['agent', 'task_per_agent', 'task_num_all', 'time_ms_all', 'time_ms_dynamic', 'ratio',
                       'reserve_dynamic', 'task_success_dynamic', 'reserve_ratio']] \
        .sort_values(['agent', 'task_per_agent'])
    print(print_df)

    ratio_str = []
    reserve_ratio_str = []
    for task_per_agent, group in print_df.groupby('task_per_agent'):
        ratios = []
        reserve_ratios = []
        for index, row in group.iterrows():
            ratios.append(std_notation(row['ratio'], 4))
            reserve_ratios.append(std_notation(row['reserve_ratio'], 4))
        ratio_str.append('%s & $%d \\times M$ & %s \\\\ \\hline' % (phi, task_per_agent, ' & '.join(ratios)))
        reserve_ratio_str.append(
            '%s & $%d \\times M$ & %s \\\\ \\hline' % (phi, task_per_agent, ' & '.join(reserve_ratios)))

    return ratio_str, reserve_ratio_str

    # print(new_df[['agent', 'task_per_agent', 'task_num_all', 'time_ms_all', 'time_ms_dynamic', 'ratio']]
    #       .sort_values(['agent', 'task_per_agent']))


def plot_recalculate(df, size, phi):
    cond = (df['size'] == size) & (df['phi'] == phi) & (df['time_ms'] >= 0) & \
           (df['bound'] == True) & (df['sort'] == True) & (df['mlabel'] == True) & (df['reserve_all'] == False) & \
           (df['scheduler'] == 'flex') & (df['window'] == 0) & (df['skip'] == True) & (df['task_bound'] == True) & \
           (df['nearest'] == False) & (df['recalc'] == True)
    new_df = df[cond].copy()
    map_size = parse_map_size(new_df)
    phi_str = str(phi)
    filename = 'DP-%s-PHI-%s.png' % (map_size, phi_str.replace('-', 'n'))
    title = 'Recalculate: %s Map, Phi=%s' % (map_size, phi_str)
    print(filename, title)

    new_df = parse_control_variable(new_df, 'ec')
    new_df.reset_index(level=new_df.index.names, inplace=True)
    # new_df['ratio'] = new_df['time_ms_all'] / new_df['time_ms_dynamic']
    # new_df['success_ratio'] = new_df['time_ms_off'] / new_df['time_ms_on']
    new_df['success_ratio'] = new_df['task_success_on'] / new_df['task_success_off']

    new_df = new_df.groupby(['agent', 'task_per_agent'], as_index=False).mean()

    print_df = new_df[['agent', 'task_per_agent', 'task_num_on', 'task_success_on', 'task_success_off',
                       'time_ms_on', 'time_ms_off', 'success_ratio']] \
        .sort_values(['agent', 'task_per_agent'])
    print(print_df)

    success_ratio_str = []
    for task_per_agent, group in print_df.groupby('task_per_agent'):
        success_ratios = []
        for index, row in group.iterrows():
            success_ratios.append(std_notation(row['success_ratio'], 4))
        success_ratio_str.append(
            '%s & $%d \\times M$ & %s \\\\ \\hline' % (phi, task_per_agent, ' & '.join(success_ratios)))

    return success_ratio_str


def plot_nearest_ec(df, size, phi):
    cond = (df['size'] == size) & (df['phi'] == phi) & (df['time_ms'] >= 0) & \
           (df['bound'] == True) & (df['sort'] == True) & (df['mlabel'] == True) & (df['reserve_all'] == False) & \
           (df['scheduler'] == 'flex') & (df['window'] == 0) & (df['skip'] == True) & (df['task_bound'] == True) & \
           (df['recalc'] == True)
    new_df = df[cond].copy()
    map_size = parse_map_size(new_df)
    phi_str = str(phi)
    title = 'Nearest & Extra Cost: %s Map, Phi=%s' % (map_size, phi_str)
    print(title)

    new_df = new_df.groupby(['agent', 'task_per_agent', 'nearest', 'ec'], as_index=False).mean()
    print(new_df)


def calculate_average(df, reserve_all, label):
    cond = (df['bound'] == True) & (df['sort'] == True) & (df['mlabel'] == True) & \
           (df['window'] == 0) & (df['reserve_all'] == reserve_all) & \
           (df['skip'] == True) & (df['task_bound'] == True)
    new_df = df[cond].groupby(['phi', 'scheduler'], as_index=False).mean()
    print('Average-%s' % label)
    print(new_df)


def generate_table(data, size):
    assert len(data) > 0
    print()
    for i in range(2, len(data[0])):
        table = []
        for row in data:
            if row[0] == size:
                table.append('\n'.join(row[i]))
        print('\n'.join(table))
        print()


def generate_csv(result_dfs, size):
    dfs = []
    for map_size, df in result_dfs:
        if map_size == size:
            dfs.append(df)
    new_df = pd.concat(dfs)
    print(new_df)
    recalc = bool(new_df['recalc'].unique()[0]) and '-exp' or '-baseline'
    filename = 'result' + recalc + '-' + size + '.csv'
    new_df.to_csv(os.path.join(experiment_dir, filename), index_label=False, float_format="%.5f")


def main():
    # small_filename = os.path.join(experiment_dir, "result-new-small.csv")
    # large_filename = os.path.join(experiment_dir, "result-new-big.csv")
    # small_df = pd.read_csv(small_filename)
    # small_df['success_rate'] = small_df['task_success'] / small_df['task_num']
    # large_df = pd.read_csv(large_filename)
    # large_df['success_rate'] = large_df['task_success'] / large_df['task_num']
    # all_df = pd.concat([small_df, large_df])

    all_filename = os.path.join(experiment_dir, "result.csv")
    all_df = pd.read_csv(all_filename)

    # calculate_average(large_df, False, 'L')
    # calculate_average(small_df, False, 'S')

    # plot_phi(small_df)
    # plot_phi(large_df)

    # pairs = all_df.groupby(['agent', 'task_per_agent']).first()
    # for index, row in pairs.iterrows():
    #     agent, task_per_agent = index
    #     plot_phi_vs_success(all_df, agent, task_per_agent)

    pairs = all_df.groupby(['size', 'phi']).first()
    data = []
    result_dfs = []
    for index, row in pairs.iterrows():
        size, phi = index
        if phi >= 0:
            ratios = []
            times = []
            for k in [10]:
                ratio, time, result_df = plot_tasks_vs_success(all_df, size, phi, k)
                ratios.append(ratio)
                times.append(time)
                data.append((_parse_map_size(size), phi, ratios, times))
                result_dfs.append((_parse_map_size(size), result_df))
    #
    # print(data)
    generate_table(data, 'S')
    generate_table(data, 'L')
    generate_csv(result_dfs, 'S')
    generate_csv(result_dfs, 'L')

    # pairs = all_df.groupby(['size', 'phi']).first()
    # data = []
    # for index, row in pairs.iterrows():
    #     size, phi = index
    #     if phi >= 0:
    #         ratios, reserve_ratios = plot_dummy_path(all_df, size, phi)
    #         data.append((_parse_map_size(size), phi, ratios, reserve_ratios))
    # generate_table(data, 'S')
    # generate_table(data, 'L')

    # pairs = all_df.groupby(['size', 'phi']).first()
    # data = []
    # for index, row in pairs.iterrows():
    #     size, phi = index
    #     if phi >= 0:
    #         success_ratios = plot_recalculate(all_df, size, phi)
    #         data.append((_parse_map_size(size), phi, success_ratios))
    #
    # generate_table(data, 'S')
    # generate_table(data, 'L')

    # pairs = all_df.groupby(['size', 'phi']).first()
    # data = []
    # for index, row in pairs.iterrows():
    #     size, phi = index
    #     if phi >= 0:
    #         ratios = plot_branch_and_bound(all_df, size, phi)
    #         data.append((_parse_map_size(size), phi, ratios))
    # generate_table(data, 'S')

    # print(pair)
    # agent = pair[['agent']]
    # task_per_agent = pair[['task_per_agent']]
    # print(agent, task_per_agent)

    # pairs = all_df.groupby(['size', 'phi']).first()
    # data = []
    # for index, row in pairs.iterrows():
    #     size, phi = index
    #     if phi >= 0:
    #         plot_nearest_ec(all_df, size, phi)


if __name__ == '__main__':
    main()
