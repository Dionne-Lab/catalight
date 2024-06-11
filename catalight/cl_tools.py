"""Helper functions for command line printing"""


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1,
                     length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar.

    Parameters
    ----------
    iteration : `int`
        Current iteration.
    total : `int`
        Total iterations.
    prefix : `str`, optional
        Prefix string.
    suffix : `str`, optional
        Suffix string.
    decimals : `int`, optional
        Positive number of decimals in percent.
    length : `int`, optional
        Character length of the bar.
    fill : `str`, optional
        Bar fill character.
    printEnd : `str`, optional
        End character (e.g., "\\r", "\\r\\n").
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration
                                                            / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    # dont
    # if iteration == total:
    #    print()
