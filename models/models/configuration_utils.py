from typing import Dict


class ConfigurationUtils:
    def to_dict(self):
        print("HHHI")
        return {**self.__dict__, "name": self.name}

    @classmethod
    def from_dict(cls, dct: Dict):
        return cls(**dct)