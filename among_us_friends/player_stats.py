from among_us_friends.imposter_stat import ImposterStat
from among_us_friends.keyed_default_dict import KeyedDefaultDict
from among_us_friends.repository import Repository, User


class PlayersMatchesStats:
    """Calculates aggregate stats for every player who participated in a collection of matches."""
    def __init__(self, matches):
        self.matches = matches

    def using(self, repo: Repository):
        users = KeyedDefaultDict(default_factory=lambda k: ImposterStat(k.username))
        users_by_rowid = KeyedDefaultDict(default_factory=lambda k: repo.user_dao().get_by_rowid(k))
        for match in self.matches:
            match_results = list(repo.result_dao().list_for_match(match))
            match_num_imposters = sum(1 for x in match_results if x.imposter)
            for result in match_results:
                user: User = users_by_rowid[result.user_id]
                users[user].tablulate(match, match_num_imposters, result)
        return users.values()
