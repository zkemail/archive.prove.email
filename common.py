from dataclasses import dataclass


@dataclass(frozen=True)
class Dsp:
    domain: str
    selector: str

    def __init__(self, domain: str, selector: str):
        object.__setattr__(self, 'domain', domain.lower())
        object.__setattr__(self, 'selector', selector.lower())



@dataclass
class MsgInfo:
    signedData: bytes
    signature: bytes
    source: str
    date: str
