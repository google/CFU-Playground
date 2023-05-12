import matplotlib.pyplot as plt
import numpy as np
import matplotlib

hardware_data = {
    "ORIGINAL\\_NO\\_QUANT": [
        5971026057,
        5944417118,
        6133404028,
        5833330973,
        6138185898,
        5911456163,
        6137149382,
        6049811882,
        6133211906,
        6022189573,
        5870294503,
    ],
    "ORIGINAL": [
        752182170,
        752122254,
        752160713,
        752140908,
        752142490,
        752102486,
        752149939,
        751750572,
        751771204,
        751773747,
        751773084,
    ],
    "SIMPLIFIED": [
        491407175,
        491360223,
        491397944,
        491335108,
        491375008,
        491349410,
        491376256,
        489941347,
        489936716,
        489965846,
        489923110,
    ],
    # "V4.0": [
    #     95719797,
    #     95676269,
    #     95716557,
    #     95676320,
    #     95696417,
    #     95666518,
    #     95687184,
    #     95719066,
    #     95726895,
    #     95731060,
    #     95720439,
    # ],
    # "V5.0": [
    #     88146970,
    #     88130416,
    #     88143378,
    #     88120787,
    #     88129324,
    #     88128744,
    #     88142928,
    #     87999091,
    #     87998990,
    #     88010580,
    #     88014720,
    # ],
    # "V5.1": [
    #     88683710,
    #     88667391,
    #     88680118,
    #     88657527,
    #     88666064,
    #     88665719,
    #     88679668,
    #     88531836,
    #     88531735,
    #     88542855,
    #     88547230,
    # ],
    # "V6.1": [
    #     66083613,
    #     66065016,
    #     66081619,
    #     66056950,
    #     66064052,
    #     66063548,
    #     66078644,
    #     66036291,
    #     66037426,
    #     66046356,
    #     66053939,
    # ],
    # "V7.0": [
    #     67859699,
    #     67841275,
    #     67857708,
    #     67834157,
    #     67840749,
    #     67840559,
    #     67856093,
    #     67747250,
    #     67746664,
    #     67757729,
    #     67762696,
    # ],
    # "V8.0": [
    #     70107097,
    #     70088996,
    #     70103962,
    #     70081439,
    #     70089759,
    #     70088734,
    #     70103388,
    #     70022851,
    #     70023791,
    #     70032091,
    #     70038780,
    # ],
    # "V8.0\nx1": [
    #     345659071,
    #     345657867,
    #     345656221,
    #     345655741,
    #     345657580,
    #     345658877,
    #     345656454,
    #     345658990,
    #     345656419,
    #     345657632,
    #     345655281,
    # ],
    # "V8.0\nx2": [
    #     187807435,
    #     187806722,
    #     187804371,
    #     187801071,
    #     187805495,
    #     187807497,
    #     187802724,
    #     187808363,
    #     187805509,
    #     187807945,
    #     187802961,
    # ],
    # "V8.0\nx4": [
    #     109606720,
    #     109587442,
    #     109604596,
    #     109578736,
    #     109586733,
    #     109586572,
    #     109602244,
    #     109583160,
    #     109583927,
    #     109593552,
    #     109600649,
    # ],
    # "V8.0\nx8": [
    #     70107097,
    #     70088996,
    #     70103962,
    #     70081439,
    #     70089759,
    #     70088734,
    #     70103388,
    #     70022851,
    #     70023791,
    #     70032091,
    #     70038780,
    # ],
    # "V8.0\nx16": [
    #     50291780,
    #     50272737,
    #     50289656,
    #     50263796,
    #     50271793,
    #     50271632,
    #     50287304,
    #     50268220,
    #     50269222,
    #     50278612,
    #     50285709,
    # ],
    # "V8.0\nx24": [
    #     44066395,
    #     44050925,
    #     44065681,
    #     44039586,
    #     44052470,
    #     44046530,
    #     44062859,
    #     44044245,
    #     44050134,
    #     44066152,
    #     44060297,
    # ],
    # "V8.0\nx32": [
    #     40583695,
    #     40567002,
    #     40582041,
    #     40555946,
    #     40563943,
    #     40563547,
    #     40579219,
    #     40560135,
    #     40560902,
    #     40575462,
    #     40577624,
    # ],
}

