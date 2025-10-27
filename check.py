import argparse
import polib
from language_tool_python import LanguageTool, utils
from language_tool_python.utils import classify_matches
from colorama import Fore, Style
import os
import json
from jsonschema import validate
import jsonschema_default
from Levenshtein import distance
import sys

# Schema for the JSON configs
schema = {
    "type": "object",
    "properties": {
        "checkSourceString": {"type": "boolean", "default": True},
        "checkTranslationString": {"type": "boolean", "default": False},
        "customDictionary": {
            "type": "array",
            "items": {"type": "string"},
            "default": [],
        },
        "disabledRules": {"type": "array", "items": {"type": "string"}, "default": []},
    },
    "required": [],
}

# poChecker class - does all the main work
class poChecker:
    totalIssues = 0

    def __init__(
        self,
        path,
        language="en-US",
        check_source=True,
        check_translation=False,
        dict=[],
        disabled_rules=[],
        verbose=False,
    ):
        self.poFile = polib.pofile(path)
        self.tool = LanguageTool(
            language,
            config={
                "cacheSize": 500,
                "pipelineCaching": True,
                "maxSpellingSuggestions": 10,
                "disabledRuleIds": ",".join(disabled_rules),
            },
        )
        self.check_source = check_source
        self.check_translation = check_translation
        self.dict = dict
        self.verbose = verbose

    # Main check loop
    def process(self):
        for entry in self.poFile:
            # Source strings
            if self.check_source:
                self.doCheck(entry.msgid)
            if self.check_translation and entry.msgstr:
                self.doCheck(entry.msgid)

        self.tool.close()
        
        return self.totalIssues
        
    # Checks a string against the custom dict and LanguageTool
    def doCheck(self, string):
        # Get the issues
        issues = self.tool.check(string)
        # If there are issues, validate them
        if len(issues) > 0:
            for issue in issues:
                if self.isIssueValid(issue):
                    self.outputIssue(issue)

        self.tool.close()
        
    # Checks a string against the custom dict and LanguageTool
    def doCheck(self, string):
        # Get the issues
        issues = self.tool.check(string)
        # If there are issues, validate them
        if len(issues) > 0:
            for issue in issues:
                if self.isIssueValid(issue):
                    self.outputIssue(issue)

    # Suggests a spelling correction using the custom dictionary
    def suggestCorrectionsFromCustomDic(self, typo, distance_limit=3):
        min_dist = distance_limit + 1
        suggested_word = None

        for knownWord in self.dict:
            dist = distance(typo, knownWord, score_cutoff=distance_limit)
            if dist < min_dist:
                min_dist = dist
                suggested_word = knownWord

        return suggested_word

    # Checks an issue against the 
    def isIssueValid(self, issue):
        context = issue.context[
            issue.offsetInContext : issue.offsetInContext + issue.errorLength
        ]

        if context in self.dict:
            return False
        else:
            return True

    # Formats and outputs the result to the terminal screen
    def outputIssue(self, issue):
        offset = " " * issue.offsetInContext
        pointer = "^" * issue.errorLength
        context = issue.context.strip()
        suggestion = None
        self.totalIssues+=1

        print(Fore.RED + f"{issue.message.strip()}")
        print(Fore.YELLOW + f"{context}")
        print(f"{offset}{pointer}")

        # Extracting the typo out of the string using the offset and length provided
        typo = context[
            issue.offsetInContext : issue.offsetInContext + issue.errorLength
        ]

        hasSuggestion = True if issue.replacements and issue.replacements[0] else False

        # Our method for giving suggestions is less robust, we should reduce the allowed edit distance if a suggestion was already provided
        if hasSuggestion:
            suggestionFromCustomDict = self.suggestCorrectionsFromCustomDic(typo, 2)
        else:
            suggestionFromCustomDict = self.suggestCorrectionsFromCustomDic(typo, 3)

        if hasSuggestion:
            # Ensure we are providing the suggestion with the smallest edit distance
            if suggestionFromCustomDict:
                suggestion = (
                    issue.replacements[0]
                    if distance(typo, issue.replacements[0], score_cutoff=3)
                    < distance(typo, suggestionFromCustomDict, score_cutoff=3)
                    else suggestionFromCustomDict
                )
            else:
                suggestion = issue.replacements[0]
        else:
            suggestion = suggestionFromCustomDict

        if suggestion:
            print(Fore.GREEN + f"{offset}{suggestion}")

        if self.verbose:
            print(Fore.WHITE + f"Triggered rule ID: {issue.ruleId}")

        print(Style.RESET_ALL)


# Main func which takes the config, inits, and then runs the checker
def main():
    parser = argparse.ArgumentParser(description="Process a .po file path")
    parser.add_argument("--path", type=str, help="Path to the .po file", required=True)
    parser.add_argument(
        "--language",
        type=str,
        default="en-US",
        help="The language of the input file (Examples: en-US, en, es, ca-ES)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="poLanguageChecker.json",
        help="The poLanguageChecker config file to read.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Displays additional info such as what rule ID was triggered",
    )

    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(Fore.RED + f"Config file {args.config} does not exist")
        exit(1)

    with open(args.config, "r") as f:
        config = json.load(f)

    validate(instance=config, schema=schema)
    default_config = jsonschema_default.create_from(schema)
    config = {**default_config, **config}

    checker = poChecker(
        args.path,
        language=args.language,
        check_source=config["checkSourceString"],
        check_translation=config["checkTranslationString"],
        dict=config["customDictionary"],
        verbose=args.verbose,
    )

    result = checker.process()
    print(f"Total number of issues: {result}")
    
    if result > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()

