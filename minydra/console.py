class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class MinyConsole:
    def _end(self, key, *args):
        return f"{key}{' '.join(args)}{bcolors.ENDC}"

    def okblue(self, *args):
        return self._end(bcolors.OKBLUE, *args)

    def warn(self, *args):
        return self._end(bcolors.WARNING, *args)

    def okgreen(self, *args):
        return self._end(bcolors.OKGREEN, *args)

    def fail(self, *args):
        return self._end(bcolors.FAIL, *args)

    def bold(self, *args):
        return self._end(bcolors.BOLD, *args)

    def underline(self, *args):
        return self._end(bcolors.UNDERLINE, *args)
