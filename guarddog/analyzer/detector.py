from abc import abstractmethod
from typing import Optional


class Detector:
    """belongs to packages"""

    def __init__(self) -> None:
        pass

    # returns (ruleMatches, message)
    @abstractmethod
    def detect(self, package_info) -> tuple[bool, Optional[str]]:
        pass


class SourcecodeDetector(Detector):
    def detect(self, package_info) -> tuple[bool, Optional[str]]:
        try:
            response = invoke_semgrep(
                heuristic.absolute_location,
                [target_path],
                exclude=self.exclude,
                no_git_ignore=True,
            )
            rule_results = self._format_semgrep_response(response, rule=heuristic.key, targetpath=target_path)
            issues += len(rule_results)

            results = results | rule_results
        except Exception as e:
            errors[heuristic.key] = f"failed to run rule {heuristic.key}: {str(e)}"