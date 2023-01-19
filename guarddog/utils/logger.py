class Logger:
    _instances: dict[str, 'Logger'] = {}

    def __init__(self, info_out, warn_out, fatal_out):
        self.info_out = info_out if info_out else print
        self.warn_out = warn_out if warn_out else print
        self.fatal_out = fatal_out if fatal_out else print

    def info(self, message):
        self.info_out(message)

    def warn(self, message):
        self.warn_out(message)

    def fatal(self, message):
        self.fatal_out(message)

    @classmethod
    def get_instance(cls, key, *args, **kwargs):
        try:
            return cls._instances[key]
        except KeyError:
            to_return = cls(*args, **kwargs)
            cls._instances[key] = to_return
            return to_return