simulation_data = {
    "ORIGINAL\\_NO\\_QUANT": [
        4146482209,
        4124195519,
        4283585858,
        4029954626,
        4287531672,
        4095681454,
        4286648373,
        4213735836,
        4283620935,
        4189651281,
        4061753762,
    ],
    "ORIGINAL": [
        406868334,
        406834202,
        406864454,
        406844009,
        406855054,
        406822341,
        406850857,
        406852222,
        406856174,
        406855463,
        406853331,
    ],
    "SIMPLIFIED": [
        299648785,
        299621112,
        299645610,
        299628720,
        299637320,
        299611894,
        299636333,
        299634728,
        299637876,
        299637777,
        299638030,
    ],
    # "V1.0": [
    #     10415139,
    #     10387466,
    #     10411964,
    #     10395074,
    #     10403674,
    #     10378248,
    #     10402687,
    #     10401082,
    #     10404230,
    #     10404131,
    #     10404384,
    # ],
    # "V2.0": [
    #     33483262,
    #     33449130,
    #     33479382,
    #     33458937,
    #     33469982,
    #     33437269,
    #     33465785,
    #     33467150,
    #     33471102,
    #     33470391,
    #     33468259,
    # ],
    # "V3.0": [
    #     59497356,
    #     59463224,
    #     59493760,
    #     59473031,
    #     59484076,
    #     59451363,
    #     59479879,
    #     59481244,
    #     59485196,
    #     59484485,
    #     59482353,
    # ],
    # # "V4.0\nFirst Synthesizable": [
    # "V4.0": [
    #     49810757,
    #     49778778,
    #     49807112,
    #     49787852,
    #     49798082,
    #     49767798,
    #     49794955,
    #     49795330,
    #     49799014,
    #     49798507,
    #     49797170,
    # ],
    # "V5.0": [
    #     44552519,
    #     44543851,
    #     44551391,
    #     44545105,
    #     44546408,
    #     44542596,
    #     44555114,
    #     44544288,
    #     44545191,
    #     44546846,
    #     44554357,
    # ],
    # "V5.1": [
    #     45154631,
    #     45145963,
    #     45153503,
    #     45147217,
    #     45148520,
    #     45144708,
    #     45157226,
    #     45146400,
    #     45147303,
    #     45148958,
    #     45156469,
    # ],
    # "V6.0": [
    #     28805282,
    #     28796614,
    #     28804154,
    #     28797868,
    #     28799171,
    #     28795359,
    #     28807877,
    #     28797051,
    #     28797954,
    #     28799609,
    #     28807120,
    # ],
    # # "V6.0": [         // Doesn't use quant v2
    # #     28203170,
    # #     28194502,
    # #     28202042,
    # #     28195756,
    # #     28197059,
    # #     28193247,
    # #     28205765,
    # #     28194939,
    # #     28195842,
    # #     28197497,
    # #     28205008,
    # # ],
    # "V6.1": [
    #     29200999,
    #     29192343,
    #     29199887,
    #     29193620,
    #     29194879,
    #     29191076,
    #     29203605,
    #     29192772,
    #     29193670,
    #     29195334,
    #     29202857,
    # ],
    # # "V7.0": [         // Doesn't use quant_2 and uses conditional write size
    # #     26463890,
    # #     26455222,
    # #     26462762,
    # #     26456476,
    # #     26457779,
    # #     26453967,
    # #     26466485,
    # #     26455659,
    # #     26456562,
    # #     26458217,
    # #     26465728,
    # # ],
    # "V7.0": [
    #     27624493,
    #     27615837,
    #     27623381,
    #     27617114,
    #     27618373,
    #     27614570,
    #     27627099,
    #     27616266,
    #     27617164,
    #     27618828,
    #     27626351,
    # ],
    # "V8.0": [
    #     28745877,
    #     28737209,
    #     28744749,
    #     28738463,
    #     28739766,
    #     28735954,
    #     28748472,
    #     28737646,
    #     28738549,
    #     28740204,
    #     28747715,
    # ],
    # "V8.0\nx1": [138840456],
    # "V8.0\nx2": [75927431],
    # "V8.0\nx4": [44474325],
    # "V8.0\nx8": [28745877],
    # "V8.0\nx16": [20881941],
    # "V8.0\nx24": [18335081],
    # "V8.0\nx32": [16950459],
}


generate_pgf = True

if generate_pgf:
    matplotlib.use("pgf")
    matplotlib.rcParams.update(
        {
            "pgf.texsystem": "pdflatex",
            "font.family": "serif",
            "font.size": 7,
            "text.usetex": True,
            "pgf.rcfonts": False,
        }
    )


def main():
    meaned_simulation_data = {}
    for k, simulations_cycles in simulation_data.items():
        meaned_simulation_data[k] = np.mean(simulations_cycles)

    meaned_hardware_data = {}
    for k in simulation_data:
        if k in hardware_data:
            meaned_hardware_data[k] = np.mean(hardware_data[k])
        else:
            meaned_hardware_data[k] = 0

    simulation_versions = list(meaned_simulation_data.keys())
    simulations_cycles = list(meaned_simulation_data.values())

    hardware_versions = list(meaned_hardware_data.keys())
    hardware_cycles = list(meaned_hardware_data.values())

    fig, ax = plt.subplots()

    # creating the bar plot
    x = np.arange(len(meaned_simulation_data))
    width = 0.8
    hardware_bars = plt.bar(
        hardware_versions, hardware_cycles, color="#ebbd34", width=width, label="Hardware"
    )

    simulation_bars = plt.bar(
        simulation_versions, simulations_cycles, color="#63A8D3", width=width, label="Simulation"
    )
    # simulation_bars = plt.bar(
    #     x, simulations_cycles, color="#63A8D3", width=width, label="Simulation"
    # )
    # hardware_bars = plt.bar(hardware_versions, hardware_cycles, color="#ebbd34", width=width, label="Hardware")
    # ax.set_xticklabels(meaned_simulation_data.keys())

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#DDDDDD")

    ax.tick_params(bottom=False, left=False)

    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color="#DDDDDD")
    ax.xaxis.grid(False)

    plt.xlabel("CFU versions")
    # plt.xlabel("CFU versions (number after ''X'' - number of multiply-accumulate operations per cycle)")
    plt.ylabel("Cycles")
    # plt.title("CNN1:generated_0-30 inference acceleration (clock cycles)")
    # plt.title("CNN1:generated\\_0-30 inference acceleration (clock cycles)")
    plt.legend()

    bar_color = simulation_bars[0].get_facecolor()
    for bar in simulation_bars:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 5e7,
            "%.1fM" % (bar.get_height() / 1e6),
            horizontalalignment="center",
            color=bar_color,
            weight="bold",
        )

    bar_color = hardware_bars[0].get_facecolor()
    for bar in hardware_bars:
        if bar.get_height() == 0:
            continue
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 5e7,
            "%.1fM" % (bar.get_height() / 1e6),
            horizontalalignment="center",
            color=bar_color,
            weight="bold",
        )

    if generate_pgf:
        # plt.savefig("cycle_bars_evolution.pgf")
        plt.savefig("cycle_bars_computation_software.pgf")
    else:
        plt.show()


if __name__ == "__main__":
    main()
