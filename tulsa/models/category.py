from enum import StrEnum


class Severity(StrEnum):
    Information = "information"
    Low = "low"
    Medium = "medium"
    High = "high"
    Critical = "critical"


class Category(StrEnum):
    Generic = "generic"
    Blockchain = "blockchain"
    BugBounty = "bug-bounty"
    HacktivityBounty = "hacktivity-bounty"
