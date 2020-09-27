from among_us_friends.imposter_stat import ImposterStat
from among_us_friends.keyed_default_dict import KeyedDefaultDict
from among_us_friends.repository import Repository


class ColorsMatchesStats:
    def __init__(self, matches):
        self.matches = matches

    def using(self, repo: Repository):
        colors = KeyedDefaultDict(default_factory=lambda k: ImposterStat(k))
        for match in self.matches:
            match_results = list(repo.result_dao().list_for_match(match))
            match_num_imposters = sum(1 for x in match_results if x.imposter)
            for result in match_results:
                colors[result.color].tablulate(match, match_num_imposters, result)
        return colors.values()
