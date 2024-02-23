import os
import matplotlib.pyplot as plt
import catalight.analysis.plotting as plot_tools
from catalight.equipment.experiment_control import Experiment


def get_file_paths(main_dir):
    filepaths = []
    for root, dirs, files in os.walk(main_dir):
        for name in files:
            if name.endswith('Conv_Sel_plot.pickle'):
                filepaths.append(os.path.join(root, name))
    for index, path in enumerate(filepaths):
        print(f"{index}, {os.path.relpath(path, main_dir)}")
    return filepaths


def rescale_plots(filepaths):
    """
    Seperate conversion and selectivity into two y axes, rescale lims of each.

    Parameters
    ----------
    filepaths : list[str]
        list of filepaths to Conv vs Sel figures as .pickle files.
    """
    for file in filepaths:
        fig, ax = plot_tools.open_pickled_fig(file)
        ax2 = ax.twinx()
        lines = ax.lines
        ax.set_ylabel('Conversion [%]')
        ax2.set_ylabel('Selectivity [%]', fontsize=ax.yaxis.label.get_fontsize())

        ax2.yaxis.label.set_color('r')
        ax2.tick_params(axis='y', colors='r')
        ax2.spines['right'].set_color('r')

        for line in lines:
            # If the line doesn't have a label, add one based on line color
            if line.get_label() == '_nolegend_':
                if line.get_color() == 'k':
                    line.set_label('Conversion')
                elif line.get_color() == 'r':
                    line.set_label('Selectivity')

            # Move selecitivy line to second y axis. Adjust each y lims
            if line.get_label() == 'Conversion':
                ydata = line.get_ydata()
                #[min(ydata) - 3
                ax.set_ylim([0, 5])
            elif line.get_label() == 'Selectivity':
                line.remove()
                ax2.add_line(line)
                line.set_transform(ax2.transData)

                ydata = line.get_ydata()
                ax2.set_ylim([min(ydata)-3, max(ydata)+2])
            else:
                print('Warning: No label found. There may be some error.')

        plt.tight_layout()
        fig.savefig(os.path.splitext(file)[0] + '_zoomed_in.svg', format="svg")

if __name__ == '__main__':
    main_dir = (r"G:\Shared drives\Photocatalysis Projects"
                r"\catalight_experiments\20240131\20230504_Au95Pd5_4wt%_5mg")
    paths = get_file_paths(main_dir)
    rescale_plots(paths)
