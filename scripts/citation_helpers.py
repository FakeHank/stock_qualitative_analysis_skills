#!/usr/bin/env python3

from dataclasses import dataclass


@dataclass
class SecCitation:
    form: str
    filing_date: str
    section: str

    def format(self) -> str:
        return f"{self.form} + {self.filing_date} + {self.section}"


@dataclass
class WebCitation:
    publisher: str
    published_date: str
    title: str

    def format(self) -> str:
        return f"{self.publisher} + {self.published_date} + {self.title}"
