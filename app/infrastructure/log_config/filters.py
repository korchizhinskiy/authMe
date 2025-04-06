import re
from logging import Filter, LogRecord
from typing import Any

regex_patterns = (
    # SNILS
    (r"(\d{6})\d{5}", r"\1*****"),
    (r"(\d{3})-(\d{3})-\d{3}\s\d{2}", r"\1-\2-***** **\3"),
)


class SensitiveDataFilter(Filter):
    patterns = regex_patterns

    def filter(self, record: LogRecord) -> bool:
        if record.args:
            record.args = tuple(self.mask_sensitive_data(arg) for arg in record.args)
        return True

    def mask_sensitive_data(self, argument: Any) -> str:  # noqa: ANN401
        for find_pattern, replace_pattern in self.patterns:
            if re.compile(find_pattern).match(str(argument)):
                argument = re.sub(find_pattern, replace_pattern, argument)
        return argument
