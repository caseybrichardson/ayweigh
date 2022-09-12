
class AyWeighException(Exception):
    pass


class ChannelNotFound(AyWeighException):
    pass


class NoContestRunning(AyWeighException):
    pass


class ContestantNotFound(AyWeighException):
    pass


class ContestantAlreadyJoined(AyWeighException):
    pass
