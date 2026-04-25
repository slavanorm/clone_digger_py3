import logging
from pydantic import BaseModel


class Settings(BaseModel):
    # todo: describe settings
    clustering_threshold: int = 30  # looks doesnt work
    hashing_depth: int = 1
    clusterize_using_dcup: bool = True
    clusterize_using_hash: bool = False
    report_unifiers: bool = False  # report unifiers - not working now
    print_time: bool = False  # report time
    force: bool = False  # check very long sequences
    no_recursion: bool = False
    logger_level: int = logging.DEBUG  # logging.INFO
    free_variable_cost: float = 0.5
    free_variables_count: int = 1
    size_threshold: int = 5
    distance_threshold: int = 5


cfg = Settings()
