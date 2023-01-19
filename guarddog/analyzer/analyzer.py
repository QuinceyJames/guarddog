import os
from importlib import resources
from pathlib import Path

from semgrep.semgrep_main import invoke_semgrep  # type: ignore

import guarddog
from guarddog.configs.config import Config


class Analyzer:
    """
    Analyzes a local directory for threats found by source code or metadata rules

    Attributes:
        metadata_ruleset (list): list of metadata rule names
        sourcecode_ruleset (list): list of source code rule names

        exclude (list): list of directories to exclude from source code search
    """

    def __init__(self) -> None:
        self.config = Config()

        with resources.as_file(resources.files(guarddog).joinpath("../.guarddog.yaml")) as file:
            self.config.add_config_file(file)

        self.metadata_ruleset = {heuristic.key for heuristic in self.config.get_heuristics()}
        self.sourcecode_ruleset = {heuristic.key for heuristic in self.config.get_heuristics()}

        # Define paths to exclude from sourcecode analysis
        self.exclude = [
            "helm",
            ".idea",
            "venv",
            "test",
            "tests",
            ".env",
            "dist",
            "build",
            "semgrep",
            "migrations",
            ".github",
            ".semgrep_logs",
        ]

    def analyze(self, path, info=None, rules=None) -> dict:
        """
        Analyzes a package in the given path

        Args:
            path (str): path to package
            info (dict, optional): Any package information to analyze metadata. Defaults to None.
            rules (set, optional): Set of rules to analyze. Defaults to all rules.

        Raises:
            Exception: "{rule} is not a valid rule."

        Returns:
            dict[str]: map from each rule and their corresponding output
        """

        metadata_results = None
        sourcecode_results = None

        heuristics = self.config.get_heuristics(key=rules)
        for missing_heuristic in {rules} - {heuristic.key for heuristic in heuristics}:



        metadata_results = self.analyze_metadata(info, metadata_rules)
        sourcecode_results = self.analyze_sourcecode(path, sourcecode_rules)

        # Concatenate dictionaries together
        issues = metadata_results["issues"] + sourcecode_results["issues"]
        results = metadata_results["results"] | sourcecode_results["results"]
        errors = metadata_results["errors"] | sourcecode_results["errors"]

        return {"issues": issues, "errors": errors, "results": results, "path": path}

    def analyze_metadata(self, info, rules=None) -> dict:
        """
        Analyzes the metadata of a given package

        Args:
            info (dict): package information given by PyPI Json API
            rules (set, optional): Set of metadata rules to analyze. Defaults to all rules.

        Returns:
            dict[str]: map from each metadata rule and their corresponding output
        """

        results = {}
        errors = {}
        issues = 0

        for heuristic in self.config.get_heuristics(key=rules):
            try:
                rule_matches, message = heuristic.detector().detect(info)
                if rule_matches:
                    issues += 1
                    results[heuristic.key] = message
            except Exception as e:
                errors[heuristic.key] = f"failed to run rule {heuristic.key}: {str(e)}"

        return {"results": results, "errors": errors, "issues": issues}

    def analyze_sourcecode(self, path, rules=None) -> dict:
        """
        Analyzes the source code of a given package

        Args:
            path (str): path to directory of package
            rules (set, optional): Set of source code rules to analyze. Defaults to all rules.

        Returns:
            dict[str]: map from each source code rule and their corresponding output
        """
        target_path = Path(path)
        results = {}
        errors = {}
        issues = 0

        for heuristic in self.config.get_heuristics(key=rules):
            # try:
            #     response = invoke_semgrep(
            #         heuristic.absolute_location,
            #         [target_path],
            #         exclude=self.exclude,
            #         no_git_ignore=True,
            #     )
            #     rule_results = self._format_semgrep_response(response, rule=heuristic.key, targetpath=target_path)
            #     issues += len(rule_results)
            #
            #     results = results | rule_results
            # except Exception as e:
            #     errors[heuristic.key] = f"failed to run rule {heuristic.key}: {str(e)}"

        return {"results": results, "errors": errors, "issues": issues}

    def _format_semgrep_response(self, response, rule=None, targetpath=None):
        """
        Formats the response from Semgrep

        Args:
            response (dict): response from Semgrep
            rule (str, optional): name of rule to format. Defaults to all rules.
            targetpath (str, optional): root directory of scan. Defaults to None.
                Paths in formatted resonse will be rooted from targetpath.

        Returns:
            dict: formatted response in the form...

            {
                ...
                <rule-name>: {
                    <path-to-code:line-num>: <dangerous-code>
                    ...
                },
                ...
            }
        """

        results = {}

        for result in response["results"]:
            rule_name = rule or result["check_id"].split(".")[-1]
            code_snippet = result["extra"]["lines"]
            line = result["start"]["line"]

            file_path = os.path.abspath(result["path"])
            if targetpath:
                file_path = os.path.relpath(file_path, targetpath)

            location = file_path + ":" + str(line)
            code = self.trim_code_snippet(code_snippet)

            if rule_name not in result:
                results[rule_name] = []
                results[rule_name].append({
                    'location': location,
                    'code': code,
                    'message': result["extra"]["message"]
                })

        return results

    # Makes sure the matching code to be displayed isn't too long
    def trim_code_snippet(self, code):
        THRESHOLD = 250
        if len(code) > THRESHOLD:
            return code[: THRESHOLD - 10] + '...' + code[len(code) - 10:]
        else:
            return code
